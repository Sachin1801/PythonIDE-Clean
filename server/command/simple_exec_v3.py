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
            # Send to WebSocket
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

            # Echo the input back
            self.executor.send_message(MessageType.STDOUT, input_value + "\n")
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

        print(f"[SimpleExecutorV3-INIT] Thread ID: {threading.get_ident()}")
        print(f"[SimpleExecutorV3-INIT] cmd_id: {cmd_id}, script: {script_path}")
        print(f"[SimpleExecutorV3-INIT] username: {username}")
        print(f"[SimpleExecutorV3-INIT] alive: {self.alive}, state: {self.state}")

    def send_message(self, msg_type: MessageType, data: Any):
        """Send message to frontend via WebSocket"""
        # CRITICAL: Check if we're still alive before sending
        if not self.alive:
            print(f"[SimpleExecutorV3-SEND] WARNING: Attempt to send message after executor stopped")
            print(f"[SimpleExecutorV3-SEND] cmd_id: {self.cmd_id}, msg_type: {msg_type}, alive: {self.alive}")
            return

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
            print(f"[SimpleExecutorV3-SEND] Sent {msg_type.value}: {data_preview}")

    def handle_input(self, text: str):
        """Handle input from WebSocket"""
        print(f"[SimpleExecutorV3] Received input: {text}")
        self.input_queue.put(text)

    def send_input(self, text: str):
        """Alias for handle_input to match expected interface"""
        return self.handle_input(text)

    def run(self):
        """Main execution thread"""
        print(f"[SimpleExecutorV3-RUN] ===== THREAD STARTED =====")
        print(f"[SimpleExecutorV3-RUN] Thread ID: {threading.get_ident()}")
        print(f"[SimpleExecutorV3-RUN] cmd_id: {self.cmd_id}")
        print(f"[SimpleExecutorV3-RUN] script_path: {self.script_path}")
        print(f"[SimpleExecutorV3-RUN] alive: {self.alive}, state: {self.state}")

        self.start_time = time.time()

        try:
            # Create namespace for execution
            self.namespace = {
                '__name__': '__main__',
                '__doc__': None,
                'input': self.repl_input  # Custom input function
            }
            print(f"[SimpleExecutorV3-RUN] Namespace created")

            # Execute script if provided
            if self.script_path:
                print(f"[SimpleExecutorV3-RUN] Executing script: {self.script_path}")
                self.execute_script()
            else:
                print(f"[SimpleExecutorV3-RUN] No script provided, starting REPL directly")

            # Start REPL (whether script was run or not)
            if self.alive:  # Only start REPL if still alive
                print(f"[SimpleExecutorV3-RUN] Starting REPL mode")
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
            print(f"[SimpleExecutorV3-RUN] Entering cleanup phase")
            self.cleanup()
            print(f"[SimpleExecutorV3-RUN] ===== THREAD ENDED =====")

    def repl_input(self, prompt=""):
        """Custom input function for use in scripts and REPL"""
        if prompt:
            self.send_message(MessageType.INPUT_REQUEST, prompt)

        self.waiting_for_input = True
        try:
            # Wait for input from WebSocket
            input_value = self.input_queue.get(timeout=300)
            self.waiting_for_input = False

            # Echo the input
            self.send_message(MessageType.STDOUT, input_value + "\n")
            return input_value

        except Empty:
            self.waiting_for_input = False
            raise EOFError("No input received")

    def execute_script(self):
        """Execute the script file"""
        print(f"[SimpleExecutorV3-SCRIPT] ===== SCRIPT EXECUTION START =====")
        print(f"[SimpleExecutorV3-SCRIPT] Path: {self.script_path}")
        print(f"[SimpleExecutorV3-SCRIPT] File exists: {os.path.exists(self.script_path)}")

        self.state = ExecutionState.SCRIPT_RUNNING

        try:
            # Read script content
            with open(self.script_path, 'r') as f:
                script_code = f.read()

            print(f"[SimpleExecutorV3-SCRIPT] Script size: {len(script_code)} bytes")
            print(f"[SimpleExecutorV3-SCRIPT] First 100 chars: {script_code[:100]}")

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

                # Execute the script
                exec(compiled_code, self.namespace)

                # Send any output
                stdout_text = stdout_buffer.getvalue()
                stderr_text = stderr_buffer.getvalue()

                if stdout_text:
                    self.send_message(MessageType.STDOUT, stdout_text)
                if stderr_text:
                    self.send_message(MessageType.STDERR, stderr_text)

                # Report variables loaded
                user_vars = [k for k in self.namespace.keys()
                            if not k.startswith('_') and k != 'input']
                if user_vars:
                    var_msg = f"\n🎯 Script variables loaded into REPL: {', '.join(user_vars)}\n"
                    self.send_message(MessageType.STDOUT, var_msg)
                    print(f"[SimpleExecutorV3-SCRIPT] Variables loaded: {user_vars}")

                print(f"[SimpleExecutorV3-SCRIPT] Script executed successfully")

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        except Exception as e:
            print(f"[SimpleExecutorV3-SCRIPT] ERROR: Script execution failed")
            print(f"[SimpleExecutorV3-SCRIPT] Exception: {e}")
            traceback.print_exc()

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
            print(f"[SimpleExecutorV3-SCRIPT] ===== SCRIPT EXECUTION END =====")

    def start_repl(self):
        """Start the interactive REPL"""
        print(f"[SimpleExecutorV3-REPL] ===== REPL START =====")
        print(f"[SimpleExecutorV3-REPL] alive: {self.alive}, state: {self.state}")

        if not self.alive:
            print(f"[SimpleExecutorV3-REPL] Not starting REPL (alive=False)")
            return

        self.state = ExecutionState.REPL_ACTIVE

        # Create custom console
        self.console = InteractiveREPLConsole(self.namespace, self)
        print(f"[SimpleExecutorV3-REPL] Console created")

        # Send REPL ready message
        self.send_message(MessageType.REPL_READY, {"prompt": ">>>"})
        print(f"[SimpleExecutorV3-REPL] REPL ready message sent")

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
                print(f"[SimpleExecutorV3-REPL] Loop iteration {iteration}, alive: {self.alive}, stop_event: {self._stop_event.is_set()}")

            iteration += 1

            # Wait for input
            if not self.waiting_for_input:
                try:
                    # Get command from queue
                    command = self.input_queue.get(timeout=0.1)
                    self.last_activity = time.time()

                    print(f"[SimpleExecutorV3-REPL] Received command: {command[:50]}...")

                    # Handle special commands
                    if command.strip() in ['exit()', 'quit()', 'exit', 'quit']:
                        print(f"[SimpleExecutorV3-REPL] Exit command received")
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

        print(f"[SimpleExecutorV3-STOP] Stop completed")

    def cleanup(self):
        """Clean up resources - CRITICAL for preventing zombie threads"""
        print(f"[SimpleExecutorV3-CLEANUP] Starting cleanup")
        print(f"[SimpleExecutorV3-CLEANUP] cmd_id: {self.cmd_id}")
        print(f"[SimpleExecutorV3-CLEANUP] cleanup_done: {self._cleanup_done}")

        # Prevent double cleanup
        if self._cleanup_done:
            print(f"[SimpleExecutorV3-CLEANUP] Already cleaned up, skipping")
            return

        self._cleanup_done = True

        # Send completion message if still connected
        if self.alive and self.client:
            duration = time.time() - self.start_time if self.start_time else 0
            print(f"[SimpleExecutorV3-CLEANUP] Sending completion message, duration: {duration:.2f}s")
            self.send_message(MessageType.COMPLETE, {
                "exit_code": 0,
                "duration": duration
            })

        # Final state update
        self.alive = False
        self.state = ExecutionState.TERMINATED
        self._stop_event.set()

        # Release any execution locks
        if hasattr(self, 'username') and hasattr(self, 'script_path') and self.username and self.script_path:
            try:
                from .execution_lock_manager import execution_lock_manager
                execution_lock_manager.release_execution_lock(self.username, self.script_path, self.cmd_id)
                print(f"[SimpleExecutorV3-CLEANUP] Released execution lock")
            except Exception as e:
                print(f"[SimpleExecutorV3-CLEANUP] Error releasing lock: {e}")

        print(f"[SimpleExecutorV3-CLEANUP] Cleanup completed")