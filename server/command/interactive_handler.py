#!/usr/bin/env python3
"""
Interactive Input and Output Handler for Python Web IDE
Handles user input requests and special outputs like matplotlib graphs
"""

import os
import re
import json
import base64
import asyncio
import threading
import subprocess
from io import BytesIO
from typing import Optional, Dict, Any
from queue import Queue, Empty
import time


class InteractiveHandler:
    """Manages interactive I/O for Python programs"""

    def __init__(self):
        self.input_queue = Queue()
        self.waiting_for_input = False
        self.current_prompt = ""
        self.process = None
        self.client = None
        self.cmd_id = None

    def set_process(self, process: subprocess.Popen):
        """Set the subprocess to handle"""
        self.process = process

    def set_client_info(self, client, cmd_id):
        """Set client and command ID for responses"""
        self.client = client
        self.cmd_id = cmd_id

    def request_user_input(self, prompt: str):
        """Send input request to frontend"""
        self.waiting_for_input = True
        self.current_prompt = prompt

        # Send WebSocket message to frontend requesting input
        if self.client:
            asyncio.create_task(self._send_input_request(prompt))

    async def _send_input_request(self, prompt: str):
        """Send input request via WebSocket"""
        from .response import response

        await response(
            self.client,
            self.cmd_id,
            2000,  # Special code for input request
            {"type": "input_request", "prompt": prompt, "waiting": True},
        )

    def provide_input(self, user_input: str):
        """Receive input from frontend and forward to process"""
        if self.waiting_for_input and self.process:
            try:
                # Write to process stdin
                self.process.stdin.write(user_input + "\n")
                self.process.stdin.flush()
                self.waiting_for_input = False
                return True
            except Exception as e:
                print(f"Error providing input: {e}")
                return False
        return False

    def handle_matplotlib_output(self, figure_data: bytes) -> Dict[str, Any]:
        """Convert matplotlib figure to base64 for frontend display"""
        try:
            # Convert bytes to base64
            encoded = base64.b64encode(figure_data).decode("utf-8")
            return {"type": "matplotlib_figure", "data": f"data:image/png;base64,{encoded}", "timestamp": time.time()}
        except Exception as e:
            print(f"Error handling matplotlib output: {e}")
            return None


class EnhancedSubProgramThread(threading.Thread):
    """Enhanced thread for running Python programs with interactive I/O"""

    def __init__(self, cmd, cmd_id, client, event_loop):
        super().__init__()
        self.cmd = cmd
        self.cmd_id = cmd_id
        self.client = client
        self.alive = True
        self.daemon = True
        self.event_loop = event_loop
        self.p = None
        self.interactive_handler = InteractiveHandler()
        self.output_buffer = []
        self.matplotlib_mode = False

    def stop(self):
        """Stop the running program"""
        self.alive = False
        if self.p:
            try:
                self.p.terminate()
                self.p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.p.kill()
            except:
                pass
            self.p = None

    def send_input(self, user_input: str):
        """Send user input to the running program"""
        if self.p and self.p.stdin:
            try:
                self.p.stdin.write(user_input + "\n")
                self.p.stdin.flush()
                return True
            except:
                return False
        return False

    async def response_to_client(self, code, data):
        """Send response to client via WebSocket"""
        from .response import response

        await response(self.client, self.cmd_id, code, data)

    def detect_input_request(self, output: str) -> Optional[str]:
        """Detect if program is waiting for input"""
        # Common input patterns
        input_patterns = [
            r'input\(["\'](.+?)["\']\)',  # input("prompt")
            r"Enter .+?:",  # Enter something:
            r"Please .+?:",  # Please enter:
            r"Type .+?:",  # Type something:
            r".+?\?$",  # Question mark at end
            r">>>\s*$",  # Python prompt
            r":\s*$",  # Colon at end
        ]

        for pattern in input_patterns:
            if re.search(pattern, output.strip()):
                return output.strip()
        return None

    def setup_matplotlib_backend(self):
        """Configure matplotlib for non-interactive backend"""
        matplotlib_setup = """
import sys
import os
os.environ['MPLBACKEND'] = 'Agg'

# Monkey-patch matplotlib to capture figures
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO
    import base64
    
    _original_show = plt.show
    
    def _capture_show(*args, **kwargs):
        # Save current figure to bytes
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Send to IDE
        print(f"__MATPLOTLIB_FIGURE_START__")
        print(base64.b64encode(buf.read()).decode('utf-8'))
        print(f"__MATPLOTLIB_FIGURE_END__")
        
        # Clear the figure
        plt.clf()
        buf.close()
    
    plt.show = _capture_show
except ImportError:
    pass  # matplotlib not installed
"""
        return matplotlib_setup

    def run_interactive_program(self):
        """Run Python program with interactive I/O support"""
        start_time = time.time()
        asyncio.set_event_loop(self.event_loop)

        print(f"[{self.client.id}-Program {self.cmd_id} starting with interactive I/O]")

        try:
            # Modify command to include matplotlib setup
            python_cmd = self.cmd[0]  # Should be python executable
            script_path = self.cmd[-1]  # Should be script path

            # Create wrapper script with matplotlib support
            wrapper_code = self.setup_matplotlib_backend()

            # Read original script
            with open(script_path, "r") as f:
                user_code = f.read()

            # Combine wrapper and user code
            full_code = wrapper_code + "\n\n# User code starts here\n" + user_code

            # Create process with stdin, stdout, stderr pipes
            self.p = subprocess.Popen(
                [python_cmd, "-u", "-c", full_code],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=0,  # Unbuffered
            )

            # Set up interactive handler
            self.interactive_handler.set_process(self.p)
            self.interactive_handler.set_client_info(self.client, self.cmd_id)

            # Create queues for stdout and stderr
            from queue import Queue, Empty
            from threading import Thread

            q_out = Queue()
            q_err = Queue()

            def reader(pipe, queue):
                """Read from pipe and put in queue"""
                try:
                    for line in iter(pipe.readline, ""):
                        if line:
                            queue.put(line.rstrip())
                finally:
                    pipe.close()

            # Start reader threads
            t_out = Thread(target=reader, args=(self.p.stdout, q_out))
            t_err = Thread(target=reader, args=(self.p.stderr, q_err))
            t_out.daemon = True
            t_err.daemon = True
            t_out.start()
            t_err.start()

            # Main loop
            input_buffer = ""
            waiting_for_input = False

            while self.alive and self.p.poll() is None:
                if not self.client.connected:
                    self.alive = False
                    self.p.kill()
                    print(f"[{self.client.id}-Program {self.cmd_id} killed - client disconnected]")
                    return

                # Check for output
                try:
                    output = q_out.get(timeout=0.1)

                    # Check for matplotlib figure
                    if "__MATPLOTLIB_FIGURE_START__" in output:
                        # Capture matplotlib figure data
                        figure_data = []
                        while True:
                            line = q_out.get(timeout=1)
                            if "__MATPLOTLIB_FIGURE_END__" in line:
                                break
                            figure_data.append(line)

                        # Send figure to client
                        if figure_data:
                            figure_base64 = "".join(figure_data)
                            asyncio.run_coroutine_threadsafe(
                                self.response_to_client(
                                    3000,
                                    {  # Special code for matplotlib
                                        "type": "matplotlib_figure",
                                        "data": f"data:image/png;base64,{figure_base64}",
                                    },
                                ),
                                self.event_loop,
                            )
                    else:
                        # Regular output
                        input_buffer += output + "\n"

                        # Check if waiting for input
                        if not waiting_for_input:
                            prompt = self.detect_input_request(output)
                            if prompt:
                                waiting_for_input = True
                                # Send accumulated output first
                                if input_buffer.strip():
                                    asyncio.run_coroutine_threadsafe(
                                        self.response_to_client(0, {"stdout": input_buffer.rstrip()}), self.event_loop
                                    )
                                    input_buffer = ""

                                # Request input from user
                                asyncio.run_coroutine_threadsafe(
                                    self.response_to_client(
                                        2000, {"type": "input_request", "prompt": prompt}  # Input request code
                                    ),
                                    self.event_loop,
                                )
                        else:
                            # Send output immediately
                            asyncio.run_coroutine_threadsafe(
                                self.response_to_client(0, {"stdout": output}), self.event_loop
                            )

                except Empty:
                    pass

                # Check for errors
                try:
                    error = q_err.get_nowait()
                    asyncio.run_coroutine_threadsafe(self.response_to_client(1, {"stderr": error}), self.event_loop)
                except Empty:
                    pass

                # Send buffered output if no input requested
                if not waiting_for_input and input_buffer and len(input_buffer) > 100:
                    asyncio.run_coroutine_threadsafe(
                        self.response_to_client(0, {"stdout": input_buffer.rstrip()}), self.event_loop
                    )
                    input_buffer = ""

            # Send any remaining output
            if input_buffer:
                asyncio.run_coroutine_threadsafe(
                    self.response_to_client(0, {"stdout": input_buffer.rstrip()}), self.event_loop
                )

            # Get remaining output
            while not q_out.empty():
                try:
                    output = q_out.get_nowait()
                    asyncio.run_coroutine_threadsafe(self.response_to_client(0, {"stdout": output}), self.event_loop)
                except Empty:
                    break

            # Get remaining errors
            while not q_err.empty():
                try:
                    error = q_err.get_nowait()
                    asyncio.run_coroutine_threadsafe(self.response_to_client(1, {"stderr": error}), self.event_loop)
                except Empty:
                    break

            # Send completion message
            exit_code = self.p.returncode if self.p else -1
            completion_msg = f"[Finished in {time.time() - start_time:.2f}s with exit code {exit_code}]"

            asyncio.run_coroutine_threadsafe(self.response_to_client(1111, {"stdout": completion_msg}), self.event_loop)

            print(f"{self.client.id}-Program {self.cmd_id} completed with code {exit_code}")

        except Exception as e:
            print(f"[{self.client.id}-Program {self.cmd_id} exception]: {e}")
            asyncio.run_coroutine_threadsafe(
                self.response_to_client(1111, {"stdout": f"[Program exception]: {e}"}), self.event_loop
            )
        finally:
            if self.p:
                try:
                    self.p.kill()
                except:
                    pass
            self.alive = False

    def run(self):
        """Main thread run method"""
        self.alive = True
        try:
            self.run_interactive_program()
        except Exception as e:
            print(f"Thread exception: {e}")
        self.alive = False
