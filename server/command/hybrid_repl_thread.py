#!/usr/bin/env python3
"""
Hybrid REPL Thread - Executes scripts then transitions to REPL mode
Maintains variable state between script execution and interactive mode
"""

import subprocess
import threading
import time
import os
import sys
import tempfile
import asyncio
from queue import Queue, Empty
import json
import traceback
import signal
import resource
import psutil

from common.config import Config
from common.file_storage import file_storage
from command.error_handler import EducationalErrorHandler
from command.response import response


class HybridREPLThread(threading.Thread):
    """Thread for running Python scripts then transitioning to REPL mode"""

    def __init__(
        self, cmd_id, client, event_loop, script_path=None, registry_callback=None, lock_manager=None, username=None
    ):
        super().__init__()
        self.cmd_id = cmd_id
        self.client = client
        self.event_loop = event_loop
        self.script_path = script_path
        self.registry_callback = registry_callback
        self.lock_manager = lock_manager
        self.username = username
        self.alive = True
        self.p = None
        self.error_handler = EducationalErrorHandler()
        self.input_queue = Queue()
        self.repl_mode = False
        self.script_executed = False
        self.had_error = False
        self.daemon = True

        # Resource limits (configurable via environment)
        self.memory_limit_mb = int(os.environ.get("MEMORY_LIMIT_MB", "128"))
        self.cpu_time_limit = int(os.environ.get("EXECUTION_TIMEOUT", "60"))  # Changed from 30 to 60 seconds
        self.file_size_limit_mb = int(os.environ.get("FILE_SIZE_LIMIT_MB", "10"))
        self.max_processes = int(os.environ.get("MAX_PROCESSES", "50"))
        self.start_time = time.time()

        # REPL sessions should have extended CPU time for interactive use
        self.repl_cpu_limit = 300  # Changed from 3600 to 300 seconds (5 minutes)

    def kill(self):
        """Kill the running subprocess"""
        self.alive = False
        if self.p:
            try:
                self.p.kill()
            except:
                pass

    def stop(self):
        """Stop the subprocess gracefully, then forcefully if needed"""
        print(f"[HYBRID-REPL] Stopping thread for cmd_id: {self.cmd_id}")
        self.alive = False
        if self.p:
            try:
                # First try graceful termination
                self.p.terminate()

                # Wait up to 0.1 seconds for graceful shutdown
                for _ in range(10):  # 10 * 0.01 = 0.1 seconds
                    if self.p.poll() is not None:
                        print(f"[HYBRID-REPL] Process {self.p.pid} terminated gracefully")
                        break
                    time.sleep(0.01)
                else:
                    # Force kill if still running
                    print(f"[HYBRID-REPL] Force killing process {self.p.pid}")
                    self.p.kill()
                    self.p.wait()  # Ensure process is fully dead

            except Exception as e:
                print(f"[HYBRID-REPL] Error stopping process: {e}")
                pass

        # Release execution lock if we have one
        self._release_execution_lock()

    def _release_execution_lock(self):
        """Release execution lock for this script"""
        if self.lock_manager and self.script_path and self.username:
            try:
                self.lock_manager.release_execution_lock(self.username, self.script_path, self.cmd_id)
            except Exception as e:
                print(f"[HYBRID-REPL] Error releasing execution lock: {e}")

    def update_client(self, client, cmd_id):
        """Update client reference for reconnections"""
        print(f"[HYBRID-REPL] Updating client reference: old_cmd_id={self.cmd_id}, new_cmd_id={cmd_id}")
        self.client = client
        self.cmd_id = cmd_id

    def send_input(self, user_input):
        """Queue user input to be sent to the program or REPL"""
        print(f"[HYBRID-REPL] Received input from queue: {repr(user_input)}")
        print(f"[HYBRID-REPL] REPL mode: {self.repl_mode}, Process alive: {self.is_alive()}")
        self.input_queue.put(user_input)
        return True

    def set_resource_limits(self):
        """Set resource limits for the subprocess (Linux/Unix only)"""
        try:
            # Memory limit (address space)
            memory_bytes = self.memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

            # CPU time limit - use extended limit for REPL or if no script (empty REPL)
            cpu_limit = self.repl_cpu_limit if (not self.script_path) else self.cpu_time_limit
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
            print(
                f"[HYBRID-REPL] Set CPU limit to {cpu_limit}s for {'REPL' if not self.script_path else 'script'} mode"
            )

            # File size limit
            file_size_bytes = self.file_size_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_size_bytes, file_size_bytes))

            # Process limit
            resource.setrlimit(resource.RLIMIT_NPROC, (self.max_processes, self.max_processes))

            # Core dump size (disable core dumps)
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

        except Exception as e:
            # Resource limits may not work on all systems (e.g., Windows)
            print(f"Warning: Could not set resource limits: {e}")

    def response_to_client(self, code, data):
        """Send response to client via WebSocket"""
        if data:
            asyncio.run_coroutine_threadsafe(response(self.client, self.cmd_id, code, data), self.event_loop)

    def create_hybrid_wrapper(self):
        """Create a wrapper script that runs user code then starts REPL"""
        wrapper_code = '''import sys
import os
import traceback
import code
import builtins
import base64
import io

# Lazy load matplotlib only when actually imported by user code
_matplotlib_hooked = False

def _hook_matplotlib():
    """Hook matplotlib.pyplot.show only when matplotlib is actually imported"""
    global _matplotlib_hooked
    if _matplotlib_hooked:
        return

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        _original_show = plt.show

        def _custom_show(*args, **kwargs):
            """Custom show function that captures matplotlib figures"""
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            print("__MATPLOTLIB_FIGURE_START__")
            print(img_base64)
            print("__MATPLOTLIB_FIGURE_END__")
            sys.stdout.flush()
            plt.clf()
            plt.close('all')

        plt.show = _custom_show
        _matplotlib_hooked = True
    except ImportError:
        pass

# Override __import__ to detect matplotlib usage
_original_builtins_import = builtins.__import__

def _custom_import(name, *args, **kwargs):
    result = _original_builtins_import(name, *args, **kwargs)
    # Hook matplotlib after it's imported by user code
    if 'matplotlib' in name and not _matplotlib_hooked:
        _hook_matplotlib()
    return result

builtins.__import__ = _custom_import

# Store original input for REPL mode
_original_input = builtins.input

def _custom_input(prompt=""):
    """Custom input function for script execution"""
    sys.stdout.write(f"__INPUT_REQUEST_START__{prompt}__INPUT_REQUEST_END__")
    sys.stdout.flush()
    result = _original_input()
    return result

# Override input during script execution
builtins.input = _custom_input

# Dictionary to store script variables
script_globals = {}

'''

        if self.script_path:
            # Add script execution code
            wrapper_code += f"""
# Execute the user script
script_path = r"{self.script_path}"

# Signal script execution starting
print("__SCRIPT_START__")
sys.stdout.flush()

try:
    with open(script_path, 'r') as f:
        script_code = f.read()
    
    # Execute script and capture its namespace
    # Note: exec() output goes to current stdout, which is captured by parent process
    exec(compile(script_code, script_path, 'exec'), script_globals)
    
    # Script completed successfully
    print("__SCRIPT_END__")
    sys.stdout.flush()
    
except Exception as e:
    # Print error
    traceback.print_exc()
    
    # Signal error to parent process
    print("__SCRIPT_ERROR__")
    sys.stdout.flush()
    sys.exit(1)

# Update globals with script variables (excluding private ones)
for key, value in script_globals.items():
    if not key.startswith('__') and not key.startswith('_'):
        globals()[key] = value

# Also make variables available globally for REPL access
for var_name, var_value in script_globals.items():
    if not var_name.startswith('__') and not var_name.startswith('_'):
        globals()[var_name] = var_value

# Variables are now available in REPL scope

"""

        # Add REPL startup code
        wrapper_code += '''
# Signal REPL mode starting
print("__REPL_MODE_START__")
sys.stdout.flush()

# Restore original input for REPL
builtins.input = _original_input

# Start interactive REPL with proper multiline handling

# Custom REPL using InteractiveInterpreter-like logic
import readline
import rlcompleter
import code
readline.parse_and_bind("tab: complete")

# Multiline input buffer and state
multiline_buffer = []
in_multiline = False

def execute_code_block(source, exec_globals):
    """Execute a complete code block and handle both expressions and statements"""
    try:
        # Try to compile and execute as 'single' mode first (for expressions)
        try:
            compiled = compile(source, '<stdin>', 'single')
            result = eval(compiled, exec_globals)
            if result is not None:
                print(repr(result))
        except SyntaxError:
            # If single mode fails, try exec mode (for statements)
            exec(compile(source, '<stdin>', 'exec'), exec_globals)
    except Exception:
        traceback.print_exc()

# Interactive REPL loop with proper multiline support
while True:
    try:
        # Always use >>> prompt (user doesn't want ... continuation prompts)
        prompt = ">>> "
        line = input(prompt)
        
        # Add current line to buffer
        if in_multiline:
            multiline_buffer.append(line)
        else:
            multiline_buffer = [line]
        
        # Join all lines to form complete source
        complete_source = '\\n'.join(multiline_buffer)
        
        # Use compile_command to check if code is complete
        try:
            compiled = code.compile_command(complete_source)
            
            if compiled is None:
                # Code is incomplete, need more input
                in_multiline = True
                continue
            else:
                # Code is complete, execute it
                in_multiline = False
                
                # Only execute if there's actual code (not just empty lines)
                if complete_source.strip():
                    # Merge script variables into current execution context
                    exec_globals = globals().copy()
                    exec_globals.update(script_globals)
                    
                    # Execute the compiled code
                    try:
                        result = eval(compiled, exec_globals)
                        if result is not None:
                            print(repr(result))
                    except SyntaxError:
                        # If eval fails, try exec for statements
                        try:
                            exec(compiled, exec_globals)
                        except Exception:
                            traceback.print_exc()
                    except Exception:
                        # Handle runtime errors (NameError, ValueError, etc.)
                        traceback.print_exc()
                    
                    # Update script_globals with new variables for persistence
                    for k, v in exec_globals.items():
                        if not k.startswith('__') and not k.startswith('_'):
                            script_globals[k] = v
                    
                    # Update current globals with any new variables from execution
                    globals().update({k: v for k, v in exec_globals.items() if not k.startswith('__')})
                
                # Reset buffer after successful execution
                multiline_buffer = []
                
        except (SyntaxError, OverflowError, ValueError) as e:
            # Code has syntax error, report it and reset
            print(f"SyntaxError: {e}")
            in_multiline = False
            multiline_buffer = []
            
    except SystemExit:
        break
    except KeyboardInterrupt:
        print("\\nKeyboardInterrupt")
        in_multiline = False
        multiline_buffer = []
    except EOFError:
        print()
        sys.exit(0)
    
    sys.stdout.flush()
'''

        # Write wrapper to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(wrapper_code)
            return f.name

    def run(self):
        """Main thread execution"""
        self.alive = True
        wrapper_path = None

        try:
            # Create wrapper script
            wrapper_path = self.create_hybrid_wrapper()

            # Start Python subprocess without resource limits for now (debugging)
            popen_kwargs = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "bufsize": 0,
                "cwd": os.path.dirname(self.script_path) if self.script_path else file_storage.ide_base,
            }

            # Temporarily disable resource limits to debug the issue
            # TODO: Re-enable after fixing output streaming
            # is_unix = os.name == 'posix'
            # if is_unix:
            #     popen_kwargs['preexec_fn'] = self.set_resource_limits

            self.p = subprocess.Popen([Config.PYTHON, "-u", wrapper_path], **popen_kwargs)

            # Start output reader thread
            output_thread = threading.Thread(target=self.read_output)
            output_thread.daemon = True
            output_thread.start()

            # Start input handler thread
            input_thread = threading.Thread(target=self.handle_input)
            input_thread.daemon = True
            input_thread.start()

            # Start timeout monitor thread
            timeout_thread = threading.Thread(target=self.monitor_timeout)
            timeout_thread.daemon = True
            timeout_thread.start()

            # Wait for process to complete or be killed
            while self.alive and self.p.poll() is None:
                time.sleep(0.1)

            # Process ended
            if self.p.poll() is not None:
                return_code = self.p.poll()
                if return_code != 0 and not self.had_error:
                    self.response_to_client(1, {"stdout": f"Process exited with code {return_code}"})

        except Exception as e:
            print(f"Error in HybridREPLThread: {e}")
            traceback.print_exc()
            self.response_to_client(1, {"stdout": f"Error: {str(e)}"})

        finally:
            # Cleanup
            if wrapper_path and os.path.exists(wrapper_path):
                try:
                    os.unlink(wrapper_path)
                except:
                    pass

            # Ensure process is terminated
            if self.p:
                try:
                    self.p.terminate()
                    self.p.wait(timeout=2)
                except:
                    try:
                        self.p.kill()
                    except:
                        pass

    def monitor_timeout(self):
        """Monitor execution time and kill if exceeds limit"""
        # Disable timeout monitoring for now - it's interfering with input()
        # TODO: Implement smarter timeout that pauses during input wait
        return

        # Only monitor during script execution, not REPL
        while self.alive and self.p and not self.repl_mode:
            elapsed = time.time() - self.start_time

            # Check if timeout exceeded (add grace period for REPL transition)
            if elapsed > self.cpu_time_limit + 5:
                print(f"[TIMEOUT] Process {self.cmd_id} exceeded time limit ({self.cpu_time_limit}s)")
                self.response_to_client(
                    1, {"stdout": f"\n[TIMEOUT] Execution time limit exceeded ({self.cpu_time_limit} seconds)\n"}
                )
                self.kill()
                break

            # Also monitor memory usage if psutil available
            try:
                if self.p and self.p.pid:
                    process = psutil.Process(self.p.pid)
                    memory_mb = process.memory_info().rss / (1024 * 1024)

                    if memory_mb > self.memory_limit_mb:
                        print(f"[MEMORY] Process {self.cmd_id} exceeded memory limit ({self.memory_limit_mb}MB)")
                        self.response_to_client(
                            1, {"stdout": f"\n[MEMORY LIMIT] Memory usage exceeded ({self.memory_limit_mb}MB)\n"}
                        )
                        self.kill()
                        break
            except:
                # psutil not available or process already dead
                pass

            time.sleep(1)

    def read_output(self):
        """Read output from subprocess"""
        buffer = ""

        print(f"[HYBRID-REPL] Starting output reader for cmd_id: {self.cmd_id}")

        while self.alive and self.p and self.p.poll() is None:
            try:
                # Read character by character to handle input prompts without newlines
                char = self.p.stdout.read(1)
                if not char:
                    time.sleep(0.01)
                    continue

                buffer += char
                self._last_char_time = time.time()  # Track when we last received a character

                # Check for special markers first
                if "__INPUT_REQUEST_START__" in buffer and "__INPUT_REQUEST_END__" in buffer:
                    # Send any text before the marker
                    pre_marker = buffer[: buffer.index("__INPUT_REQUEST_START__")]
                    if pre_marker:
                        for line in pre_marker.split("\n"):
                            if line or line == "":
                                self.response_to_client(0, {"stdout": line})

                    # Extract prompt
                    start = buffer.index("__INPUT_REQUEST_START__") + len("__INPUT_REQUEST_START__")
                    end = buffer.index("__INPUT_REQUEST_END__")
                    prompt = buffer[start:end]

                    print(f"[HYBRID-REPL] Input request detected: {repr(prompt)}")

                    # Send input request to client
                    self.response_to_client(2000, {"prompt": prompt})

                    # Clear the processed part from buffer
                    buffer = buffer[end + len("__INPUT_REQUEST_END__") :]

                elif "__MATPLOTLIB_FIGURE_START__" in buffer:
                    # Handle matplotlib figure
                    if "__MATPLOTLIB_FIGURE_END__" in buffer:
                        start = buffer.index("__MATPLOTLIB_FIGURE_START__") + len("__MATPLOTLIB_FIGURE_START__")
                        end = buffer.index("__MATPLOTLIB_FIGURE_END__")
                        figure_data = buffer[start:end].strip()

                        # Send figure to client
                        self.response_to_client(3000, {"figure": figure_data})

                        # Clear the marker from buffer
                        buffer = buffer[end + len("__MATPLOTLIB_FIGURE_END__") :]

                elif "__SCRIPT_START__" in buffer:
                    # Script execution starting - signal to frontend
                    print(f"[HYBRID-REPL] Script execution starting")
                    buffer = buffer.replace("__SCRIPT_START__", "")
                    # Send script start signal to client (null data triggers run=true)
                    self.response_to_client(0, None)

                elif "__SCRIPT_END__" in buffer:
                    # Script execution completed successfully
                    print(f"[HYBRID-REPL] Script execution completed")
                    buffer = buffer.replace("__SCRIPT_END__", "")
                    self.script_executed = True

                    # Release execution lock since script is done (REPL can continue)
                    self._release_execution_lock()

                elif "__SCRIPT_ERROR__" in buffer:
                    # Script had an error, don't start REPL
                    self.had_error = True
                    buffer = buffer.replace("__SCRIPT_ERROR__", "")
                    # Send any remaining output
                    if buffer.strip():
                        self.response_to_client(0, {"stdout": buffer})

                    # Release execution lock on error too
                    self._release_execution_lock()
                    # Signal script error to client
                    self.response_to_client(4000, {"error": "Script execution failed"})
                    # Kill the process
                    self.kill()
                    break

                elif "__REPL_MODE_START__" in buffer:
                    # Send any text before the marker
                    pre_marker = buffer[: buffer.index("__REPL_MODE_START__")]
                    if pre_marker:
                        for line in pre_marker.split("\n")[:-1]:  # Skip last incomplete line
                            self.response_to_client(0, {"stdout": line})

                    # Entering REPL mode
                    self.repl_mode = True
                    buffer = buffer[buffer.index("__REPL_MODE_START__") + len("__REPL_MODE_START__") :].lstrip()
                    # Signal REPL mode to client
                    self.response_to_client(5000, {"mode": "repl"})

                # Send complete lines
                elif "\n" in buffer:
                    lines = buffer.split("\n")
                    # Send all complete lines
                    for line in lines[:-1]:
                        # Strip trailing whitespace only, preserve intentional leading spaces
                        clean_line = line.rstrip()
                        print(f"[HYBRID-REPL] Sending line: {repr(clean_line)}")
                        self.response_to_client(0, {"stdout": clean_line})
                    # Keep the incomplete line in buffer
                    buffer = lines[-1]

                # In REPL mode, check for prompt patterns
                elif self.repl_mode:
                    # Simple approach: if buffer contains prompts, remove them and keep clean content
                    original_buffer = buffer

                    # Remove all variations of prompts and clean up
                    if ">>> " in buffer:
                        # Replace '>>> ' with newline to separate content, then clean up
                        buffer = buffer.replace(">>> ", "\n").strip()
                    elif " >>>" in buffer:
                        # Replace ' >>>' with newline to separate content, then clean up
                        buffer = buffer.replace(" >>>", "\n").strip()
                    elif ">>>" in buffer:
                        # Replace '>>>' with newline to separate content, then clean up
                        buffer = buffer.replace(">>>", "\n").strip()

                    if buffer != original_buffer:
                        print(f"[HYBRID-REPL] Cleaned prompt from buffer: {repr(original_buffer)} -> {repr(buffer)}")

                    # Filter out empty or whitespace-only buffers after cleaning
                    if not buffer or buffer.isspace():
                        buffer = ""
                    # CRITICAL FIX: In REPL mode, send output lines that don't end with newline
                    # after a short delay to catch expression results like 'Sachin'
                    elif (
                        len(buffer) > 0
                        and not buffer.endswith((">>>", "..."))
                        and time.time() - getattr(self, "_last_char_time", 0) > 0.3
                    ):
                        # Likely an expression result or output that needs flushing
                        if buffer.strip() and not buffer.isspace():  # Only send non-empty, non-whitespace content
                            print(f"[HYBRID-REPL] Flushing buffered output: {repr(buffer)}")
                            self.response_to_client(0, {"stdout": buffer})
                            buffer = ""
                    # Also flush if buffer gets too long (prevent memory issues)
                    elif len(buffer) > 1000:
                        print(f"[HYBRID-REPL] Flushing large buffer: {repr(buffer[:100])}...")
                        self.response_to_client(0, {"stdout": buffer})
                        buffer = ""

            except Exception as e:
                print(f"[HYBRID-REPL] Error reading output: {e}")
                import traceback

                traceback.print_exc()
                break

        # Send any remaining buffer
        if buffer and buffer.strip():
            print(f"[HYBRID-REPL] Sending remaining buffer: {repr(buffer)}")
            self.response_to_client(0, {"stdout": buffer})

    def handle_input(self):
        """Handle input queue and send to subprocess"""
        while self.alive and self.p and self.p.poll() is None:
            try:
                # Wait for input with timeout
                user_input = self.input_queue.get(timeout=0.1)

                print(f"[HYBRID-REPL] Received input from queue: {user_input}")
                print(f"[HYBRID-REPL] REPL mode: {self.repl_mode}, Process alive: {self.p.poll() is None}")

                if self.p and self.p.stdin:
                    # Send input to subprocess
                    self.p.stdin.write(user_input + "\n")
                    self.p.stdin.flush()
                    print(f"[HYBRID-REPL] Sent input to subprocess: {user_input}")

                    # Echo input back to client in REPL mode
                    if self.repl_mode:
                        # Input echo is handled by the REPL itself
                        pass

            except Empty:
                continue
            except Exception as e:
                print(f"Error handling input: {e}")
                break
