#!/usr/bin/env python3
"""
Terminado-based REPL Handler - Production-grade replacement for HybridREPLThread

This implementation uses Terminado (Jupyter's terminal library) for:
- Robust PTY management
- Reliable process isolation
- Clean WebSocket ↔ Terminal bridging
- Battle-tested production code

Key improvements over HybridREPLThread:
- Single process instead of 4 threads per student
- Proper PTY handling via Terminado
- Cleaner state management
- Better error handling
- Less code (~400 lines vs ~1400 lines)
"""

import os
import sys
import json
import time
import asyncio
import tempfile
import signal
import base64
import traceback
import threading
from datetime import datetime
from typing import Optional, Callable

# Terminado imports
from terminado import TermManagerBase
import ptyprocess

# Project imports
from common.config import Config
from common.file_storage import file_storage
from command.response import response


class PythonREPLManager(TermManagerBase):
    """
    Custom Terminal Manager for Python REPL sessions

    Manages individual Python REPL processes using Terminado's pty infrastructure.
    Each student gets their own isolated terminal process.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.terminals = {}  # {term_name: terminal_instance}
        self.max_terminals = kwargs.get('max_terminals', 100)

    def new_terminal(self, **kwargs):
        """Create a new Python terminal session"""
        if len(self.terminals) >= self.max_terminals:
            raise RuntimeError(f"Maximum terminals reached ({self.max_terminals})")

        # Generate unique terminal name
        name = f"python-{int(time.time() * 1000)}-{len(self.terminals)}"

        # Get command to run (Python with wrapper script)
        command = kwargs.get('command', [Config.PYTHON, '-i'])
        cwd = kwargs.get('cwd', file_storage.ide_base)
        env = kwargs.get('env', {**os.environ, 'PYTHONUNBUFFERED': '1', 'TERM': 'xterm'})

        # Create PTY process
        terminal = ptyprocess.PtyProcess.spawn(
            command,
            cwd=cwd,
            env=env,
            dimensions=(24, 80)  # rows, cols
        )

        # Store terminal
        self.terminals[name] = terminal

        return name, terminal

    def get_terminal(self, name):
        """Get terminal by name"""
        return self.terminals.get(name)

    def kill_terminal(self, name):
        """Kill a terminal process"""
        terminal = self.terminals.get(name)
        if terminal and terminal.isalive():
            try:
                terminal.kill(signal.SIGTERM)
                terminal.wait()  # Clean up zombie
            except:
                try:
                    terminal.kill(signal.SIGKILL)
                except:
                    pass

        if name in self.terminals:
            del self.terminals[name]

    def kill_all(self):
        """Kill all terminals"""
        for name in list(self.terminals.keys()):
            self.kill_terminal(name)

    def list(self):
        """List all terminal names"""
        return list(self.terminals.keys())


class TerminadoPythonREPL(threading.Thread):
    """
    Production-grade Python REPL using Terminado

    Replaces HybridREPLThread with a cleaner, more reliable implementation.
    Uses Terminado's battle-tested PTY management instead of manual threading.

    Inherits from threading.Thread for compatibility with existing handler_info interface.
    """

    def __init__(
        self,
        cmd_id: str,
        client,
        event_loop,
        script_path: Optional[str] = None,
        username: Optional[str] = None,
        lock_manager=None,
        registry_callback: Optional[Callable] = None
    ):
        """
        Initialize Terminado Python REPL

        Args:
            cmd_id: Unique command ID for WebSocket communication
            client: WebSocket client reference
            event_loop: Asyncio event loop for async operations
            script_path: Path to Python script to run (None for empty REPL)
            username: Student username for permissions
            lock_manager: Execution lock manager
            registry_callback: Callback when REPL finishes
        """
        super().__init__()
        self.daemon = True  # Daemon thread for auto-cleanup

        self.cmd_id = cmd_id
        self.client = client
        self.event_loop = event_loop
        self.script_path = script_path
        self.username = username
        self.lock_manager = lock_manager
        self.registry_callback = registry_callback

        # Terminal state
        self.terminal_name = None
        self.terminal = None
        self.manager = PythonREPLManager()
        self.alive = True

        # Execution state tracking
        self.script_started = False
        self.script_ended = False
        self.repl_mode = False
        self.had_error = False
        self.waiting_for_input = False

        # Wrapper script
        self.wrapper_path = None

        # Timeout tracking
        self.start_time = time.time()
        self.timeout_limit = 3.0  # 3 seconds for scripts
        self.timeout_accumulated = 0.0
        self._last_output_time = time.time()

        # Output buffer and processing
        self.output_buffer = ""
        self.output_reader_task = None
        self.timeout_monitor_task = None

        # Resource limits
        self.memory_limit_mb = int(os.environ.get("MEMORY_LIMIT_MB", "128"))
        self.max_output_lines = 10000
        self.max_identical_lines = 500
        self.output_line_count = 0
        self.identical_line_count = 0
        self.last_line = None

    def create_wrapper_script(self) -> str:
        """
        Create Python wrapper script for hybrid script→REPL execution

        This is similar to HybridREPLThread's wrapper but simplified for Terminado.
        The wrapper:
        1. Runs the user's script (if provided)
        2. Transitions to REPL mode
        3. Persists variables from script to REPL
        """
        wrapper_code = '''import sys
import os
import code
import builtins
import base64
import io
import traceback

# Matplotlib lazy loading hook
_matplotlib_hooked = False

def _hook_matplotlib():
    """Hook matplotlib.pyplot.show for image capture"""
    global _matplotlib_hooked
    if _matplotlib_hooked:
        return

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        _original_show = plt.show

        def _custom_show(*args, **kwargs):
            """Capture matplotlib figures as base64 PNG"""
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
_original_import = builtins.__import__

def _custom_import(name, *args, **kwargs):
    result = _original_import(name, *args, **kwargs)
    if 'matplotlib' in name and not _matplotlib_hooked:
        _hook_matplotlib()
    return result

builtins.__import__ = _custom_import

# Custom input for script execution (markers for WebSocket communication)
_original_input = builtins.input

def _custom_input(prompt=""):
    """Custom input with markers for WebSocket bridge"""
    sys.stdout.flush()
    sys.stdout.write(f"__INPUT_REQUEST_START__{prompt}__INPUT_REQUEST_END__")
    sys.stdout.flush()

    # Force OS-level flush
    try:
        if hasattr(sys.stdout, 'fileno'):
            os.fsync(sys.stdout.fileno())
    except:
        pass

    # Read input (prompt already sent via marker)
    result = _original_input("")
    return result

# Override input during script execution
builtins.input = _custom_input

# Script variables storage
script_globals = {}
_script_success = False

'''

        # Add script execution if script_path provided
        if self.script_path:
            wrapper_code += f'''
# Execute user script
script_path = r"{self.script_path}"

print("__SCRIPT_START__")
sys.stdout.flush()

try:
    with open(script_path, 'r') as f:
        script_code = f.read()

    # Execute script and capture namespace
    exec(compile(script_code, script_path, 'exec'), script_globals)

    print("__SCRIPT_END__")
    sys.stdout.flush()
    _script_success = True

except Exception as e:
    traceback.print_exc()
    print("__SCRIPT_ERROR__")
    sys.stdout.flush()
    sys.exit(1)

# Inject script variables into global scope for REPL
for key, value in script_globals.items():
    if not key.startswith('__') and not key.startswith('_'):
        globals()[key] = value

'''

        # Add REPL startup code
        wrapper_code += f'''
# Start REPL only if script succeeded (or if no script)
if _script_success or not {bool(self.script_path)}:
    print("__REPL_MODE_START__")
    sys.stdout.flush()

    # Restore original input for REPL mode
    builtins.input = _original_input

    # Start interactive REPL with multiline support
    import readline
    import rlcompleter
    import code
    readline.parse_and_bind("tab: complete")

    multiline_buffer = []
    in_multiline = False

    # Interactive loop
    while True:
        try:
            prompt = ">>> "
            line = input(prompt)

            if in_multiline:
                multiline_buffer.append(line)
            else:
                multiline_buffer = [line]

            complete_source = '\\n'.join(multiline_buffer)

            # Check if code is complete
            try:
                compiled = code.compile_command(complete_source)

                if compiled is None:
                    # Incomplete, need more input
                    in_multiline = True
                    continue
                else:
                    # Complete, execute
                    in_multiline = False

                    if complete_source.strip():
                        exec_globals = globals().copy()
                        exec_globals.update(script_globals)

                        try:
                            result = eval(compiled, exec_globals)
                            if result is not None:
                                print(repr(result))
                        except SyntaxError:
                            try:
                                exec(compiled, exec_globals)
                            except Exception:
                                traceback.print_exc()
                        except Exception:
                            traceback.print_exc()

                        # Update script_globals with new variables
                        for k, v in exec_globals.items():
                            if not k.startswith('__') and not k.startswith('_'):
                                script_globals[k] = v

                        globals().update({{k: v for k, v in exec_globals.items() if not k.startswith('__')}})

                    multiline_buffer = []

            except (SyntaxError, OverflowError, ValueError) as e:
                print(f"SyntaxError: {{e}}")
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
else:
    # Script failed, exit
    sys.exit(1)
'''

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(wrapper_code)
            return f.name

    def run(self):
        """
        Thread run method - starts the async event loop for terminal management

        This is called by threading.Thread.start() and runs in a separate thread.
        It creates a new event loop and runs all async tasks within it.
        """
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run the async main logic
            loop.run_until_complete(self._async_main())

        except Exception as e:
            print(f"[TERMINADO-REPL] Fatal error in run(): {e}")
            traceback.print_exc()
        finally:
            try:
                loop.close()
            except:
                pass

    async def _async_main(self):
        """
        Main async execution logic for the REPL

        This replaces the old start() method and contains all async operations.
        """
        try:
            # Create wrapper script
            self.wrapper_path = self.create_wrapper_script()
            print(f"[TERMINADO-REPL] Wrapper created: {self.wrapper_path}")

            # Prepare terminal command
            command = [Config.PYTHON, '-u', self.wrapper_path]
            cwd = os.path.dirname(self.script_path) if self.script_path else file_storage.ide_base

            # Create terminal
            print(f"[TERMINADO-REPL] Creating terminal for cmd_id: {self.cmd_id}")
            self.terminal_name, self.terminal = self.manager.new_terminal(
                command=command,
                cwd=cwd
            )

            print(f"[TERMINADO-REPL] Terminal created: {self.terminal_name}, PID: {self.terminal.pid}")

            # Start output reader and timeout monitor concurrently
            await asyncio.gather(
                self._read_output(),
                self._monitor_timeout(),
                return_exceptions=True
            )

            print(f"[TERMINADO-REPL] Async main completed")

        except Exception as e:
            print(f"[TERMINADO-REPL] Error in async main: {e}")
            traceback.print_exc()
            await self._send_to_client(1, {"stdout": f"Error: {str(e)}"})
        finally:
            self.cleanup()

    async def _read_output(self):
        """
        Async task to read terminal output and send to WebSocket client

        This replaces the read_pty_output() thread in HybridREPLThread
        """
        print(f"[TERMINADO-REPL] Output reader started for {self.terminal_name}")

        try:
            while self.alive and self.terminal.isalive():
                try:
                    # Non-blocking read from terminal
                    output = self.terminal.read(4096)

                    if output:
                        self._last_output_time = time.time()
                        await self._process_output(output)
                    else:
                        # No output, small delay
                        await asyncio.sleep(0.01)

                except EOFError:
                    print(f"[TERMINADO-REPL] Terminal closed (EOF)")
                    break
                except Exception as e:
                    print(f"[TERMINADO-REPL] Error reading output: {e}")
                    await asyncio.sleep(0.1)

            print(f"[TERMINADO-REPL] Output reader finished")

            # Send termination signal
            if not self.repl_mode:
                await self._send_to_client(1111, {"stdout": ""})

        except Exception as e:
            print(f"[TERMINADO-REPL] Fatal error in output reader: {e}")
            traceback.print_exc()
        finally:
            self.cleanup()

    async def _process_output(self, output: str):
        """
        Process terminal output and handle special markers

        This replaces the marker processing in HybridREPLThread
        """
        self.output_buffer += output

        # Process special markers
        if "__SCRIPT_START__" in self.output_buffer:
            self.output_buffer = self.output_buffer.replace("__SCRIPT_START__", "")
            self.output_buffer = self.output_buffer.lstrip('\r\n')
            self.script_started = True
            await self._send_to_client(0, None)

        if "__SCRIPT_END__" in self.output_buffer:
            self.output_buffer = self.output_buffer.replace("__SCRIPT_END__", "")
            self.script_ended = True
            self._release_execution_lock()

        if "__SCRIPT_ERROR__" in self.output_buffer:
            self.output_buffer = self.output_buffer.replace("__SCRIPT_ERROR__", "")
            self.had_error = True
            if self.output_buffer.strip():
                await self._send_to_client(0, {"stdout": self.output_buffer})
            self._release_execution_lock()
            await self._send_to_client(4000, {"error": "Script execution failed"})
            self.kill()
            return

        if "__REPL_MODE_START__" in self.output_buffer:
            pre_marker = self.output_buffer[:self.output_buffer.index("__REPL_MODE_START__")]
            if pre_marker:
                for line in pre_marker.split('\n'):
                    if line:
                        await self._send_to_client(0, {"stdout": line})

            self.repl_mode = True
            self.output_buffer = self.output_buffer[self.output_buffer.index("__REPL_MODE_START__") + len("__REPL_MODE_START__"):]
            await self._send_to_client(5000, {"mode": "repl"})

        # Handle matplotlib figures
        if "__MATPLOTLIB_FIGURE_START__" in self.output_buffer and "__MATPLOTLIB_FIGURE_END__" in self.output_buffer:
            start = self.output_buffer.index("__MATPLOTLIB_FIGURE_START__") + len("__MATPLOTLIB_FIGURE_START__")
            end = self.output_buffer.index("__MATPLOTLIB_FIGURE_END__")
            figure_data = self.output_buffer[start:end].strip()

            await self._send_to_client(3000, {"figure": figure_data})
            self.output_buffer = self.output_buffer[end + len("__MATPLOTLIB_FIGURE_END__"):]

        # Handle input requests
        if "__INPUT_REQUEST_START__" in self.output_buffer and "__INPUT_REQUEST_END__" in self.output_buffer:
            marker_start = self.output_buffer.index("__INPUT_REQUEST_START__")
            marker_end = self.output_buffer.index("__INPUT_REQUEST_END__") + len("__INPUT_REQUEST_END__")

            prompt_start = marker_start + len("__INPUT_REQUEST_START__")
            prompt_end = self.output_buffer.index("__INPUT_REQUEST_END__")
            prompt = self.output_buffer[prompt_start:prompt_end]

            pre_marker = self.output_buffer[:marker_start]
            if pre_marker and pre_marker.strip():
                for line in pre_marker.split("\n"):
                    if line or line == "":
                        await self._send_to_client(0, {"stdout": line})

            self.waiting_for_input = True
            await self._send_to_client(2000, {"prompt": prompt})

            self.output_buffer = self.output_buffer[marker_end:].lstrip('\n')

        # Send complete lines to client
        while '\n' in self.output_buffer:
            line_end = self.output_buffer.find('\n')
            line = self.output_buffer[:line_end]
            self.output_buffer = self.output_buffer[line_end + 1:]

            clean_line = line.replace('\r', '').strip()
            if clean_line or self.repl_mode:
                await self._send_to_client(0, {"stdout": line})

                # Infinite loop detection (only during script execution)
                if not self.repl_mode:
                    await self._check_output_flooding(clean_line)

        # In REPL mode, send prompts
        if self.output_buffer and self.repl_mode:
            stripped = self.output_buffer.strip()
            is_prompt = ('\n' not in self.output_buffer and
                        (('>>>' in self.output_buffer) or
                         stripped.endswith(': ') or
                         stripped.endswith(':') or
                         stripped.endswith('? ')))

            if is_prompt:
                await self._send_to_client(0, {"stdout": self.output_buffer})
                self.output_buffer = ""

    async def _check_output_flooding(self, line: str):
        """Check for infinite loop via output flooding"""
        self.output_line_count += 1

        # Check 1: Total lines limit
        if self.output_line_count > self.max_output_lines:
            await self._send_to_client(0, {
                'stdout': f'\n\n{"="*50}\nOutput Limit Exceeded\nTotal output exceeded {self.max_output_lines} lines\n{"="*50}\n'
            })
            self.kill()
            await self._send_to_client(4000, {'error': 'Output limit exceeded'})
            await self._send_to_client(1111, {'stdout': 'Process terminated'})
            return

        # Check 2: Identical lines
        if line == self.last_line:
            self.identical_line_count += 1
            if self.identical_line_count >= self.max_identical_lines:
                await self._send_to_client(0, {
                    'stdout': f'\n\n{"="*50}\nInfinite Loop Detected\nSame line repeated {self.max_identical_lines}+ times\n{"="*50}\n'
                })
                self.kill()
                await self._send_to_client(4000, {'error': 'Infinite loop detected'})
                await self._send_to_client(1111, {'stdout': 'Process terminated'})
                return
        else:
            self.identical_line_count = 0
            self.last_line = line

    async def _monitor_timeout(self):
        """
        Monitor execution timeout (3 seconds for scripts, no timeout for REPL)

        This replaces monitor_timeout_v2() thread in HybridREPLThread
        """
        print(f"[TERMINADO-REPL] Timeout monitor started")

        # Wait for script to start (up to 10 seconds)
        startup_timeout = time.time() + 10.0
        while not self.script_started and self.alive and self.terminal.isalive():
            if time.time() > startup_timeout:
                print(f"[TERMINADO-REPL] Script didn't start within 10 seconds")
                break
            await asyncio.sleep(0.1)

        if not self.script_started:
            print(f"[TERMINADO-REPL] Timeout monitor exiting (script never started)")
            return

        print(f"[TERMINADO-REPL] Script started, enforcing 3-second timeout")

        # Enforce 3-second timeout for script execution
        script_exec_time = 0.0
        last_check = time.time()

        while self.alive and self.terminal.isalive() and not self.repl_mode and not self.script_ended:
            current_time = time.time()

            # Check if process is idle (likely waiting for input)
            time_since_output = current_time - self._last_output_time
            is_idle = time_since_output > 1.0

            # Only accumulate time if not waiting for input and not idle
            if not self.waiting_for_input and not is_idle:
                elapsed = current_time - last_check
                script_exec_time += elapsed

            last_check = current_time

            # Check timeout
            if script_exec_time > self.timeout_limit:
                print(f"[TERMINADO-REPL] 3-second timeout exceeded!")
                await self._send_to_client(0, {
                    'stdout': f'\n\n{"="*50}\nTime Limit Exceeded (3 seconds)\n{"="*50}\n'
                })

                self.had_error = True
                self.kill()
                self._release_execution_lock()
                await self._send_to_client(4000, {'error': 'Time limit exceeded'})
                await asyncio.sleep(0.1)
                await self._send_to_client(1111, {'stdout': 'Process terminated'})
                break

            await asyncio.sleep(0.1)

        print(f"[TERMINADO-REPL] Timeout monitor finished")

    def send_input(self, user_input: str):
        """
        Send user input to the terminal (synchronous interface for compatibility)

        This method is called from the WebSocket handler and needs to be synchronous.
        It writes directly to the PTY terminal.

        Args:
            user_input: The user's input string

        Returns:
            bool: True if input was sent successfully, False otherwise
        """
        if self.terminal and self.terminal.isalive():
            try:
                # Write input to terminal (ptyprocess uses write() method)
                self.terminal.write((user_input + '\n').encode('utf-8'))
                self.waiting_for_input = False
                print(f"[TERMINADO-REPL] Sent input: {user_input}")
                return True
            except Exception as e:
                print(f"[TERMINADO-REPL] Error sending input: {e}")
                traceback.print_exc()
                return False
        print(f"[TERMINADO-REPL] Cannot send input: terminal not alive")
        return False

    def kill(self):
        """Kill the terminal process"""
        print(f"[TERMINADO-REPL] Killing terminal: {self.terminal_name}")
        self.alive = False
        if self.terminal_name:
            self.manager.kill_terminal(self.terminal_name)

    def stop(self):
        """Stop the terminal gracefully"""
        print(f"[TERMINADO-REPL] Stopping terminal: {self.terminal_name}")
        self.kill()

    def cleanup(self):
        """Clean up resources"""
        print(f"[TERMINADO-REPL] Cleaning up")

        # Kill terminal
        if self.terminal_name:
            try:
                self.manager.kill_terminal(self.terminal_name)
            except:
                pass

        # Remove wrapper script
        if self.wrapper_path and os.path.exists(self.wrapper_path):
            try:
                os.unlink(self.wrapper_path)
            except:
                pass

        # Release execution lock
        self._release_execution_lock()

        # Call registry callback
        if self.registry_callback:
            try:
                self.registry_callback(self.cmd_id)
            except:
                pass

    def _release_execution_lock(self):
        """Release execution lock for this script"""
        if self.lock_manager and self.script_path and self.username:
            try:
                self.lock_manager.release_execution_lock(self.username, self.script_path, self.cmd_id)
            except Exception as e:
                print(f"[TERMINADO-REPL] Error releasing lock: {e}")

    async def _send_to_client(self, code: int, data):
        """
        Send response to WebSocket client via the main event loop

        Since we're running in a separate thread with our own event loop,
        we need to schedule the response on the main Tornado event loop.
        """
        try:
            # Schedule the response on the main event loop
            asyncio.run_coroutine_threadsafe(
                response(self.client, self.cmd_id, code, data),
                self.event_loop
            )
        except Exception as e:
            print(f"[TERMINADO-REPL] Error sending to client: {e}")

    def is_alive(self):
        """Check if terminal is alive"""
        return self.alive and self.terminal and self.terminal.isalive()

    def update_client(self, client, cmd_id):
        """Update client reference for reconnections"""
        print(f"[TERMINADO-REPL] Updating client: old_cmd_id={self.cmd_id}, new_cmd_id={cmd_id}")
        self.client = client
        self.cmd_id = cmd_id
