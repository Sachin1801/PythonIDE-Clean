#!/usr/bin/env python3
"""
Simple Execution Engine V2 - With proper input() support
Clean implementation for running Python scripts and transitioning to REPL
"""

import subprocess
import threading
import time
import os
import sys
import json
import asyncio
import select
import pty
import re
from queue import Queue, Empty
import signal
import traceback
from typing import Optional, Dict, Any
import tempfile
import base64
import io
import fcntl
import struct
import termios

from command.exec_protocol import (
    MessageType, ExecutionState, create_message,
    debug_log, set_debug_mode
)

class SimpleExecutorV2(threading.Thread):
    """
    Enhanced executor with proper input() handling for both script and REPL modes
    """

    def __init__(self, cmd_id: str, client, event_loop,
                 script_path: Optional[str] = None, username: Optional[str] = None):
        super().__init__()
        self.cmd_id = cmd_id
        self.client = client
        self.event_loop = event_loop
        self.script_path = script_path
        self.username = username

        # Process management
        self.process = None
        self.master_fd = None
        self.alive = True
        self.state = ExecutionState.IDLE

        # Input handling
        self.input_queue = Queue()
        self.waiting_for_input = False
        self.input_prompt = ""
        self.last_output = ""
        self.output_buffer = ""

        # Timing
        self.start_time = None
        self.script_timeout = 30  # Increased for input() handling
        self.input_timeout = 300  # 5 minutes for user input
        self.repl_timeout = 300  # 5 minutes for REPL
        self.last_activity = time.time()

        # Script code for REPL re-execution
        self.script_code = None

        # Debug mode
        set_debug_mode(os.environ.get("DEBUG_MODE", "false").lower() == "true")

        self.daemon = True

        print(f"[SimpleExecutorV2] Initialized for cmd_id: {cmd_id}, script: {script_path}")

    def send_message(self, msg_type: MessageType, data: Any):
        """Send message to frontend via WebSocket"""
        message = create_message(self.cmd_id, msg_type, data)
        message["cmd"] = "repl_output"

        asyncio.run_coroutine_threadsafe(
            self.client.write_message(json.dumps(message)),
            self.event_loop
        )

        if msg_type != MessageType.DEBUG:
            print(f"[SimpleExecutorV2] Sent {msg_type.value}: {str(data)[:100]}")

    def run(self):
        """Main execution thread"""
        print(f"[SimpleExecutorV2] Starting execution thread")
        self.start_time = time.time()

        try:
            if self.script_path:
                # Execute script first
                self.execute_script_with_input()

                # If script succeeded, transition to REPL
                if self.state != ExecutionState.TERMINATED:
                    self.start_repl()
            else:
                # Direct REPL mode (no script)
                self.start_repl()

        except Exception as e:
            print(f"[SimpleExecutorV2] Fatal error: {e}")
            traceback.print_exc()
            self.send_message(MessageType.ERROR, {
                "error": str(e),
                "traceback": traceback.format_exc()
            })
        finally:
            self.cleanup()

    def execute_script_with_input(self):
        """Execute Python script with proper input() handling"""
        print(f"[SimpleExecutorV2] Executing script with input support: {self.script_path}")
        self.state = ExecutionState.SCRIPT_RUNNING

        try:
            # Read the script
            with open(self.script_path, 'r', encoding='utf-8') as f:
                self.script_code = f.read()

            # Create PTY with proper size
            master_fd, slave_fd = pty.openpty()
            self.master_fd = master_fd

            # Set PTY size for better compatibility
            winsize = struct.pack('HHHH', 24, 80, 0, 0)  # 24 rows, 80 cols
            fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)

            # Make master_fd non-blocking
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Prepare environment
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'

            # Start the script process directly (no wrapper needed for input handling)
            self.process = subprocess.Popen(
                [sys.executable, '-u', self.script_path],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                preexec_fn=os.setsid,
                cwd=os.path.dirname(os.path.abspath(self.script_path)),
                env=env
            )

            os.close(slave_fd)

            # Start input handler thread
            input_handler = threading.Thread(target=self.handle_script_input)
            input_handler.daemon = True
            input_handler.start()

            # Read output and detect input() calls
            self.output_buffer = ""
            self.last_output = ""
            script_complete = False

            while self.alive and self.process.poll() is None:
                # Check timeout (but pause during input waiting)
                if not self.waiting_for_input:
                    elapsed = time.time() - self.last_activity
                    if elapsed > self.script_timeout:
                        print(f"[SimpleExecutorV2] Script timeout after {elapsed}s")
                        self.process.terminate()
                        time.sleep(0.1)
                        if self.process.poll() is None:
                            self.process.kill()
                        self.send_message(MessageType.STDERR,
                            f"\n⏱️ Execution timed out after {self.script_timeout} seconds\n")
                        self.state = ExecutionState.TERMINATED
                        return

                # Read available output
                ready, _, _ = select.select([master_fd], [], [], 0.1)
                if ready:
                    try:
                        chunk = os.read(master_fd, 4096)
                        if not chunk:
                            break

                        # Decode and process output
                        text = chunk.decode('utf-8', errors='replace')
                        self.output_buffer += text
                        self.last_output += text

                        # Detect input() prompt patterns
                        # Python's input() writes prompt to stdout then waits on stdin
                        # Common patterns:
                        # 1. Ends with ": " and no newline
                        # 2. Ends with "? " and no newline
                        # 3. Contains "input" and ends without newline
                        lines = self.output_buffer.split('\n')

                        # Check if we're waiting for input
                        if len(lines) > 0:
                            last_line = lines[-1]

                            # Check if last line looks like an input prompt
                            if last_line and not last_line.endswith('\n'):
                                # Heuristic: if output stops mid-line and contains certain patterns
                                is_input_prompt = False

                                # Check common prompt endings
                                prompt_patterns = [
                                    r': $',      # Ends with ": "
                                    r'\? $',     # Ends with "? "
                                    r'> $',      # Ends with "> "
                                    r': ?$',     # Ends with ":"
                                    r'\? ?$',    # Ends with "?"
                                ]

                                for pattern in prompt_patterns:
                                    if re.search(pattern, last_line):
                                        is_input_prompt = True
                                        break

                                # Also check if process is blocked on read
                                # (This happens when input() is called)
                                if not is_input_prompt and len(last_line) > 0:
                                    # Wait a bit to see if more output comes
                                    time.sleep(0.05)
                                    ready2, _, _ = select.select([master_fd], [], [], 0.01)
                                    if not ready2:
                                        # No more output, likely waiting for input
                                        is_input_prompt = True

                                if is_input_prompt and not self.waiting_for_input:
                                    print(f"[SimpleExecutorV2] Detected input prompt: {last_line}")
                                    self.waiting_for_input = True
                                    self.input_prompt = last_line

                                    # Send everything except the prompt
                                    if len(lines) > 1:
                                        output_to_send = '\n'.join(lines[:-1]) + '\n'
                                        self.send_message(MessageType.STDOUT, output_to_send)

                                    # Send input request
                                    self.send_message(MessageType.INPUT_REQUEST, self.input_prompt)
                                    self.output_buffer = ""  # Clear buffer

                                    # Reset activity timer during input wait
                                    self.last_activity = time.time()
                                    continue

                        # Send complete lines if not waiting for input
                        if not self.waiting_for_input and '\n' in self.output_buffer:
                            lines = self.output_buffer.split('\n')
                            # Send all complete lines
                            for line in lines[:-1]:
                                self.send_message(MessageType.STDOUT, line + '\n')
                            # Keep incomplete last line in buffer
                            self.output_buffer = lines[-1]

                        self.last_activity = time.time()

                    except OSError as e:
                        if e.errno == 5:  # Input/output error (process ended)
                            break
                        else:
                            raise

            # Send any remaining output
            if self.output_buffer:
                self.send_message(MessageType.STDOUT, self.output_buffer)
                self.output_buffer = ""

            # Check exit code
            exit_code = self.process.wait() if self.process else -1

            if exit_code == 0:
                print(f"[SimpleExecutorV2] Script executed successfully")
                self.state = ExecutionState.SCRIPT_COMPLETE
            else:
                print(f"[SimpleExecutorV2] Script failed with exit code: {exit_code}")
                if exit_code != 0:
                    self.send_message(MessageType.STDERR, f"\n❌ Script exited with code {exit_code}\n")
                self.state = ExecutionState.TERMINATED

        except Exception as e:
            print(f"[SimpleExecutorV2] Script execution error: {e}")
            traceback.print_exc()
            self.send_message(MessageType.ERROR, {
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            self.state = ExecutionState.TERMINATED

    def handle_script_input(self):
        """Handle input from queue and send to script"""
        while self.alive and self.process and self.process.poll() is None:
            try:
                # Wait for input with timeout
                user_input = self.input_queue.get(timeout=0.5)

                if self.master_fd and self.waiting_for_input:
                    # Send input to process
                    os.write(self.master_fd, (user_input + '\n').encode('utf-8'))

                    # Echo the input with prompt
                    self.send_message(MessageType.STDOUT, self.input_prompt + user_input + '\n')

                    self.waiting_for_input = False
                    self.input_prompt = ""
                    self.last_activity = time.time()

                    print(f"[SimpleExecutorV2] Sent input to script: {user_input[:50]}")

            except Empty:
                continue
            except Exception as e:
                print(f"[SimpleExecutorV2] Input handler error: {e}")

    def start_repl(self):
        """Start an interactive Python REPL session with input() support"""
        print(f"[SimpleExecutorV2] Starting REPL mode")
        self.state = ExecutionState.REPL_ACTIVE

        try:
            # Close previous process if any
            if self.process:
                if self.process.poll() is None:
                    self.process.terminate()
                    self.process.wait()
                self.process = None

            if self.master_fd:
                try:
                    os.close(self.master_fd)
                except:
                    pass
                self.master_fd = None

            # Create new PTY for REPL
            master_fd, slave_fd = pty.openpty()
            self.master_fd = master_fd

            # Set PTY size
            winsize = struct.pack('HHHH', 24, 80, 0, 0)
            fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)

            # Make non-blocking
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Start Python in interactive mode
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'

            python_cmd = [sys.executable, '-u', '-i']

            # Create startup script to load variables
            startup_script = None
            if hasattr(self, 'script_code') and self.script_code:
                startup_script = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')

                # Escape the script code
                escaped_code = self.script_code.replace('\\', '\\\\').replace("'''", "\\'''")

                startup_script.write(f"""# Re-execute script to load variables into REPL
import sys
import io
import os

# Change to script directory
os.chdir('{os.path.dirname(os.path.abspath(self.script_path))}')

# Suppress output during re-execution
_old_stdout = sys.stdout
_old_stderr = sys.stderr
sys.stdout = sys.stderr = io.StringIO()

try:
    exec('''{escaped_code}''')
    _vars = [k for k in globals().keys() if not k.startswith('_')]
finally:
    sys.stdout = _old_stdout
    sys.stderr = _old_stderr
    if '_vars' in locals():
        print(f'\\n🎯 Script variables loaded into REPL: {{", ".join(_vars)}}\\n')
""")
                startup_script.close()
                env['PYTHONSTARTUP'] = startup_script.name

            # Start REPL process
            self.process = subprocess.Popen(
                python_cmd,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                preexec_fn=os.setsid,
                env=env,
                cwd=os.path.dirname(os.path.abspath(self.script_path)) if self.script_path else os.getcwd()
            )

            os.close(slave_fd)

            # Send REPL ready signal
            self.send_message(MessageType.REPL_READY, {"prompt": ">>> "})

            # Start REPL input handler
            repl_input_handler = threading.Thread(target=self.handle_repl_input_v2)
            repl_input_handler.daemon = True
            repl_input_handler.start()

            # Read REPL output
            self.output_buffer = ""
            current_prompt = ">>> "

            while self.alive and self.process.poll() is None:
                ready, _, _ = select.select([master_fd], [], [], 0.1)
                if ready:
                    try:
                        chunk = os.read(master_fd, 4096)
                        if not chunk:
                            break

                        text = chunk.decode('utf-8', errors='replace')
                        self.output_buffer += text

                        # In REPL, we need to handle:
                        # 1. Regular output
                        # 2. Prompts (>>> and ...)
                        # 3. input() calls within REPL

                        # Send output immediately for better responsiveness
                        self.send_message(MessageType.STDOUT, text)

                        # Check if this looks like an input() call in REPL
                        # This is trickier because REPL already uses prompts
                        if not text.endswith(('>>> ', '... ')):
                            # Check for input prompt pattern
                            lines = text.split('\n')
                            last_line = lines[-1] if lines else ""

                            # If last line looks like input prompt (not >>> or ...)
                            if last_line and not last_line.endswith('\n'):
                                if re.search(r': $|\? $|> $', last_line) and '>>>' not in last_line and '...' not in last_line:
                                    print(f"[SimpleExecutorV2] REPL input() detected: {last_line}")
                                    self.waiting_for_input = True
                                    self.input_prompt = last_line
                                    self.send_message(MessageType.INPUT_REQUEST, last_line)

                        self.output_buffer = ""

                    except OSError as e:
                        if e.errno == 5:
                            break
                        else:
                            raise

            # Cleanup startup script
            if startup_script:
                try:
                    os.unlink(startup_script.name)
                except:
                    pass

            print(f"[SimpleExecutorV2] REPL terminated")
            self.state = ExecutionState.TERMINATED

        except Exception as e:
            print(f"[SimpleExecutorV2] REPL error: {e}")
            traceback.print_exc()
            self.send_message(MessageType.ERROR, {
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            self.state = ExecutionState.TERMINATED

    def handle_repl_input_v2(self):
        """Enhanced REPL input handler that handles both commands and input() responses"""
        while self.alive and self.process and self.process.poll() is None:
            try:
                user_input = self.input_queue.get(timeout=0.5)

                if self.master_fd:
                    # Send input to REPL
                    os.write(self.master_fd, (user_input + '\n').encode('utf-8'))

                    # Clear waiting flag if we were waiting for input()
                    if self.waiting_for_input:
                        self.waiting_for_input = False
                        self.input_prompt = ""

                    print(f"[SimpleExecutorV2] Sent to REPL: {user_input[:50]}")

            except Empty:
                continue
            except Exception as e:
                print(f"[SimpleExecutorV2] REPL input handler error: {e}")

    def send_input(self, text: str):
        """Queue user input to be sent to process"""
        print(f"[SimpleExecutorV2] Queuing input: {text[:50]}")
        self.input_queue.put(text)

    def stop(self):
        """Stop execution gracefully"""
        print(f"[SimpleExecutorV2] Stopping execution")
        self.alive = False

        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                time.sleep(0.1)

                if self.process.poll() is None:
                    self.process.kill()
                    self.process.wait()

            except Exception as e:
                print(f"[SimpleExecutorV2] Error stopping process: {e}")

        # Send completion message
        duration = time.time() - self.start_time if self.start_time else 0
        self.send_message(MessageType.COMPLETE, {
            "exit_code": self.process.returncode if self.process else -1,
            "duration": duration
        })

    def cleanup(self):
        """Clean up resources"""
        print(f"[SimpleExecutorV2] Cleaning up")

        if self.master_fd:
            try:
                os.close(self.master_fd)
            except:
                pass
            self.master_fd = None

        if self.process:
            if self.process.poll() is None:
                self.process.kill()
            self.process = None

        self.state = ExecutionState.TERMINATED