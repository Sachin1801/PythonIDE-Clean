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
        self.script_started = False  # Track when script execution begins
        self.script_ended = False    # Track when script execution completes
        self.script_executed = False
        self.had_error = False
        self.daemon = True

        # Resource limits (configurable via environment)
        self.memory_limit_mb = int(os.environ.get("MEMORY_LIMIT_MB", "128"))
        # Simple 3-second timeout like LeetCode
        self.script_timeout = 3  # 3 seconds for script execution
        self.cpu_time_limit = int(os.environ.get("EXECUTION_TIMEOUT", "60"))  # Keep for REPL mode
        self.file_size_limit_mb = int(os.environ.get("FILE_SIZE_LIMIT_MB", "10"))
        self.max_processes = int(os.environ.get("MAX_PROCESSES", "50"))
        self.start_time = time.time()
        self._last_char_time = time.time()  # Track when we last received output (for idle detection)

        # Track input state for timeout pause
        self.waiting_for_input = False
        self.timeout_accumulated = 0  # Track accumulated runtime (excluding input wait)

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
import code
import builtins
import base64
import io
import signal
import traceback

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
_in_repl_mode = False

def _custom_input(prompt=""):
    """Custom input function for script execution (should NOT be called in REPL mode)"""
    # For script execution, use markers for WebSocket communication
    sys.stdout.flush()

    # Send the input request marker with the prompt
    sys.stdout.write(f"__INPUT_REQUEST_START__{prompt}__INPUT_REQUEST_END__")
    sys.stdout.flush()

    # Force flush at multiple levels
    try:
        import os
        if hasattr(sys.stdout, 'fileno'):
            os.fsync(sys.stdout.fileno())
    except:
        pass

    # Read input without prompt (we handle display in parent)
    result = _original_input("")
    return result

# Override input during script execution only
builtins.input = _custom_input

# Dictionary to store script variables
script_globals = {}

# Flag to track if script execution was successful
_script_success = False

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
    _script_success = True

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

        # Add REPL startup code - only start REPL if script succeeded or no script
        wrapper_code += '''
# Only start REPL if script succeeded (or if no script was run)
if _script_success or not {has_script}:
    # Signal REPL mode starting
    print("__REPL_MODE_START__")
    sys.stdout.flush()

    # CRITICAL: Completely restore native Python input() for REPL mode
    # Don't use _in_repl_mode flag, just restore the input directly
    builtins.input = _original_input

    # Debug logging removed - REPL mode active, input() restored
'''.format(has_script='True' if self.script_path else 'False')

        # Continue with REPL code only if we're supposed to start it
        wrapper_code += '''
else:
    # Script failed, don't start REPL
    sys.exit(1)
'''

        # Add the actual REPL loop
        wrapper_code += '''
# Now using original input() in REPL mode for natural prompt handling
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
        use_pty = False
        master_fd = None
        slave_fd = None

        try:
            # CRITICAL DEBUG: Log the start of run method
            print(f"[HYBRID-REPL] ========== RUN METHOD STARTED ==========")
            print(f"[HYBRID-REPL] cmd_id: {self.cmd_id}, script_path: {self.script_path}")

            # Create wrapper script
            wrapper_path = self.create_hybrid_wrapper()
            print(f"[HYBRID-REPL] Wrapper script created at: {wrapper_path}")

            # Check if we're on Unix and can use PTY for better terminal emulation
            is_unix = os.name == 'posix'
            print(f"[HYBRID-REPL] System check: os.name={os.name}, is_unix={is_unix}")

            if is_unix:
                try:
                    print(f"[HYBRID-REPL] Attempting to import pty module...")
                    import pty
                    import select
                    print(f"[HYBRID-REPL] pty module imported successfully")

                    # Create a pseudo-terminal for proper input() handling
                    print(f"[HYBRID-REPL] Creating PTY...")
                    master_fd, slave_fd = pty.openpty()

                    # Disable echo to prevent duplicate input display
                    import termios
                    attrs = termios.tcgetattr(slave_fd)
                    attrs[3] = attrs[3] & ~termios.ECHO  # lflag - turn off ECHO flag
                    termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)
                    print(f"[HYBRID-REPL] ✓ PTY echo disabled")

                    use_pty = True
                    print(f"[HYBRID-REPL] ✓✓✓ PTY CREATED SUCCESSFULLY ✓✓✓")
                    print(f"[HYBRID-REPL] PTY master_fd={master_fd}, slave_fd={slave_fd}")
                except Exception as e:
                    print(f"[HYBRID-REPL] ✗✗✗ PTY FAILED ✗✗✗")
                    print(f"[HYBRID-REPL] PTY not available, falling back to pipes: {e}")
                    import traceback
                    traceback.print_exc()
                    use_pty = False
            else:
                print(f"[HYBRID-REPL] Not Unix system, skipping PTY")
                use_pty = False

            print(f"[HYBRID-REPL] Final decision: use_pty={use_pty}")

            if use_pty:
                print(f"[HYBRID-REPL] ========== USING PTY MODE ==========")
                # Use PTY for proper terminal emulation (Unix only)
                # Set terminal size for better output
                import fcntl
                import termios
                import struct

                # Set a reasonable terminal size
                winsize = struct.pack('HHHH', 24, 80, 0, 0)  # 24 rows, 80 columns
                fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)

                # Start subprocess with PTY
                self.p = subprocess.Popen(
                    [Config.PYTHON, "-u", wrapper_path],  # Remove -i flag, wrapper handles REPL
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    cwd=os.path.dirname(self.script_path) if self.script_path else file_storage.ide_base,
                    env={**os.environ, "PYTHONUNBUFFERED": "1", "TERM": "xterm"},
                    preexec_fn=lambda: (os.setsid(), self.set_resource_limits()) if is_unix else None,
                    close_fds=False
                )
                print(f"[HYBRID-REPL] ✓ PTY subprocess created successfully")

                # Close slave end in parent
                os.close(slave_fd)
                slave_fd = None

                # Make master non-blocking
                fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

                self.master_fd = master_fd  # Store for reading/writing

            else:
                print(f"[HYBRID-REPL] ========== USING PIPE MODE (PTY not available) ==========")
                # Fall back to pipes (Windows or PTY not available)
                popen_kwargs = {
                    "stdin": subprocess.PIPE,
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.STDOUT,
                    "text": True,
                    "bufsize": 1,  # Line buffering
                    "cwd": os.path.dirname(self.script_path) if self.script_path else file_storage.ide_base,
                    "env": {**os.environ, "PYTHONUNBUFFERED": "1"},
                }

                if is_unix:
                    # Set resource limits on Unix
                    def setup_process():
                        os.setsid()
                        self.set_resource_limits()
                    popen_kwargs['preexec_fn'] = setup_process

                self.p = subprocess.Popen([Config.PYTHON, "-u", wrapper_path], **popen_kwargs)
                print(f"[HYBRID-REPL] ✓ PIPE subprocess created successfully")
                print(f"[HYBRID-REPL] ⚠️  Note: Using INPUT_REQUEST markers for input() detection")

            print(f"[HYBRID-REPL] Subprocess PID: {self.p.pid}")

            # Start appropriate output reader based on PTY or pipe mode
            if use_pty:
                # Store PTY flag for other methods
                self.use_pty = True
                print(f"[HYBRID-REPL] ✓ Using PTY output reader (read_pty_output)")
                output_thread = threading.Thread(target=self.read_pty_output)
            else:
                self.use_pty = False
                print(f"[HYBRID-REPL] ✗ Using PIPE output reader (read_output)")
                output_thread = threading.Thread(target=self.read_output)

            output_thread.daemon = True
            output_thread.start()

            # Start input handler thread
            input_thread = threading.Thread(target=self.handle_input)
            input_thread.daemon = True
            input_thread.start()

            # Start timeout monitor thread (v2 - improved with input pause and script start detection)
            timeout_thread = threading.Thread(target=self.monitor_timeout_v2)
            timeout_thread.daemon = True
            timeout_thread.start()

            # Wait for process to complete or be killed
            while self.alive and self.p.poll() is None:
                time.sleep(0.1)

            # Process ended - always send termination signal to update UI button state
            if self.p.poll() is not None:
                return_code = self.p.poll()
                # If had_error is True (timeout/infinite loop), don't send additional error message
                # The error message was already sent before killing the process
                if not self.had_error and return_code != 0:
                    self.response_to_client(1, {"stdout": f"Process exited with code {return_code}"})

                # Always send termination signal (code 1111) to update button state
                if self.had_error or not self.repl_mode:
                    # Program terminated without entering REPL, send final signal
                    self.response_to_client(1111, {"stdout": ""})

        except Exception as e:
            print(f"Error in HybridREPLThread: {e}")
            traceback.print_exc()
            self.response_to_client(1, {"stdout": f"Error: {str(e)}"})

        finally:
            # Cleanup PTY if used
            if master_fd is not None:
                try:
                    os.close(master_fd)
                except:
                    pass

            if slave_fd is not None:
                try:
                    os.close(slave_fd)
                except:
                    pass

            # Cleanup wrapper script
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

    def monitor_timeout_v2(self):
        """Simple and robust timeout monitor - kills process after 3 seconds of script execution"""
        print(f"[TIMEOUT_MONITOR_V2] Started for cmd_id: {self.cmd_id}")

        # PHASE 1: Wait for script to actually start executing (up to 10 seconds for Python startup)
        startup_timeout = time.time() + 10.0
        while not self.script_started and self.alive and self.p:
            if time.time() > startup_timeout:
                print(f"[TIMEOUT_MONITOR_V2] WARNING: Script didn't start within 10 seconds")
                break
            if self.p and self.p.poll() is not None:
                print(f"[TIMEOUT_MONITOR_V2] Process ended during startup")
                return
            time.sleep(0.1)

        if not self.script_started:
            print(f"[TIMEOUT_MONITOR_V2] Script never started, exiting monitor")
            return

        print(f"[TIMEOUT_MONITOR_V2] Script started, beginning 3-second timeout")

        # PHASE 2: Enforce 3-second timeout for script execution (excluding input wait time)
        script_exec_time = 0.0  # Accumulated execution time (excluding input waits)
        last_check = time.time()
        TIMEOUT_LIMIT = 3.0

        while self.alive and self.p and not self.repl_mode and not self.script_ended:
            try:
                # Check if process ended
                if self.p and self.p.poll() is not None:
                    print(f"[TIMEOUT_MONITOR_V2] Process ended naturally")
                    break

                current_time = time.time()

                # Check if process is idle (likely waiting for input)
                # If no output received for >1 second, assume waiting for input
                time_since_last_output = current_time - self._last_char_time if hasattr(self, '_last_char_time') else 0
                is_idle = time_since_last_output > 1.0

                # Only accumulate time if NOT waiting for input AND process is not idle
                if not self.waiting_for_input and not is_idle:
                    elapsed_since_last = current_time - last_check
                    script_exec_time += elapsed_since_last
                elif is_idle:
                    print(f"[TIMEOUT_MONITOR_V2] Paused (process idle {time_since_last_output:.1f}s - likely waiting for input)")
                elif self.waiting_for_input:
                    print(f"[TIMEOUT_MONITOR_V2] Paused (waiting for input)")

                last_check = current_time

                # Log every second
                if int(script_exec_time) > int(script_exec_time - 0.2):
                    print(f"[TIMEOUT_MONITOR_V2] Execution time: {script_exec_time:.1f}s / {TIMEOUT_LIMIT}s")

                # Hard timeout at 3 seconds
                if script_exec_time > TIMEOUT_LIMIT:
                    print(f"[TIMEOUT_MONITOR_V2] KILLING PROCESS - 3 second timeout exceeded!")

                    # Send timeout message
                    self.response_to_client(0, {
                        'stdout': f'\n\n{"="*50}\nTime Limit Exceeded (3 seconds)\n{"="*50}\n'
                    })

                    # Force kill the process and all children
                    if self.p:
                        try:
                            # Kill process group to ensure all children die
                            os.killpg(os.getpgid(self.p.pid), signal.SIGKILL)
                        except:
                            try:
                                self.p.kill()  # Fallback to regular kill
                            except:
                                pass

                    self.had_error = True
                    self.alive = False

                    # Clean up
                    self._release_execution_lock()
                    self.response_to_client(4000, {'error': 'Time limit exceeded'})
                    time.sleep(0.1)
                    self.response_to_client(1111, {'stdout': 'Process terminated'})
                    break

                time.sleep(0.1)

            except Exception as e:
                print(f"[TIMEOUT_MONITOR_V2] Error: {e}")
                break

        print(f"[TIMEOUT_MONITOR_V2] Exiting (script_ended={self.script_ended}, repl_mode={self.repl_mode})")

    def monitor_timeout(self):
        """Monitor execution time and kill if exceeds limit - only for script execution phase"""
        print(f"[TIMEOUT_MONITOR] Started for cmd_id: {self.cmd_id}")

        # Two-phase timeout approach:
        # Phase 1: Allow 10 seconds for wrapper initialization
        # Phase 2: Enforce 3-second timeout for script execution only (from __SCRIPT_START__ to __SCRIPT_END__)
        # Phase 3: No timeout once script completes (REPL mode)
        start_time = time.time()
        script_start_time = None  # Track when script actually starts

        # Timeout thresholds
        STARTUP_TIMEOUT = 10.0  # Allow 10 seconds for Python startup + wrapper init
        SCRIPT_TIMEOUT = 3.0    # Strict 3-second limit for actual script execution

        while self.alive and self.p and not self.repl_mode:
            try:
                # Check if process is still running
                if self.p.poll() is not None:
                    print(f"[TIMEOUT_MONITOR] Process {self.cmd_id} ended naturally")
                    break

                current_time = time.time()

                # Detect when script execution actually starts
                if script_start_time is None and self.script_started:
                    script_start_time = current_time
                    print(f"[TIMEOUT_MONITOR] Script execution started, enforcing 3-second limit")

                # CRITICAL: Stop timeout counting when script completes
                if self.script_ended:
                    print(f"[TIMEOUT_MONITOR] Script completed, stopping timeout monitor (REPL starting)")
                    break

                # Calculate elapsed time (pausing for input)
                if not self.waiting_for_input:
                    if script_start_time is not None and not self.script_ended:
                        # Script is executing - use strict 3-second timeout
                        self.timeout_accumulated = current_time - script_start_time
                        timeout_limit = SCRIPT_TIMEOUT
                        phase = "SCRIPT"
                    else:
                        # Still in startup phase - use relaxed 10-second timeout
                        self.timeout_accumulated = current_time - start_time
                        timeout_limit = STARTUP_TIMEOUT
                        phase = "STARTUP"

                    # Log progress every 0.5 seconds
                    if int(self.timeout_accumulated * 2) % 2 == 1:
                        print(f"[TIMEOUT_MONITOR] Process {self.cmd_id} [{phase}]: {self.timeout_accumulated:.1f}s / {timeout_limit}s")

                    # Check if timeout exceeded
                    if self.timeout_accumulated > timeout_limit:
                        print(f"[TIMEOUT] Process {self.cmd_id} exceeded {timeout_limit}-second limit in {phase} phase!")
                        # Send clear timeout message
                        self.response_to_client(0, {
                            'stdout': f'\n\n{"="*50}\nTime Limit Exceeded\nYour code took too long to execute (>{timeout_limit:.0f} seconds)\n{"="*50}\n'
                        })
                        # Mark as had error to prevent REPL from opening
                        self.had_error = True
                        # Kill the process
                        self.kill()
                        # Release execution lock
                        self._release_execution_lock()
                        # Send error signal to update UI (button state)
                        self.response_to_client(4000, {'error': 'Time limit exceeded'})
                        # Send termination signal
                        time.sleep(0.1)
                        self.response_to_client(1111, {'stdout': 'Process terminated due to timeout'})
                        break

                # Small delay to prevent busy waiting
                time.sleep(0.1)

            except Exception as e:
                print(f"[TIMEOUT_MONITOR] Error in timeout monitor: {e}")
                break

        print(f"[TIMEOUT_MONITOR] Exiting for cmd_id: {self.cmd_id}")

    def monitor_memory(self):
        """Monitor memory usage if psutil available"""
        if not psutil:
            return

        last_cpu_time = 0
        consecutive_high_cpu = 0

        while self.alive and self.p:
            try:
                if self.p and self.p.pid:
                    process = psutil.Process(self.p.pid)

                    # Get CPU time (actual computation time, not wall clock)
                    cpu_times = process.cpu_times()
                    current_cpu_time = cpu_times.user + cpu_times.system

                    # Check if process is actively computing
                    cpu_delta = current_cpu_time - last_cpu_time
                    last_cpu_time = current_cpu_time

                    # If CPU usage is high for consecutive checks, it's likely an infinite loop
                    if cpu_delta > 0.8:  # Using more than 80% CPU in the last second
                        consecutive_high_cpu += 1
                    else:
                        consecutive_high_cpu = 0  # Reset if CPU usage drops (likely waiting for input)

                    # Check total CPU time consumed
                    if current_cpu_time > self.cpu_time_limit:
                        print(f"[TIMEOUT] Process {self.cmd_id} exceeded CPU time limit ({self.cpu_time_limit}s)")
                        self.response_to_client(0, {
                            'stdout': f'\nConsole ending: Timeout 1 minute\n'
                        })
                        # Mark as had error to prevent REPL from opening
                        self.had_error = True
                        # Release execution lock
                        self._release_execution_lock()
                        # Send error signal to update UI (button state)
                        self.response_to_client(4000, {'error': 'Execution timeout exceeded'})
                        self.kill()
                        break

                    # Also check for sustained high CPU (infinite loop detection)
                    if consecutive_high_cpu >= 10:  # 10 seconds of continuous high CPU
                        print(f"[INFINITE LOOP] Process {self.cmd_id} detected in infinite loop")
                        # Send message to user console FIRST
                        self.response_to_client(0, {
                            'stdout': f'\n\nConsole ending: Timeout 1 minute (infinite loop detected)\n'
                        })
                        # Mark as had error to prevent REPL from opening
                        self.had_error = True
                        # Release execution lock
                        self._release_execution_lock()
                        # Send error signal to update UI (button state)
                        self.response_to_client(4000, {'error': 'Infinite loop detected'})
                        # Then kill the process
                        self.kill()
                        break

                    # Memory check
                    memory_mb = process.memory_info().rss / (1024 * 1024)

                    if memory_mb > self.memory_limit_mb:
                        print(f"[MEMORY] Process {self.cmd_id} exceeded memory limit ({self.memory_limit_mb}MB)")
                        self.response_to_client(
                            1, {"stdout": f"\n[MEMORY LIMIT] Memory usage exceeded ({self.memory_limit_mb}MB)\n"}
                        )
                        self.kill()
                        break

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process already terminated or access denied
                break
            except Exception as e:
                print(f"[TIMEOUT-MONITOR] Error monitoring process: {e}")
                # Continue monitoring even if there's an error
                pass

            time.sleep(1)

    def _kill_for_infinite_loop(self, reason):
        """Helper to kill process for infinite loop detection"""
        # Send error message
        self.response_to_client(0, {
            'stdout': f'\n\n{"="*50}\nInfinite Loop Detected\n{reason}\n{"="*50}\n'
        })

        # Kill the process
        if self.p:
            try:
                os.killpg(os.getpgid(self.p.pid), signal.SIGKILL)
            except:
                try:
                    self.p.kill()
                except:
                    pass

        self.had_error = True
        self.alive = False
        self._release_execution_lock()
        self.response_to_client(4000, {'error': 'Infinite loop detected'})
        self.response_to_client(1111, {'stdout': 'Process terminated'})

    def read_pty_output(self):
        """Read output from PTY (Unix only) - handles terminal properly"""
        import select
        buffer = ""
        print(f"[HYBRID-REPL] Starting PTY output reader for cmd_id: {self.cmd_id}")

        # Output rate limiting for infinite loop detection
        lines_count = 0
        window_start = time.time()
        total_lines = 0  # Track total output
        last_line = None  # Track repeated lines
        identical_count = 0  # Count consecutive identical lines

        # Safety thresholds (conservative to avoid false positives)
        MAX_LINES_PER_SECOND = 100  # Increased from 50 to allow burst output
        MAX_TOTAL_LINES = 10000  # Hard limit on total output
        MAX_IDENTICAL_LINES = 500  # Kill if same line repeated 500x in a row

        while self.alive and self.p and self.p.poll() is None:
            try:
                # Use select to check if data is available
                rlist, _, _ = select.select([self.master_fd], [], [], 0.01)

                if rlist:
                    # Read available data from PTY
                    try:
                        data = os.read(self.master_fd, 4096).decode('utf-8', errors='replace')
                    except OSError as e:
                        print(f"[PTY-DEBUG] PTY read error: {e}")
                        break  # PTY closed

                    if not data:
                        print(f"[PTY-DEBUG] PTY closed (no data)")
                        break

                    print(f"[PTY-DEBUG] Received {len(data)} bytes from PTY: {repr(data[:200])}")

                    # Track last output time for idle detection (used by timeout monitor)
                    self._last_char_time = time.time()

                    # FAST FLOOD DETECTION: If receiving full 4KB chunks repeatedly during script execution, likely an infinite loop
                    if not self.repl_mode and len(data) >= 4000:
                        lines_count += data.count('\n')
                        if lines_count >= 50:  # If we've received 50+ lines quickly
                            current_time = time.time()
                            elapsed = current_time - window_start
                            if elapsed < 0.5:  # 50+ lines in < 0.5 seconds = flooding
                                print(f"[RATE-LIMIT] FAST KILL - Output flooding detected ({lines_count} lines in {elapsed:.2f}s)")
                                self._kill_for_infinite_loop(f"Output flooding detected ({lines_count} lines in {elapsed:.2f} seconds)")
                                return

                    buffer += data

                    # Process special markers for mode transitions
                    # CRITICAL: Use independent 'if' statements (not elif) to process multiple markers in same buffer
                    if "__SCRIPT_START__" in buffer:
                        buffer = buffer.replace("__SCRIPT_START__", "")
                        # Strip any trailing whitespace/newlines after marker removal
                        buffer = buffer.lstrip('\r\n')
                        self.script_started = True  # Mark that script execution has started
                        self.response_to_client(0, None)  # Signal script started

                    if "__SCRIPT_END__" in buffer:
                        buffer = buffer.replace("__SCRIPT_END__", "")
                        self.script_ended = True     # Mark that script execution completed
                        self.script_executed = True
                        self._release_execution_lock()

                    if "__SCRIPT_ERROR__" in buffer:
                        buffer = buffer.replace("__SCRIPT_ERROR__", "")
                        self.had_error = True
                        if buffer.strip():
                            self.response_to_client(0, {"stdout": buffer})
                        self._release_execution_lock()
                        self.response_to_client(4000, {"error": "Script execution failed"})
                        self.kill()
                        break

                    if "__REPL_MODE_START__" in buffer:
                        print(f"[PTY-DEBUG] ✓ REPL mode marker detected - STOPPING TIMEOUT MONITOR")
                        # Send any text before the marker
                        pre_marker = buffer[:buffer.index("__REPL_MODE_START__")] if "__REPL_MODE_START__" in buffer else ""
                        if pre_marker:
                            for line in pre_marker.split('\n'):
                                if line:
                                    self.response_to_client(0, {"stdout": line})

                        # CRITICAL: Set REPL mode flag to stop timeout monitoring
                        self.repl_mode = True
                        buffer = buffer[buffer.index("__REPL_MODE_START__") + len("__REPL_MODE_START__"):] if "__REPL_MODE_START__" in buffer else buffer
                        print(f"[PTY-DEBUG] ✓ Sending REPL mode signal to client, self.repl_mode={self.repl_mode}")
                        print(f"[PTY-DEBUG] ✓ Timeout monitor will now exit (REPL mode active)")
                        self.response_to_client(5000, {"mode": "repl"})

                    # Check for matplotlib figures
                    if "__MATPLOTLIB_FIGURE_START__" in buffer and "__MATPLOTLIB_FIGURE_END__" in buffer:
                        start = buffer.index("__MATPLOTLIB_FIGURE_START__") + len("__MATPLOTLIB_FIGURE_START__")
                        end = buffer.index("__MATPLOTLIB_FIGURE_END__")
                        figure_data = buffer[start:end].strip()

                        # Send figure to client
                        self.response_to_client(3000, {"figure": figure_data})

                        # Clear the marker from buffer
                        buffer = buffer[end + len("__MATPLOTLIB_FIGURE_END__"):]

                    # CRITICAL: Check for INPUT_REQUEST markers from custom input() during script execution
                    if "__INPUT_REQUEST_START__" in buffer and "__INPUT_REQUEST_END__" in buffer:
                        # Extract the positions
                        marker_start = buffer.index("__INPUT_REQUEST_START__")
                        marker_end = buffer.index("__INPUT_REQUEST_END__") + len("__INPUT_REQUEST_END__")

                        # Extract prompt from markers
                        prompt_start = marker_start + len("__INPUT_REQUEST_START__")
                        prompt_end = buffer.index("__INPUT_REQUEST_END__")
                        prompt = buffer[prompt_start:prompt_end]

                        # Send any text before the marker
                        pre_marker = buffer[:marker_start]
                        if pre_marker and pre_marker.strip():
                            for line in pre_marker.split("\n"):
                                if line or line == "":
                                    self.response_to_client(0, {"stdout": line})

                        print(f"[PTY-DEBUG] Input request detected: {repr(prompt)}")

                        # Pause timeout when waiting for user input
                        self.waiting_for_input = True

                        # Send input request signal to enable input field (with prompt for frontend)
                        # The frontend will display the prompt, so we don't need to send it separately
                        self.response_to_client(2000, {"prompt": prompt})

                        # Clear the processed part from buffer
                        buffer = buffer[marker_end:].lstrip('\n')

                    # Send complete lines to client
                    while '\n' in buffer or '\r' in buffer:
                        # Handle both \n and \r\n line endings
                        line_end = buffer.find('\n')
                        cr_pos = buffer.find('\r')

                        if cr_pos != -1 and (line_end == -1 or cr_pos < line_end):
                            line_end = cr_pos

                        if line_end == -1:
                            break

                        line = buffer[:line_end]
                        buffer = buffer[line_end + 1:]

                        # Clean terminal codes and send line
                        clean_line = line.replace('\r', '').strip()
                        if clean_line or self.repl_mode:  # Send empty lines in REPL mode
                            self.response_to_client(0, {"stdout": line})

                            # Multiple safety checks for infinite loop detection (ONLY during script execution, not REPL)
                            if not self.repl_mode:
                                lines_count += 1
                                total_lines += 1

                                # Check 1: Total lines limit
                                if total_lines > MAX_TOTAL_LINES:
                                    print(f"[RATE-LIMIT] KILLING PROCESS - Total output limit exceeded ({total_lines} lines)")
                                    self._kill_for_infinite_loop("Total output limit exceeded (>10,000 lines)")
                                    return

                                # Check 2: Identical lines detection
                                if clean_line == last_line:
                                    identical_count += 1
                                    if identical_count >= MAX_IDENTICAL_LINES:
                                        print(f"[RATE-LIMIT] KILLING PROCESS - Same line repeated {identical_count} times")
                                        self._kill_for_infinite_loop(f"Same line repeated {MAX_IDENTICAL_LINES}+ times")
                                        return
                                else:
                                    identical_count = 0
                                    last_line = clean_line

                                # Check 3: Output rate limiting - check every 20 lines
                                if lines_count >= 20:
                                    current_time = time.time()
                                    elapsed = current_time - window_start

                                    # Calculate rate if we have at least 0.1 seconds of data
                                    if elapsed >= 0.1:
                                        rate = lines_count / elapsed
                                        print(f"[RATE-LIMIT] {lines_count} lines in {elapsed:.2f}s = {rate:.1f} lines/sec")

                                        if rate > MAX_LINES_PER_SECOND:
                                            print(f"[RATE-LIMIT] KILLING PROCESS - Output flooding detected ({rate:.1f} lines/sec)")
                                            self._kill_for_infinite_loop(f"Output flooding detected ({rate:.1f} lines/sec, max {MAX_LINES_PER_SECOND})")
                                            return

                                        # Reset counter for next window
                                        lines_count = 0
                                        window_start = current_time

                # Check for incomplete lines that might be prompts (ONLY in REPL mode)
                if buffer and self.repl_mode:
                    # Only check for real prompts in REPL mode, not during script execution
                    # Detect prompts ending with ':', '?', or containing '>>>'
                    # Must not contain newlines (to avoid detecting multiple lines as prompts)
                    stripped = buffer.strip()
                    is_prompt = ('\n' not in buffer and
                                (('>>>' in buffer) or
                                 stripped.endswith(': ') or
                                 stripped.endswith(':') or
                                 stripped.endswith('? ')))

                    if is_prompt:
                        print(f"[PTY-DEBUG] Sending REPL prompt: {repr(buffer)}")
                        self.response_to_client(0, {"stdout": buffer})
                        buffer = ""

            except Exception as e:
                print(f"[HYBRID-REPL] Error reading PTY output: {e}")
                break

        # Send any remaining buffer
        if buffer and buffer.strip():
            self.response_to_client(0, {"stdout": buffer})

    def read_output(self):
        """Read output from subprocess"""
        buffer = ""

        print(f"[HYBRID-REPL] Starting output reader for cmd_id: {self.cmd_id}")

        # Output rate limiting for infinite loop detection
        lines_count = 0
        window_start = time.time()
        total_lines = 0  # Track total output
        last_line = None  # Track repeated lines
        identical_count = 0  # Count consecutive identical lines

        # Safety thresholds (conservative to avoid false positives)
        MAX_LINES_PER_SECOND = 100  # Increased from 50 to allow burst output
        MAX_TOTAL_LINES = 10000  # Hard limit on total output
        MAX_IDENTICAL_LINES = 500  # Kill if same line repeated 500x in a row

        while self.alive and self.p and self.p.poll() is None:
            try:
                # Read character by character to handle input prompts without newlines
                char = self.p.stdout.read(1)
                if not char:
                    time.sleep(0.001)  # Reduced sleep for faster response
                    continue

                buffer += char
                self._last_char_time = time.time()  # Track when we last received a character

                # Check for special markers first - process immediately when we see the START marker
                # CRITICAL: Check for input markers IMMEDIATELY after each character
                if "__INPUT_REQUEST_START__" in buffer:
                    # Check if we have the complete marker pair
                    if "__INPUT_REQUEST_END__" in buffer:
                        # Extract the positions
                        marker_start = buffer.index("__INPUT_REQUEST_START__")
                        marker_end = buffer.index("__INPUT_REQUEST_END__") + len("__INPUT_REQUEST_END__")

                        # Extract prompt from markers
                        prompt_start = marker_start + len("__INPUT_REQUEST_START__")
                        prompt_end = buffer.index("__INPUT_REQUEST_END__")
                        prompt = buffer[prompt_start:prompt_end]

                        # Send any text before the marker
                        pre_marker = buffer[:marker_start]
                        if pre_marker and pre_marker.strip():
                            for line in pre_marker.split("\n"):
                                if line or line == "":
                                    self.response_to_client(0, {"stdout": line})

                        print(f"[HYBRID-REPL] Input request detected: {repr(prompt)}")

                        # Pause timeout when waiting for user input
                        self.waiting_for_input = True

                        # Send input request signal to enable input field (with prompt for frontend)
                        # The frontend will display the prompt, so we don't need to send it separately
                        self.response_to_client(2000, {"prompt": prompt})

                        # Clear the processed part from buffer
                        buffer = buffer[marker_end:].lstrip('\n')

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
                    # Strip any trailing whitespace/newlines after marker removal
                    buffer = buffer.lstrip('\r\n')
                    self.script_started = True  # Mark that script execution has started
                    # Send script start signal to client (null data triggers run=true)
                    self.response_to_client(0, None)

                elif "__SCRIPT_END__" in buffer:
                    # Script execution completed successfully
                    print(f"[HYBRID-REPL] Script execution completed")
                    buffer = buffer.replace("__SCRIPT_END__", "")
                    self.script_ended = True     # Mark that script execution completed
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

                        # Multiple safety checks for infinite loop detection
                        lines_count += 1
                        total_lines += 1

                        # Check 1: Total lines limit
                        if total_lines > MAX_TOTAL_LINES:
                            print(f"[RATE-LIMIT] KILLING PROCESS - Total output limit exceeded ({total_lines} lines)")
                            self._kill_for_infinite_loop("Total output limit exceeded (>10,000 lines)")
                            return

                        # Check 2: Identical lines detection
                        if clean_line == last_line:
                            identical_count += 1
                            if identical_count >= MAX_IDENTICAL_LINES:
                                print(f"[RATE-LIMIT] KILLING PROCESS - Same line repeated {identical_count} times")
                                self._kill_for_infinite_loop(f"Same line repeated {MAX_IDENTICAL_LINES}+ times")
                                return
                        else:
                            identical_count = 0
                            last_line = clean_line

                        # Check 3: Output rate limiting - check every 20 lines
                        if lines_count >= 20:
                            current_time = time.time()
                            elapsed = current_time - window_start

                            # Calculate rate if we have at least 0.1 seconds of data
                            if elapsed >= 0.1:
                                rate = lines_count / elapsed
                                print(f"[RATE-LIMIT] {lines_count} lines in {elapsed:.2f}s = {rate:.1f} lines/sec")

                                if rate > MAX_LINES_PER_SECOND:
                                    print(f"[RATE-LIMIT] KILLING PROCESS - Output flooding detected ({rate:.1f} lines/sec)")

                                    # Send error message
                                    self.response_to_client(0, {
                                        'stdout': f'\n\n{"="*50}\nOutput Rate Limit Exceeded\nYour code is producing too much output (>{MAX_LINES_PER_SECOND} lines/sec)\nLikely an infinite loop!\n{"="*50}\n'
                                    })

                                    # Kill the process
                                    if self.p:
                                        try:
                                            os.killpg(os.getpgid(self.p.pid), signal.SIGKILL)
                                        except:
                                            try:
                                                self.p.kill()
                                            except:
                                                pass

                                    self.had_error = True
                                    self.alive = False
                                    self._release_execution_lock()
                                    self.response_to_client(4000, {'error': 'Output rate limit exceeded'})
                                    self.response_to_client(1111, {'stdout': 'Process terminated'})
                                    return

                                # Reset counter for next window
                                lines_count = 0
                                window_start = current_time

                    # Keep the incomplete line in buffer
                    buffer = lines[-1]

                # In REPL mode, check for prompt patterns
                elif self.repl_mode:
                    # CRITICAL: Don't clean prompts if we have INPUT_REQUEST markers (even partial)
                    # This prevents corrupting input() prompts from user functions
                    if "__INPUT_REQUEST_" not in buffer:
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
                print(f"[HYBRID-REPL] REPL mode: {self.repl_mode}, Process alive: {self.p.poll() is None}, PTY: {getattr(self, 'use_pty', False)}")

                # Resume timeout counting after receiving input
                self.waiting_for_input = False

                if getattr(self, 'use_pty', False) and hasattr(self, 'master_fd'):
                    # PTY mode - write directly to the PTY master
                    try:
                        os.write(self.master_fd, (user_input + "\n").encode('utf-8'))
                        print(f"[HYBRID-REPL] Sent input to PTY: {user_input}")
                    except OSError as e:
                        print(f"[HYBRID-REPL] Error writing to PTY: {e}")
                elif self.p and self.p.stdin:
                    # Pipe mode - write to stdin
                    self.p.stdin.write(user_input + "\n")
                    self.p.stdin.flush()
                    print(f"[HYBRID-REPL] Sent input to subprocess: {user_input}")

                # Echo input back to client in REPL mode is handled by the REPL itself

            except Empty:
                continue
            except Exception as e:
                print(f"Error handling input: {e}")
                break
