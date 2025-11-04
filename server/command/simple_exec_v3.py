#!/usr/bin/env python3
"""
Simple Execution Engine V3 - Using Python's code module
Clean implementation using Python's built-in InteractiveConsole
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
import code
import io
import contextlib
from queue import Queue, Empty
import signal
import traceback
from typing import Optional, Dict, Any
import tempfile
import resource

from command.exec_protocol import (
    MessageType, ExecutionState, create_message,
    debug_log, set_debug_mode
)


class InteractiveREPLConsole(code.InteractiveConsole):
    """Custom InteractiveConsole that sends output to WebSocket"""

    def __init__(self, locals, executor):
        super().__init__(locals=locals)
        self.executor = executor
        self.output_buffer = io.StringIO()

    def write(self, data):
        """Override write to capture output"""
        if data:
            # Send to WebSocket (includes infinite loop check)
            self.executor.send_message(MessageType.STDOUT, data)
            # Also buffer it
            self.output_buffer.write(data)

    def raw_input(self, prompt=""):
        """Override raw_input to handle input via WebSocket"""
        if prompt:
            self.executor.send_message(MessageType.INPUT_REQUEST, prompt)

        # Wait for input from WebSocket
        self.executor.waiting_for_input = True
        input_value = None

        try:
            # Wait up to 5 minutes for user input
            input_value = self.executor.input_queue.get(timeout=300)
            self.executor.waiting_for_input = False

            # Don't echo the input - the user already sees it in the input field
            
            self.executor.send_message(MessageType.STDOUT, input_value + "\n")
            # Standard Python input() doesn't echo either
            return input_value

        except Empty:
            self.executor.waiting_for_input = False
            raise EOFError("No input received")

    def push(self, line):
        """Override push to track activity"""
        self.executor.last_activity = time.time()
        return super().push(line)


class SimpleExecutorV3(threading.Thread):
    """
    Enhanced executor using Python's code module for proper REPL
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
        self.last_activity = time.time()

        # Timing
        self.start_time = None
        self.script_timeout = 30
        self.repl_timeout = 300  # 5 minutes for REPL

        # REPL console
        self.console = None
        self.namespace = {}

        # Debug mode
        set_debug_mode(os.environ.get("DEBUG_MODE", "false").lower() == "true")

        # Thread management - CRITICAL for cleanup
        self.daemon = True
        self._stop_event = threading.Event()  # For clean shutdown
        self._cleanup_done = False  # Prevent double cleanup
        self._lock_released = False  # Track if execution lock has been released

        # ===== INFINITE LOOP DETECTION VARIABLES =====
        # Layer 1: Output rate limiting
        self.output_start_time = time.time()
        self.output_line_count = 0
        self.MAX_LINES_PER_SECOND = 100  # Kill if > 100 lines/sec
        self.last_rate_check = time.time()

        # Layer 2: Total output limiting
        self.total_output_lines = 0
        self.MAX_TOTAL_LINES = 10000  # Kill at 10,000 lines

        # Layer 3: Identical line detection
        self.last_output_line = None
        self.identical_line_count = 0
        self.MAX_IDENTICAL_LINES = 500  # Kill if same line 500x

        # Fast flood detection (catches immediate spam)
        self.flood_check_buffer = []
        self.flood_check_time = time.time()

        # ===== RESOURCE LIMITS =====
        self.MEMORY_LIMIT_MB = 128  # 128MB memory limit
        self.CPU_TIME_LIMIT = 10    # 10 seconds CPU time (different from wall time)

        # print(f"[SimpleExecutorV3-INIT] Thread ID: {threading.get_ident()}")
        # print(f"[SimpleExecutorV3-INIT] cmd_id: {cmd_id}, script: {script_path}")
        # print(f"[SimpleExecutorV3-INIT] username: {username}")
        # print(f"[SimpleExecutorV3-INIT] alive: {self.alive}, state: {self.state}")
        # print(f"[SimpleExecutorV3-INIT] Infinite loop detection enabled:"
            #   f" rate_limit={self.MAX_LINES_PER_SECOND}/sec,"
            #   f" total_limit={self.MAX_TOTAL_LINES},"
            #   f" identical_limit={self.MAX_IDENTICAL_LINES}")

    def send_message(self, msg_type: MessageType, data: Any):
        """Send message to frontend via WebSocket"""
        # CRITICAL: Check if we're still alive before sending
        if not self.alive:
            print(f"[SimpleExecutorV3-SEND] WARNING: Attempt to send message after executor stopped")
            print(f"[SimpleExecutorV3-SEND] cmd_id: {self.cmd_id}, msg_type: {msg_type}, alive: {self.alive}")
            return

        # Update heartbeat when sending messages (shows executor is active)
        if hasattr(self, 'username') and hasattr(self, 'script_path') and self.username and self.script_path:
            try:
                from .execution_lock_manager import execution_lock_manager
                execution_lock_manager.update_heartbeat(self.username, self.script_path)
            except:
                pass  # Don't fail if heartbeat update fails

        # Check for infinite loop on STDOUT/STDERR messages
        if msg_type in [MessageType.STDOUT, MessageType.STDERR] and data:
            self._check_infinite_loop(data)

        message = create_message(self.cmd_id, msg_type, data)
        message["cmd"] = "repl_output"

        # write_message is synchronous, so we need to schedule it properly
        def _send():
            try:
                if self.client and hasattr(self.client, 'write_message'):
                    self.client.write_message(json.dumps(message))
                else:
                    print(f"[SimpleExecutorV3-SEND] ERROR: Client not available or invalid")
            except Exception as e:
                print(f"[SimpleExecutorV3-SEND] ERROR sending message: {e}")
                print(f"[SimpleExecutorV3-SEND] cmd_id: {self.cmd_id}, msg_type: {msg_type}")

        # Schedule the synchronous write_message to run in the event loop
        try:
            self.event_loop.call_soon_threadsafe(_send)
        except Exception as e:
            print(f"[SimpleExecutorV3-SEND] ERROR scheduling message: {e}")

        if msg_type != MessageType.DEBUG:
            data_preview = str(data)[:100] if data else "None"
            # print(f"[SimpleExecutorV3-SEND] Sent {msg_type.value}: {data_preview}")

    def handle_input(self, text: str):
        """Handle input from WebSocket"""
        # print(f"[SimpleExecutorV3] Received input: {text}")
        self.input_queue.put(text)

    def send_input(self, text: str):
        """Alias for handle_input to match expected interface"""
        return self.handle_input(text)

    def run(self):
        """Main execution thread"""
        print(f"[SimpleExecutorV3-RUN] ===== THREAD STARTED =====")
        # print(f"[SimpleExecutorV3-RUN] Thread ID: {threading.get_ident()}")
        # print(f"[SimpleExecutorV3-RUN] cmd_id: {self.cmd_id}")
        # print(f"[SimpleExecutorV3-RUN] script_path: {self.script_path}")
        # print(f"[SimpleExecutorV3-RUN] alive: {self.alive}, state: {self.state}")

        self.start_time = time.time()

        try:
            # Set resource limits before execution
            self.set_resource_limits()

            # Create namespace for execution
            self.namespace = {
                '__name__': '__main__',
                '__doc__': None,
                'input': self.repl_input  # Custom input function
            }
            # print(f"[SimpleExecutorV3-RUN] Namespace created")

            # Execute script if provided
            if self.script_path:
                # print(f"[SimpleExecutorV3-RUN] Executing script: {self.script_path}")
                self.execute_script()

                # CRITICAL: Release execution lock after script completes, BEFORE REPL starts
                # This allows the same file to be run again while REPL is still active
                if not self._lock_released and hasattr(self, 'username') and hasattr(self, 'script_path') and self.username and self.script_path:
                    try:
                        from .execution_lock_manager import execution_lock_manager
                        execution_lock_manager.release_execution_lock(self.username, self.script_path, self.cmd_id)
                        self._lock_released = True  # Mark lock as released
                        print(f"[SimpleExecutorV3-RUN] ✅ Released execution lock after script completion (before REPL)")
                    except Exception as e:
                        print(f"[SimpleExecutorV3-RUN] ⚠️ Error releasing lock after script: {e}")
            else:
                # print(f"[SimpleExecutorV3-RUN] No script provided, starting REPL directly")
                pass  # Keep the block valid even with commented prints

            # Start REPL (whether script was run or not)
            if self.alive:  # Only start REPL if still alive
                # print(f"[SimpleExecutorV3-RUN] Starting REPL mode")
                self.start_repl()
            else:
                print(f"[SimpleExecutorV3-RUN] Skipping REPL (alive=False)")

        except Exception as e:
            print(f"[SimpleExecutorV3-RUN] ERROR: Execution failed")
            print(f"[SimpleExecutorV3-RUN] Exception: {e}")
            traceback.print_exc()

            if self.alive:  # Only send error if still alive
                self.send_message(MessageType.ERROR, {
                    "error": f"Execution failed: {str(e)}",
                    "traceback": traceback.format_exc()
                })

        finally:
            # print(f"[SimpleExecutorV3-RUN] Entering cleanup phase")
            self.cleanup()
            # print(f"[SimpleExecutorV3-RUN] ===== THREAD ENDED =====")

    def set_resource_limits(self):
        """Set memory and CPU resource limits for the execution"""
        # NOTE: Resource limits in threads affect the entire process
        # For true isolation, we'd need to use subprocess or containers
        # For now, we'll rely on:
        # 1. 3-second timeout (wall clock time)
        # 2. Output rate limiting (prevents memory exhaustion from output)
        # 3. Total output limiting (10,000 lines max)

        # Log that resource limits are enforced through other mechanisms
        print(f"[RESOURCE-LIMITS] Using timeout (3s) and output limits for resource protection")
        # In production, consider using Docker containers with memory limits
        # or subprocess with ulimit for true process isolation

    def repl_input(self, prompt=""):
        """Custom input function for use in scripts and REPL"""
        if prompt:
            self.send_message(MessageType.INPUT_REQUEST, prompt)

        self.waiting_for_input = True
        try:
            # Wait for input from WebSocket
            input_value = self.input_queue.get(timeout=300)
            self.waiting_for_input = False

            # Don't echo the input - the user already sees it in the input field
            # self.send_message(MessageType.STDOUT, input_value + "\n")
            # Standard Python input() doesn't echo either
            return input_value

        except Empty:
            self.waiting_for_input = False
            raise EOFError("No input received")

    def execute_script(self):
        """Execute the script file with strict 3-second timeout"""
        # print(f"[SimpleExecutorV3-SCRIPT] ===== SCRIPT EXECUTION START =====")
        # print(f"[SimpleExecutorV3-SCRIPT] Path: {self.script_path}")
        # print(f"[SimpleExecutorV3-SCRIPT] File exists: {os.path.exists(self.script_path)}")

        self.state = ExecutionState.SCRIPT_RUNNING
        script_start_time = time.time()
        self.timeout_occurred = False  # Flag for timeout

        # Create a trace function for timeout checking
        def trace_function(frame, event, arg):
            """Trace function to interrupt execution on timeout"""
            if self.timeout_occurred or not self.alive:
                raise KeyboardInterrupt("Script terminated by timeout")
            return trace_function

        # Set up a timer to kill script after 3 seconds
        def timeout_killer():
            time.sleep(3.0)  # Wait exactly 3 seconds
            if self.state == ExecutionState.SCRIPT_RUNNING and not self.waiting_for_input:
                elapsed = time.time() - script_start_time
                print(f"[SCRIPT-TIMEOUT] Script exceeded 3-second limit (elapsed: {elapsed:.2f}s)")

                # Kill the script
                self._kill_for_timeout("Script execution time limit exceeded (3 seconds)")

        # Start the timeout thread
        timeout_thread = threading.Thread(target=timeout_killer, daemon=True)
        timeout_thread.start()
        # print(f"[SimpleExecutorV3-SCRIPT] Started 3-second timeout monitor")

        try:
            # Read script content
            with open(self.script_path, 'r') as f:
                script_code = f.read()

            # print(f"[SimpleExecutorV3-SCRIPT] Script size: {len(script_code)} bytes")
            # print(f"[SimpleExecutorV3-SCRIPT] First 100 chars: {script_code[:100]}")

            # Compile and execute in namespace
            compiled_code = compile(script_code, self.script_path, 'exec')

            # Capture stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            try:
                sys.stdout = stdout_buffer
                sys.stderr = stderr_buffer

                # Set trace function for timeout checking
                sys.settrace(trace_function)

                try:
                    # Execute the script (trace function will interrupt if timeout)
                    exec(compiled_code, self.namespace)
                finally:
                    # Always clear trace function
                    sys.settrace(None)

                # Script completed successfully - mark as SCRIPT_COMPLETE
                self.state = ExecutionState.SCRIPT_COMPLETE
                elapsed = time.time() - script_start_time
                # print(f"[SimpleExecutorV3-SCRIPT] Script completed in {elapsed:.2f} seconds")

                # Send any output
                stdout_text = stdout_buffer.getvalue()
                stderr_text = stderr_buffer.getvalue()

                if stdout_text:
                    self.send_message(MessageType.STDOUT, stdout_text)
                if stderr_text:
                    self.send_message(MessageType.STDERR, stderr_text)

                # Report variables loaded (disabled for cleaner output)
                # user_vars = [k for k in self.namespace.keys()
                #             if not k.startswith('_') and k != 'input']
                # if user_vars:
                #     var_msg = f"\n🎯 Script variables loaded into REPL: {', '.join(user_vars)}\n"
                #     self.send_message(MessageType.STDOUT, var_msg)
                #     print(f"[SimpleExecutorV3-SCRIPT] Variables loaded: {user_vars}")

                # print(f"[SimpleExecutorV3-SCRIPT] Script executed successfully in {elapsed:.2f}s")

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        except KeyboardInterrupt:
            # This is from our timeout killer
            print(f"[SimpleExecutorV3-SCRIPT] Script interrupted by timeout")
            # The error message was already sent by _kill_for_timeout
            self.alive = False
            self.state = ExecutionState.TERMINATED
            # Don't start REPL after timeout
            return

        except Exception as e:
            print(f"[SimpleExecutorV3-SCRIPT] ERROR: Script execution failed")
            print(f"[SimpleExecutorV3-SCRIPT] Exception: {e}")
            traceback.print_exc()

            # Only send error if not already terminated
            if self.state != ExecutionState.TERMINATED:
                self.send_message(MessageType.ERROR, {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })

            # Mark as not alive to prevent REPL from starting
            self.alive = False
            print(f"[SimpleExecutorV3-SCRIPT] Set alive=False due to error")
            # Don't start REPL if script had errors
            raise

        finally:
            # print(f"[SimpleExecutorV3-SCRIPT] ===== SCRIPT EXECUTION END =====")
            pass  # Keep the block valid even with commented prints

    def start_repl(self):
        """Start the interactive REPL"""
        # print(f"[SimpleExecutorV3-REPL] ===== REPL START =====")
        # print(f"[SimpleExecutorV3-REPL] alive: {self.alive}, state: {self.state}")

        if not self.alive:
            print(f"[SimpleExecutorV3-REPL] Not starting REPL (alive=False)")
            return

        self.state = ExecutionState.REPL_ACTIVE

        # Create custom console
        self.console = InteractiveREPLConsole(self.namespace, self)
        # print(f"[SimpleExecutorV3-REPL] Console created")

        # Send REPL ready message
        self.send_message(MessageType.REPL_READY, {"prompt": ">>>"})
        # print(f"[SimpleExecutorV3-REPL] REPL ready message sent")

        # REPL loop
        iteration = 0
        while self.alive and self.state == ExecutionState.REPL_ACTIVE and not self._stop_event.is_set():
            # Check for timeout
            if time.time() - self.last_activity > self.repl_timeout:
                print(f"[SimpleExecutorV3] REPL timeout")
                self.send_message(MessageType.STDOUT, "\n⏰ REPL session timed out\n")
                break

            # Check every 10 iterations for debugging
            if iteration % 10 == 0:
                # print(f"[SimpleExecutorV3-REPL] Loop iteration {iteration}, alive: {self.alive}, stop_event: {self._stop_event.is_set()}")
                pass  # Keep the block valid even with commented prints

            iteration += 1

            # Wait for input
            if not self.waiting_for_input:
                try:
                    # Get command from queue
                    command = self.input_queue.get(timeout=0.1)
                    self.last_activity = time.time()

                    # print(f"[SimpleExecutorV3-REPL] Received command: {command[:50]}...")

                    # Handle special commands
                    if command.strip() in ['exit()', 'quit()', 'exit', 'quit']:
                        # print(f"[SimpleExecutorV3-REPL] Exit command received")
                        self.send_message(MessageType.STDOUT, "\nGoodbye!\n")
                        break

                    # Execute in console
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    stdout_buffer = io.StringIO()
                    stderr_buffer = io.StringIO()

                    try:
                        sys.stdout = stdout_buffer
                        sys.stderr = stderr_buffer

                        # Push line to console
                        more_input_needed = self.console.push(command)

                        # Get output
                        stdout_text = stdout_buffer.getvalue()
                        stderr_text = stderr_buffer.getvalue()

                        if stdout_text:
                            self.send_message(MessageType.STDOUT, stdout_text)
                        if stderr_text:
                            self.send_message(MessageType.STDERR, stderr_text)

                        # Send appropriate prompt
                        if more_input_needed:
                            self.send_message(MessageType.STDOUT, "... ")
                        else:
                            self.console.resetbuffer()
                            self.send_message(MessageType.STDOUT, ">>> ")

                    finally:
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr

                except Empty:
                    # No input available, continue waiting
                    continue
                except Exception as e:
                    print(f"[SimpleExecutorV3] REPL error: {e}")
                    self.send_message(MessageType.ERROR, {
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    })
                    self.send_message(MessageType.STDOUT, ">>> ")
            else:
                # Waiting for input() response
                time.sleep(0.1)

        print(f"[SimpleExecutorV3-REPL] ===== REPL END =====")

    def stop(self):
        """Stop the executor - CRITICAL for preventing frozen state"""
        print(f"[SimpleExecutorV3-STOP] ===== STOP REQUESTED =====")
        print(f"[SimpleExecutorV3-STOP] cmd_id: {self.cmd_id}")
        print(f"[SimpleExecutorV3-STOP] Current state: {self.state}")
        print(f"[SimpleExecutorV3-STOP] Thread alive: {self.is_alive()}")
        print(f"[SimpleExecutorV3-STOP] self.alive: {self.alive}")

        # Set flags to stop execution
        self.alive = False
        self.state = ExecutionState.TERMINATED
        self._stop_event.set()

        # For script running, mark timeout to interrupt trace function
        if self.state == ExecutionState.SCRIPT_RUNNING:
            self.timeout_occurred = True

        # Release execution lock if not already released (only relevant for scripts stopped mid-execution)
        if not self._lock_released and hasattr(self, 'username') and hasattr(self, 'script_path') and self.username and self.script_path:
            try:
                from .execution_lock_manager import execution_lock_manager
                execution_lock_manager.release_execution_lock(self.username, self.script_path, self.cmd_id)
                self._lock_released = True  # Mark lock as released
                print(f"[SimpleExecutorV3-STOP] ✅ Lock released for {self.username}:{os.path.basename(self.script_path)}:{self.cmd_id}")
            except Exception as e:
                print(f"[SimpleExecutorV3-STOP] ⚠️ Error releasing lock: {e}")

        # Wake up any waiting input
        if self.waiting_for_input:
            print(f"[SimpleExecutorV3-STOP] Interrupting input wait")
            self.input_queue.put("")  # Send empty input to unblock

        # Clear input queue
        cleared_count = 0
        while not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
                cleared_count += 1
            except Empty:
                break

        if cleared_count > 0:
            print(f"[SimpleExecutorV3-STOP] Cleared {cleared_count} items from input queue")

        # If in REPL mode, try to interrupt the console
        if self.console and self.state in (ExecutionState.REPL_RUNNING, ExecutionState.REPL_READY):
            print(f"[SimpleExecutorV3-STOP] Attempting to stop REPL console")
            # The console will check self.alive in its push() method

        print(f"[SimpleExecutorV3-STOP] Stop completed")

    def _check_infinite_loop(self, output_text: str):
        """
        Check for infinite loop patterns in output
        Implements 3 layers of protection
        """
        if not output_text or not self.alive:
            return

        lines = output_text.split('\n')
        line_count = len(lines)

        # Update counters
        self.output_line_count += line_count
        self.total_output_lines += line_count

        # Layer 1: Output Rate Limiting (100 lines/sec)
        current_time = time.time()
        elapsed_since_start = current_time - self.output_start_time

        # Check rate every 0.5 seconds to avoid too frequent checks
        if current_time - self.last_rate_check >= 0.5 and elapsed_since_start > 0.1:
            rate = self.output_line_count / elapsed_since_start

            if rate > self.MAX_LINES_PER_SECOND:
                print(f"[INFINITE-LOOP] RATE LIMIT EXCEEDED: {rate:.1f} lines/sec > {self.MAX_LINES_PER_SECOND}")
                self._kill_for_infinite_loop(
                    f"Output rate limit exceeded: {rate:.1f} lines/sec (limit: {self.MAX_LINES_PER_SECOND}/sec)"
                )
                return

            self.last_rate_check = current_time

            # Log rate for debugging (only when high)
            if rate > 50:
                # print(f"[INFINITE-LOOP] High output rate: {rate:.1f} lines/sec")
                pass  # Keep the block valid even with commented prints

        # Layer 2: Total Output Limit (10,000 lines)
        if self.total_output_lines > self.MAX_TOTAL_LINES:
            print(f"[INFINITE-LOOP] TOTAL LIMIT EXCEEDED: {self.total_output_lines} > {self.MAX_TOTAL_LINES}")
            self._kill_for_infinite_loop(
                f"Total output limit exceeded: {self.total_output_lines} lines (limit: {self.MAX_TOTAL_LINES})"
            )
            return

        # Layer 3: Identical Line Detection (500x repeats)
        for line in lines:
            if not line.strip():  # Skip empty lines
                continue

            if line == self.last_output_line:
                self.identical_line_count += 1

                if self.identical_line_count >= self.MAX_IDENTICAL_LINES:
                    print(f"[INFINITE-LOOP] IDENTICAL LINES: '{line[:50]}...' repeated {self.identical_line_count} times")
                    self._kill_for_infinite_loop(
                        f"Identical line repeated {self.identical_line_count} times: '{line[:100]}...'"
                    )
                    return

                # Log when getting close to limit
                if self.identical_line_count > 0 and self.identical_line_count % 100 == 0:
                    # print(f"[INFINITE-LOOP] Warning: '{line[:30]}...' repeated {self.identical_line_count} times")
                    pass  # Keep the block valid even with commented prints
            else:
                # Reset counter when line changes
                self.last_output_line = line
                self.identical_line_count = 1

        # Layer 4: Fast Flood Detection (catches immediate bursts)
        # If we get > 4KB of data with > 50 lines in < 0.5 seconds, it's likely spam
        if len(output_text) >= 4000 and line_count >= 50:
            flood_elapsed = current_time - self.flood_check_time
            if flood_elapsed < 0.5:
                print(f"[INFINITE-LOOP] FLOOD DETECTED: {len(output_text)} bytes, {line_count} lines in {flood_elapsed:.2f}s")
                self._kill_for_infinite_loop(
                    f"Flood detected: {line_count} lines in {flood_elapsed:.2f} seconds"
                )
                return
            # Reset flood check timer after 0.5 seconds
            self.flood_check_time = current_time

    def _kill_for_infinite_loop(self, reason: str):
        """Kill the process due to detected infinite loop"""
        print(f"[INFINITE-LOOP-KILL] Terminating process: {reason}")

        # Send error message to user
        error_msg = f"\n⚠️ PROCESS TERMINATED: Infinite loop detected!\n"
        error_msg += f"Reason: {reason}\n"
        error_msg += f"\nCommon causes:\n"
        error_msg += f"  • while True: without break condition\n"
        error_msg += f"  • for loop with excessive iterations\n"
        error_msg += f"  • Recursive function without base case\n"
        error_msg += f"\nPlease review your code and add proper loop termination conditions.\n"

        # Send error to console
        self.send_message(MessageType.ERROR, {
            "error": "Infinite loop detected",
            "traceback": error_msg
        })

        # Force stop
        self.alive = False
        self.state = ExecutionState.TERMINATED
        self._stop_event.set()

        # If in REPL, exit it
        if self.console:
            try:
                # Send interrupt to break out of any running code
                os.kill(os.getpid(), signal.SIGINT)
            except:
                pass

    def _kill_for_timeout(self, reason: str):
        """Kill the script due to timeout (3-second limit)"""
        print(f"[TIMEOUT-KILL] Terminating script: {reason}")

        # Send error message to user
        error_msg = f"\n⏰ SCRIPT TERMINATED: Time limit exceeded!\n"
        # error_msg += f"Reason: {reason}\n"
        # error_msg += f"\nScript execution is limited to 3 seconds.\n"
        # error_msg += f"\nPossible issues:\n"
        # error_msg += f"  • Infinite loop (while True, endless for loop)\n"
        # error_msg += f"  • Very large data processing\n"
        # error_msg += f"  • Recursive function without proper termination\n"
        # error_msg += f"  • Memory-intensive operations (creating huge lists)\n"
        # error_msg += f"\nTip: Use smaller data sets or add loop limits for testing.\n"

        # Send error to console
        self.send_message(MessageType.ERROR, {
            "error": "Script timeout (3 seconds)",
            "traceback": error_msg
        })

        # Force stop the script
        self.alive = False
        self.state = ExecutionState.TERMINATED
        self._stop_event.set()

        # Mark timeout occurred
        self.timeout_occurred = True

    def cleanup(self):
        """Clean up resources - CRITICAL for preventing zombie threads"""
        # print(f"[SimpleExecutorV3-CLEANUP] Starting cleanup")
        # print(f"[SimpleExecutorV3-CLEANUP] cmd_id: {self.cmd_id}")
        # print(f"[SimpleExecutorV3-CLEANUP] cleanup_done: {self._cleanup_done}")

        # Prevent double cleanup
        if self._cleanup_done:
            # print(f"[SimpleExecutorV3-CLEANUP] Already cleaned up, skipping")
            return

        self._cleanup_done = True

        # Send completion message if still connected
        if self.alive and self.client:
            duration = time.time() - self.start_time if self.start_time else 0
            # print(f"[SimpleExecutorV3-CLEANUP] Sending completion message, duration: {duration:.2f}s")
            self.send_message(MessageType.COMPLETE, {
                "exit_code": 0,
                "duration": duration
            })

        # Final state update
        self.alive = False
        self.state = ExecutionState.TERMINATED
        self._stop_event.set()

        # Release any execution locks (if not already released)
        if not self._lock_released and hasattr(self, 'username') and hasattr(self, 'script_path') and self.username and self.script_path:
            try:
                from .execution_lock_manager import execution_lock_manager
                execution_lock_manager.release_execution_lock(self.username, self.script_path, self.cmd_id)
                self._lock_released = True  # Mark lock as released
                # print(f"[SimpleExecutorV3-CLEANUP] Released execution lock")
            except Exception as e:
                # print(f"[SimpleExecutorV3-CLEANUP] Error releasing lock: {e}")
                pass  # Keep the block valid even with commented prints

        # print(f"[SimpleExecutorV3-CLEANUP] Cleanup completed")