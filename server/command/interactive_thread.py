import subprocess
import threading
import time
import os
import sys
import tempfile
import asyncio
from queue import Queue, Empty
import select
import fcntl
import builtins

from common.config import Config
from command.error_handler import EducationalErrorHandler
from command.response import response


class InteractiveSubProgramThread(threading.Thread):
    """Thread for running Python programs with interactive I/O support using streaming output"""

    def __init__(self, cmd, cmd_id, client, event_loop):
        super().__init__()
        self.cmd = cmd
        self.cmd_id = cmd_id
        self.client = client
        self.event_loop = event_loop
        self.alive = True
        self.p = None
        self.error_buffer = []
        self.error_handler = EducationalErrorHandler()
        self.input_queue = Queue()
        self.input_sent_event = threading.Event()

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
        return True

    def response_to_client(self, code, data):
        """Send response to client via WebSocket"""
        if data:
            if code == 2000:
                # For input requests, use a synchronous approach with confirmation
                self.input_sent_event.clear()

                # Define a callback that sets the event when message is sent
                async def send_and_signal():
                    await response(self.client, self.cmd_id, code, data)
                    self.input_sent_event.set()

                # Schedule the coroutine in the event loop
                future = asyncio.run_coroutine_threadsafe(send_and_signal(), self.event_loop)
                # Wait for completion
                future.result(timeout=2.0)
            else:
                # For other messages, just send asynchronously
                asyncio.run_coroutine_threadsafe(response(self.client, self.cmd_id, code, data), self.event_loop)

    def create_wrapper_script(self, script_path):
        """Create a wrapper script that overrides input() for interactive capability"""
        wrapper_code = f'''import sys
import builtins
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Store the original input function
_original_input = builtins.input

def _custom_input(prompt=""):
    """Custom input function that signals when input is needed"""
    # Send marker for input request with the prompt
    sys.stdout.write(f"__INPUT_REQUEST_START__{{prompt}}__INPUT_REQUEST_END__")
    sys.stdout.flush()
    
    # Call original input to get user input
    result = _original_input()  # Don't pass prompt since we already displayed it
    
    return result

# Monkey-patch matplotlib.pyplot.show() to capture figures
_original_show = plt.show

def _custom_show(*args, **kwargs):
    """Custom show function that captures matplotlib figures"""
    import io
    import base64
    
    # Save current figure to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    
    # Convert to base64
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    # Send marker with figure data
    print("__MATPLOTLIB_FIGURE_START__")
    print(img_base64)
    print("__MATPLOTLIB_FIGURE_END__")
    sys.stdout.flush()
    
    # Clear the figure
    plt.clf()
    plt.close('all')

plt.show = _custom_show

# Override the built-in input function
builtins.input = _custom_input
builtins.raw_input = _custom_input

# Common aliases that students might use
get_string_input = _custom_input
get_input = _custom_input
read_input = _custom_input
user_input = _custom_input

# Make these available globally
builtins.get_string_input = _custom_input
builtins.get_input = _custom_input
builtins.read_input = _custom_input
builtins.user_input = _custom_input

# Now execute the user script
__user_script_path__ = r"{script_path}"
with open(__user_script_path__, 'r') as f:
    __user_code__ = f.read()

exec(compile(__user_code__, __user_script_path__, 'exec'))
'''

        # Create temporary file for wrapper script
        fd, wrapper_path = tempfile.mkstemp(suffix=".py", prefix="ide_wrapper_")
        with os.fdopen(fd, "w") as f:
            f.write(wrapper_code)

        return wrapper_path

    def process_line(self, line):
        """Process a single line of output"""
        # Check for matplotlib figure markers
        if "__MATPLOTLIB_FIGURE_START__" in line:
            return {"type": "figure_start"}
        elif "__MATPLOTLIB_FIGURE_END__" in line:
            return {"type": "figure_end"}

        # Check for input request
        if "__INPUT_REQUEST_START__" in line:
            # Extract prompt
            if "__INPUT_REQUEST_END__" in line:
                start = line.find("__INPUT_REQUEST_START__") + len("__INPUT_REQUEST_START__")
                end = line.find("__INPUT_REQUEST_END__")
                prompt = line[start:end]
                # Remove the markers from the line
                before = line[: line.find("__INPUT_REQUEST_START__")]
                after = line[line.find("__INPUT_REQUEST_END__") + len("__INPUT_REQUEST_END__") :]
                clean_line = before + after
                return {"type": "input_request", "prompt": prompt, "clean_line": clean_line}
            else:
                # Incomplete input request
                return {"type": "input_start", "partial": line}

        # Check for errors
        if any(err in line for err in ["Traceback", "Error:", "Exception"]):
            return {"type": "error", "line": line}

        # Regular output
        return {"type": "output", "line": line}

    def run_python_program(self):
        """Run Python program with streaming output support"""
        start_time = time.time()
        asyncio.set_event_loop(self.event_loop)

        print(f"[{self.client.id}-Program {self.cmd_id} starting with streaming I/O]")

        wrapper_path = None
        try:
            # Get the script path
            script_path = self.cmd[-1]

            # Create wrapper script
            wrapper_path = self.create_wrapper_script(script_path)

            # Create process with unbuffered output
            self.p = subprocess.Popen(
                [self.cmd[0], "-u", wrapper_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=0,  # Unbuffered
                cwd=os.path.dirname(script_path) if script_path else None,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )

            # Make stdout non-blocking
            fd = self.p.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

            # Variables for handling output
            output_buffer = ""
            figure_buffer = []
            collecting_figure = False
            waiting_for_input = False
            partial_input_request = ""

            while self.alive and self.p.poll() is None:
                # Check client connection
                if not self.client.connected:
                    self.alive = False
                    self.p.kill()
                    self.client.handler_info.remove_subprogram(self.cmd_id)
                    return

                # Check for available output
                try:
                    readable, _, _ = select.select([self.p.stdout], [], [], 0.01)

                    if not readable:
                        # No data available, but check if we have buffered content to send
                        if output_buffer and not waiting_for_input:
                            # Send partial output if no new data for a while
                            if "\n" not in output_buffer and "__INPUT_REQUEST_START__" not in output_buffer:
                                # Still incomplete, wait for more
                                continue
                        else:
                            continue

                    # Read available data
                    try:
                        chunk = self.p.stdout.read(256)  # Read smaller chunks for more responsive output
                        if chunk is None:  # Non-blocking read can return None
                            continue
                    except (IOError, OSError) as e:
                        if e.errno == 11:  # EAGAIN
                            continue
                        else:
                            raise

                    if chunk:
                        output_buffer += chunk

                    # Process buffer line by line and also handle incomplete lines with input markers
                    while True:
                        if not output_buffer:
                            break

                        # Check for input request in incomplete line
                        if "__INPUT_REQUEST_START__" in output_buffer:
                            # Find the position of the marker
                            marker_pos = output_buffer.find("__INPUT_REQUEST_START__")

                            # Send any content before the marker
                            if marker_pos > 0:
                                pre_content = output_buffer[:marker_pos]
                                if pre_content.strip():
                                    self.response_to_client(0, {"stdout": pre_content})

                            # Check if we have the complete input request
                            if "__INPUT_REQUEST_END__" in output_buffer:
                                start = output_buffer.find("__INPUT_REQUEST_START__") + len("__INPUT_REQUEST_START__")
                                end = output_buffer.find("__INPUT_REQUEST_END__")
                                prompt = output_buffer[start:end]

                                # Remove the processed part from buffer
                                output_buffer = output_buffer[end + len("__INPUT_REQUEST_END__") :]

                                # Send the prompt if not empty
                                if prompt:
                                    self.response_to_client(0, {"stdout": prompt})

                                # Send input request
                                self.response_to_client(2000, {"type": "input_request", "prompt": prompt})

                                # Wait for input
                                waiting_for_input = True
                                input_received = False
                                timeout_count = 0

                                while waiting_for_input and self.alive and timeout_count < 600:
                                    try:
                                        user_input = self.input_queue.get(timeout=0.1)
                                        self.p.stdin.write(user_input + "\n")
                                        self.p.stdin.flush()
                                        waiting_for_input = False
                                        input_received = True

                                        # Send confirmation
                                        self.response_to_client(2001, {"type": "input_processed", "input": user_input})
                                        break
                                    except Empty:
                                        timeout_count += 1
                                        continue

                                if not input_received and waiting_for_input:
                                    # Timeout
                                    self.response_to_client(0, {"stdout": "\n[Input timeout]"})
                                    self.p.stdin.write("\n")
                                    self.p.stdin.flush()
                                    waiting_for_input = False
                            else:
                                # Incomplete input request, wait for more data
                                break

                        # Process regular lines
                        elif "\n" in output_buffer:
                            line_end = output_buffer.find("\n")
                            line = output_buffer[:line_end]
                            output_buffer = output_buffer[line_end + 1 :]

                            # Process matplotlib figures
                            if collecting_figure:
                                if "__MATPLOTLIB_FIGURE_END__" in line:
                                    # Send figure
                                    if figure_buffer:
                                        figure_data = "".join(figure_buffer)
                                        self.response_to_client(
                                            3000,
                                            {
                                                "type": "matplotlib_figure",
                                                "data": f"data:image/png;base64,{figure_data}",
                                            },
                                        )
                                    collecting_figure = False
                                    figure_buffer = []
                                else:
                                    figure_buffer.append(line)
                            elif "__MATPLOTLIB_FIGURE_START__" in line:
                                collecting_figure = True
                                figure_buffer = []
                            else:
                                # Send regular output immediately
                                if line or line == "":  # Send empty lines too
                                    # Check for errors and enhance them
                                    if any(err in line for err in ["Traceback", "Error:", "Exception"]):
                                        self.error_buffer.append(line)
                                    elif self.error_buffer:
                                        self.error_buffer.append(line)
                                        if line == "" or not line.startswith(" "):
                                            # End of error
                                            full_error = "\n".join(self.error_buffer)
                                            enhanced = self.error_handler.process_error_output(full_error)
                                            self.response_to_client(0, {"stdout": enhanced})
                                            self.error_buffer = []
                                        continue
                                    else:
                                        # Send line immediately for streaming
                                        self.response_to_client(0, {"stdout": line + "\n"})
                        else:
                            # No complete line yet, wait for more data
                            break

                except Exception as e:
                    print(f"[ERROR] Exception in output processing: {e}")
                    import traceback

                    traceback.print_exc()
                    continue

            # Process any remaining output
            if output_buffer and not collecting_figure:
                self.response_to_client(0, {"stdout": output_buffer})

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
            if wrapper_path and os.path.exists(wrapper_path):
                try:
                    os.remove(wrapper_path)
                except:
                    pass

            self.client.handler_info.remove_subprogram(self.cmd_id)
            print(f"[{self.client.id}-Program {self.cmd_id} finished]")

    def run(self):
        """Thread entry point"""
        self.run_python_program()
