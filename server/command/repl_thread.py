#!/usr/bin/env python3
"""
True Python REPL implementation for interactive code execution.
Supports multi-line statements like loops, functions, and classes.
Fixed version with proper output capture using separate reader threads.
"""

import subprocess
import threading
import time
import os
import asyncio
import sys
from queue import Queue, Empty
import json

from common.config import Config
from command.response import response


class OutputReaderThread(threading.Thread):
    """Separate thread for reading subprocess output"""

    def __init__(self, stream, output_queue, stream_name="stdout"):
        super().__init__(daemon=True)
        self.stream = stream
        self.output_queue = output_queue
        self.stream_name = stream_name
        self.running = True

    def run(self):
        """Read output line by line and put in queue"""
        try:
            while self.running:
                line = self.stream.readline()
                if line:
                    self.output_queue.put((self.stream_name, line))
                else:
                    # Stream closed
                    break
        except Exception as e:
            print(f"[OutputReader-{self.stream_name}] Error: {e}")
        finally:
            self.output_queue.put((self.stream_name, None))  # Signal end

    def stop(self):
        self.running = False


class PythonREPLThread(threading.Thread):
    """Python REPL thread for interactive code execution"""

    def __init__(self, cmd_id, client, event_loop):
        super().__init__()
        self.cmd_id = cmd_id
        self.client = client
        self.event_loop = event_loop
        self.alive = True
        self.p = None
        self.input_queue = Queue()
        self.output_queue = Queue()
        self.stdout_reader = None
        self.stderr_reader = None
        self.output_buffer = ""
        self.prompt_received = False

    def kill(self):
        """Kill the REPL session"""
        self.alive = False
        if self.stdout_reader:
            self.stdout_reader.stop()
        if self.stderr_reader:
            self.stderr_reader.stop()
        if self.p:
            try:
                self.p.kill()
            except:
                pass

    def stop(self):
        """Stop the REPL session gracefully"""
        self.alive = False
        if self.stdout_reader:
            self.stdout_reader.stop()
        if self.stderr_reader:
            self.stderr_reader.stop()
        if self.p:
            try:
                self.p.terminate()
                self.p.wait(timeout=2)
            except:
                try:
                    self.p.kill()
                except:
                    pass

    def send_input(self, user_input):
        """Queue user input to be processed"""
        self.input_queue.put(user_input)
        return True

    def response_to_client(self, code, data):
        """Send response to client via WebSocket"""
        if data:
            # Create the message with proper structure
            msg = {"type": "response", "id": self.cmd_id, "code": code, "data": data}  # Use the REPL session ID

            # Debug log
            print(f"[REPL-{self.cmd_id}] Sending to client: code={code}, data={data}")

            # Send via asyncio
            asyncio.run_coroutine_threadsafe(self._send_response(msg), self.event_loop)

    async def _send_response(self, msg):
        """Async helper to send response"""
        from common.msg import res_put, ResponseItem

        item = ResponseItem(self.client, msg)
        await res_put(self.client, msg)

    def run_repl(self):
        """Run the Python REPL with improved output capture"""
        asyncio.set_event_loop(self.event_loop)

        print(f"[REPL-{self.cmd_id}] Starting Python REPL session")

        try:
            # Start Python subprocess with unbuffered output
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            self.p = subprocess.Popen(
                [Config.PYTHON, "-u", "-i", "-q"],  # -q for quiet (no banner)
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=0,  # Unbuffered
                env=env,
            )

            print(f"[REPL-{self.cmd_id}] Python subprocess started, PID={self.p.pid}")

            # Start output reader threads
            self.stdout_reader = OutputReaderThread(self.p.stdout, self.output_queue, "stdout")
            self.stderr_reader = OutputReaderThread(self.p.stderr, self.output_queue, "stderr")
            self.stdout_reader.start()
            self.stderr_reader.start()

            # Send initial prompt
            time.sleep(0.1)  # Give Python a moment to start
            self.response_to_client(0, {"stdout": "Python REPL Ready\n"})
            self.response_to_client(0, {"stdout": ">>> "})

            # Main loop
            while self.alive and self.p.poll() is None:
                # Check client connection
                if not self.client.connected:
                    print(f"[REPL-{self.cmd_id}] Client disconnected")
                    self.alive = False
                    break

                # Process user input
                try:
                    user_input = self.input_queue.get(timeout=0.01)
                    print(f"[REPL-{self.cmd_id}] Got user input: {repr(user_input)}")

                    # Write to subprocess
                    self.p.stdin.write(user_input + "\n")
                    self.p.stdin.flush()

                    # Small delay to let Python process
                    time.sleep(0.05)

                except Empty:
                    pass

                # Process output from subprocess
                try:
                    while True:
                        stream_name, line = self.output_queue.get_nowait()

                        if line is None:
                            # Stream closed
                            print(f"[REPL-{self.cmd_id}] {stream_name} closed")
                            if stream_name == "stdout":
                                self.alive = False
                            continue

                        print(f"[REPL-{self.cmd_id}] Got {stream_name}: {repr(line)}")

                        # Buffer the line
                        self.output_buffer += line

                        # Check if we have a complete output with prompt
                        if self.output_buffer.endswith(">>> ") or self.output_buffer.endswith("... "):
                            # Extract prompt
                            if self.output_buffer.endswith(">>> "):
                                prompt = ">>> "
                            else:
                                prompt = "... "

                            # Send output without prompt
                            output = self.output_buffer[:-4]
                            if output:
                                # Send output line by line for better display
                                lines = output.split("\n")
                                for i, out_line in enumerate(lines):
                                    if out_line or i < len(lines) - 1:  # Send non-empty lines or newlines
                                        self.response_to_client(
                                            0, {"stdout": out_line + ("\n" if i < len(lines) - 1 else "")}
                                        )

                            # Send prompt separately
                            self.response_to_client(0, {"stdout": prompt})

                            # Clear buffer
                            self.output_buffer = ""

                        elif "\n" in self.output_buffer and not (
                            self.output_buffer.endswith(">>> ") or self.output_buffer.endswith("... ")
                        ):
                            # Send complete lines immediately if we have them
                            lines = self.output_buffer.split("\n")
                            for i in range(len(lines) - 1):
                                self.response_to_client(0, {"stdout": lines[i] + "\n"})
                            self.output_buffer = lines[-1]

                except Empty:
                    # No output available
                    pass
                except Exception as e:
                    print(f"[REPL-{self.cmd_id}] Error processing output: {e}")

                # Small sleep to prevent busy loop
                time.sleep(0.01)

            # Send exit message
            self.response_to_client(1111, {"stdout": "\n[REPL session ended]\n"})

        except Exception as e:
            error_msg = f"Error in REPL: {str(e)}"
            print(f"[REPL-{self.cmd_id}] {error_msg}")
            import traceback

            traceback.print_exc()
            self.response_to_client(1111, {"stdout": error_msg + "\n"})

        finally:
            # Cleanup
            if self.stdout_reader:
                self.stdout_reader.stop()
            if self.stderr_reader:
                self.stderr_reader.stop()

            if self.p:
                try:
                    self.p.terminate()
                    self.p.wait(timeout=2)
                except:
                    try:
                        self.p.kill()
                    except:
                        pass

            self.client.handler_info.remove_subprogram(self.cmd_id)
            print(f"[REPL-{self.cmd_id}] Session finished")

    def run(self):
        """Thread entry point"""
        self.run_repl()
