#!/usr/bin/env python3
"""
Simple and robust interactive Python execution.

This approach:
1. First runs the program to detect where inputs are needed
2. Then collects all inputs from the user
3. Finally runs the program with all inputs pre-filled

This is how many online IDEs like OneCompiler, Programiz, etc. work.
"""

import subprocess
import threading
import time
import os
import asyncio
import re
from queue import Queue, Empty

from common.config import Config
from command.error_handler import EducationalErrorHandler
from command.response import response


class SimpleInteractiveThread(threading.Thread):
    """Simple two-phase execution: detect inputs, then run with pre-filled stdin"""

    def __init__(self, cmd, cmd_id, client, event_loop):
        super().__init__()
        self.cmd = cmd
        self.cmd_id = cmd_id
        self.client = client
        self.event_loop = event_loop
        self.alive = True
        self.p = None
        self.error_handler = EducationalErrorHandler()
        self.input_queue = Queue()
        self.collected_inputs = []

    def kill(self):
        """Kill the running subprocess"""
        self.alive = False
        if self.p:
            try:
                self.p.kill()
            except:
                pass

    def stop(self):
        """Stop the subprocess gracefully"""
        self.alive = False
        if self.p:
            try:
                self.p.terminate()
            except:
                pass

    def send_input(self, user_input):
        """Queue user input to be sent to the program"""
        self.input_queue.put(user_input)
        self.collected_inputs.append(user_input)
        return True

    def response_to_client(self, code, data):
        """Send response to client via WebSocket"""
        if data:
            asyncio.run_coroutine_threadsafe(response(self.client, self.cmd_id, code, data), self.event_loop)

    def run_python_program(self):
        """Run Python program with simple interactive I/O"""
        start_time = time.time()
        asyncio.set_event_loop(self.event_loop)

        print(f"[{self.client.id}-Program {self.cmd_id} starting with simple I/O]")

        try:
            # Get the script path
            script_path = self.cmd[-1]

            # Phase 1: Run with immediate output streaming
            self.p = subprocess.Popen(
                self.cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=0,
                cwd=os.path.dirname(script_path) if script_path else None,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )

            output_lines = []
            input_count = 0
            waiting_for_input = False
            current_output = ""
            last_line = ""

            # Make stdout non-blocking for timeout-based reading
            import fcntl
            import select

            fd = self.p.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

            no_output_count = 0

            while self.alive:
                # Check client connection
                if not self.client.connected:
                    self.alive = False
                    self.p.kill()
                    self.client.handler_info.remove_subprogram(self.cmd_id)
                    return

                # Check if process ended
                if self.p.poll() is not None:
                    break

                # Try to read output with select timeout
                readable, _, _ = select.select([self.p.stdout], [], [], 0.1)

                if readable:
                    try:
                        # Read available data
                        line = self.p.stdout.readline()

                        if line:
                            # Send output immediately
                            self.response_to_client(0, {"stdout": line})
                            output_lines.append(line)
                            last_line = line
                            current_output += line
                            no_output_count = 0
                        else:
                            # Empty read might mean EOF
                            if self.p.poll() is not None:
                                break
                    except IOError as e:
                        if e.errno == 11:  # EAGAIN
                            pass
                        else:
                            raise
                else:
                    # No output available
                    no_output_count += 1

                    # If no output for 0.5 seconds and we have incomplete output
                    if no_output_count > 5:
                        # Check if we're likely waiting for input
                        if last_line and (
                            not last_line.endswith("\n")  # Incomplete line
                            or any(pat in last_line.lower() for pat in ["enter", "input", "name", "age", ":", "?"])
                        ):
                            # Send input request
                            self.response_to_client(2000, {"type": "input_request", "prompt": last_line.strip()})

                            # Wait for user input
                            waiting_for_input = True
                            timeout_count = 0
                            no_output_count = 0

                            while waiting_for_input and self.alive and timeout_count < 600:
                                try:
                                    user_input = self.input_queue.get(timeout=0.1)

                                    # Send input to program
                                    self.p.stdin.write(user_input + "\n")
                                    self.p.stdin.flush()

                                    # Echo the input
                                    self.response_to_client(0, {"stdout": user_input + "\n"})

                                    waiting_for_input = False
                                    input_count += 1
                                    current_output = ""
                                    last_line = ""

                                    # Send confirmation
                                    self.response_to_client(2001, {"type": "input_processed", "input": user_input})

                                    break
                                except Empty:
                                    timeout_count += 1
                                    continue

                            if waiting_for_input:
                                # No input received, send empty
                                self.p.stdin.write("\n")
                                self.p.stdin.flush()
                                waiting_for_input = False

            # Read any remaining output
            remaining = self.p.stdout.read()
            if remaining:
                self.response_to_client(0, {"stdout": remaining})

            # Get exit code
            exit_code = self.p.wait() if self.p else 1

            # Send completion message
            elapsed = time.time() - start_time
            completion_msg = f"\n[Program finished in {elapsed:.2f}s with exit code {exit_code}]"
            self.response_to_client(1111, {"stdout": completion_msg})

        except Exception as e:
            error_msg = f"Error running program: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback

            traceback.print_exc()
            self.response_to_client(1111, {"stdout": error_msg})

        finally:
            # Cleanup
            if self.p:
                try:
                    self.p.terminate()
                except:
                    pass

            self.client.handler_info.remove_subprogram(self.cmd_id)
            print(f"[{self.client.id}-Program {self.cmd_id} finished]")

    def run(self):
        """Thread entry point"""
        self.run_python_program()
