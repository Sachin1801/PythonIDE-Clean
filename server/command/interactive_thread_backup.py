#!/usr/bin/env python3
"""
Interactive SubProgram Thread for Python Web IDE
Handles interactive input/output and matplotlib display
"""

import os
import sys
import time
import asyncio
import threading
import subprocess
import tempfile
from queue import Queue, Empty
from threading import Event
from tornado.ioloop import IOLoop
from .response import response
from .error_handler import EducationalErrorHandler

class InteractiveSubProgramThread(threading.Thread):
    """Enhanced thread for running Python programs with interactive I/O"""
    
    def __init__(self, cmd, cmd_id, client, event_loop):
        super(InteractiveSubProgramThread, self).__init__()
        self.cmd = cmd
        self.cmd_id = cmd_id
        self.client = client
        self.alive = True
        self.daemon = True
        self.event_loop = event_loop
        self.p = None
        self.error_handler = EducationalErrorHandler()
        self.error_buffer = []
        self.input_queue = Queue()
        self.waiting_for_input = False
        self.input_sent_event = Event()  # Event to signal when input request is sent
        
    def stop(self):
        """Stop the running program"""
        self.alive = False
        if self.p:
            try:
                self.p.kill()
            except:
                pass
            self.p = None
    
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
                
                # Schedule the callback
                IOLoop.current().add_callback(send_and_signal)
            else:
                # Regular messages use spawn_callback
                IOLoop.current().spawn_callback(response, self.client, self.cmd_id, code, data)
    
    def create_wrapper_script(self, script_path):
        """Create a temporary wrapper script that includes our custom input handling"""
        import tempfile
        import os
        
        wrapper_code = '''
import sys
import os

# Add script directory to path so imports work
sys.path.insert(0, os.path.dirname(r"{script_path}"))

# Configure matplotlib for non-interactive backend
_matplotlib_configured = False
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO
    import base64
    
    _original_show = plt.show
    
    def _custom_show(*args, **kwargs):
        """Custom show function that captures figures"""
        fig = plt.gcf()
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Output special markers with base64 data
        print("__MATPLOTLIB_FIGURE_START__", flush=True)
        print(base64.b64encode(buf.read()).decode('utf-8'), flush=True)
        print("__MATPLOTLIB_FIGURE_END__", flush=True)
        
        plt.close(fig)
        buf.close()
    
    plt.show = _custom_show
    _matplotlib_configured = True
except ImportError:
    pass  # matplotlib not installed

# Override input to add markers
import builtins
import sys

def _custom_input(prompt=""):
    """Custom input that adds markers for detection"""
    # Always ensure we have a prompt, even if empty
    prompt_str = str(prompt) if prompt else ""
    # Send the prompt with markers to stdout for detection
    sys.stdout.write("__INPUT_REQUEST_START__" + prompt_str + "__INPUT_REQUEST_END__")
    sys.stdout.flush()
    # Read input directly from stdin instead of calling original input
    # This works because stdin is properly piped from the subprocess
    result = sys.stdin.readline().rstrip('\\n')
    # Echo the input back like a real terminal
    if result:
        sys.stdout.write(result + '\\n')
        sys.stdout.flush()
    return result

# Override the built-in input function
builtins.input = _custom_input
builtins.raw_input = _custom_input  # For Python 2 compatibility if needed

# Create common input function aliases that users might define
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
'''.format(script_path=script_path)
        
        # Create temporary file for wrapper script
        fd, wrapper_path = tempfile.mkstemp(suffix='.py', prefix='ide_wrapper_')
        with os.fdopen(fd, 'w') as f:
            f.write(wrapper_code)
        
        return wrapper_path
    
    def run_python_program(self):
        """Run Python program with interactive I/O support"""
        start_time = time.time()
        asyncio.set_event_loop(self.event_loop)
        
        print(f'[{self.client.id}-Program {self.cmd_id} starting with interactive I/O]')
        print(f'[BACKEND-INPUT-DEBUG] Starting Python program execution')
        print(f'[BACKEND-INPUT-DEBUG] Command: {self.cmd}')
        
        wrapper_path = None
        try:
            # Get the script path
            script_path = self.cmd[-1]
            print(f'[BACKEND-INPUT-DEBUG] Script path: {script_path}')
            
            # Create wrapper script
            wrapper_path = self.create_wrapper_script(script_path)
            print(f'[BACKEND-INPUT-DEBUG] Wrapper script created at: {wrapper_path}')
            
            # Create process with pipes for interactive I/O
            print(f'[BACKEND-INPUT-DEBUG] Creating subprocess with pipes...')
            self.p = subprocess.Popen(
                [self.cmd[0], '-u', wrapper_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr with stdout
                universal_newlines=True,
                bufsize=0,  # Unbuffered
                cwd=os.path.dirname(script_path) if script_path else None,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}  # Force Python unbuffered
            )
            
            print(f'[BACKEND-INPUT-DEBUG] Subprocess started with PID: {self.p.pid}')
            
            # Variables for handling output
            figure_buffer = []
            collecting_figure = False
            waiting_for_input = False
            output_buffer = []  # Buffer for incomplete lines
            
            print(f'[BACKEND-INPUT-DEBUG] Starting main output reading loop...')
            
            # Make stdout non-blocking
            import fcntl
            import select
            fd = self.p.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            
            while self.alive and self.p.poll() is None:
                # Check client connection
                if not self.client.connected:
                    self.alive = False
                    self.p.kill()
                    self.client.handler_info.remove_subprogram(self.cmd_id)
                    print(f'[{self.client.id}-Program {self.cmd_id} killed - client disconnected]')
                    return
                
                # Use select to check if data is available
                try:
                    readable, _, _ = select.select([self.p.stdout], [], [], 0.1)
                    
                    if not readable:
                        continue
                    
                    # Read available data (non-blocking)
                    try:
                        chunk = self.p.stdout.read(1024)  # Read up to 1024 chars
                    except (IOError, OSError) as e:
                        if e.errno == 11:  # EAGAIN - no data available
                            continue
                        else:
                            raise
                    
                    if not chunk:
                        continue
                    
                    # Process the chunk character by character to handle prompts
                    output_buffer.append(chunk)
                    current_output = ''.join(output_buffer)
                    
                    # Check if we have complete lines or input markers
                    lines = current_output.split('\n')
                    
                    # Process all complete lines
                    for i in range(len(lines) - 1):
                        line = lines[i]
                    
                    # Keep the last incomplete line in buffer
                    output_buffer = [lines[-1]] if lines[-1] else []
                    
                    # Also check if the incomplete line contains an input request
                    if output_buffer and '__INPUT_REQUEST_START__' in output_buffer[0]:
                        # We have an input prompt, process it
                        line = output_buffer[0]
                        output_buffer = []
                        print(f'[BACKEND-INPUT-DEBUG] Processing line: {repr(line[:100])}...' if len(line) > 100 else f'[BACKEND-INPUT-DEBUG] Processing line: {repr(line)}')
                        
                        # Debug log for input detection
                        if "__INPUT" in line:
                            print(f"[BACKEND-INPUT-DEBUG] *** FOUND INPUT MARKER IN LINE: {line}")
                        
                        # Check for matplotlib figure
                        if "__MATPLOTLIB_FIGURE_START__" in line:
                            collecting_figure = True
                            figure_buffer = []
                            continue
                        elif "__MATPLOTLIB_FIGURE_END__" in line:
                            if collecting_figure and figure_buffer:
                                # Send matplotlib figure to client
                                figure_data = ''.join(figure_buffer)
                                self.response_to_client(3000, {
                                    'type': 'matplotlib_figure',
                                    'data': f'data:image/png;base64,{figure_data}'
                                })
                            collecting_figure = False
                            figure_buffer = []
                            continue
                        elif collecting_figure:
                            # Collect figure data
                            figure_buffer.append(line)
                            continue
                        
                        # Check for input request
                        if "__INPUT_REQUEST_START__" in line:
                            print(f"[BACKEND-INPUT-DEBUG] *** DETECTED INPUT REQUEST START MARKER!")
                            # Extract prompt - handle both cases where it's on same line or split
                            if "__INPUT_REQUEST_END__" in line:
                                print(f"[BACKEND-INPUT-DEBUG] Both markers on same line")
                                start = line.find("__INPUT_REQUEST_START__") + len("__INPUT_REQUEST_START__")
                                end = line.find("__INPUT_REQUEST_END__")
                                prompt = line[start:end]
                                print(f"[BACKEND-INPUT-DEBUG] Extracted prompt: '{prompt}'")
                            else:
                                print(f"[BACKEND-INPUT-DEBUG] Markers split across lines")
                                # Marker split across lines, extract what we have
                                start = line.find("__INPUT_REQUEST_START__") + len("__INPUT_REQUEST_START__")
                                prompt = line[start:]
                                # Read next part if needed
                                next_line = self.p.stdout.readline()
                                print(f"[BACKEND-INPUT-DEBUG] Next line: {repr(next_line)}")
                                if next_line and "__INPUT_REQUEST_END__" in next_line:
                                    end = next_line.find("__INPUT_REQUEST_END__")
                                    prompt += next_line[:end]
                                print(f"[BACKEND-INPUT-DEBUG] Final prompt after combining: '{prompt}'")
                            
                            # Ensure previous output has been sent
                            
                            # Display the prompt in the console (even if empty)
                            if prompt:
                                print(f"[BACKEND-INPUT-DEBUG] Sending prompt to client: '{prompt}'")
                                self.response_to_client(0, {'stdout': prompt})
                            elif prompt == "":
                                print(f"[BACKEND-INPUT-DEBUG] Empty prompt detected")
                                # For empty prompt, we might want to indicate input is needed
                                pass  # Frontend will show input field without prompt
                            
                            # Send input request to client
                            print(f"[BACKEND-INPUT-DEBUG] *** SENDING INPUT REQUEST TO CLIENT with prompt: '{prompt}'")
                            self.response_to_client(2000, {
                                'type': 'input_request',
                                'prompt': prompt
                            })
                            
                            # Wait for confirmation that the message was sent
                            if self.input_sent_event.wait(timeout=2.0):
                                print(f"[DEBUG] Input request confirmed sent, waiting for user input...")
                            else:
                                print(f"[DEBUG] Warning: Input request may not have been sent")
                            
                            # Wait for input from client
                            waiting_for_input = True
                            print(f"[BACKEND-INPUT-DEBUG] *** WAITING FOR USER INPUT FROM CLIENT...")
                            
                            # Wait for input with timeout
                            input_received = False
                            timeout_count = 0
                            while waiting_for_input and self.alive and timeout_count < 600:  # 60 second timeout
                                try:
                                    user_input = self.input_queue.get(timeout=0.1)
                                    print(f"[BACKEND-INPUT-DEBUG] *** RECEIVED USER INPUT: '{user_input}'")
                                    # Send input to program
                                    print(f"[BACKEND-INPUT-DEBUG] Writing to subprocess stdin: '{user_input}\\n'")
                                    self.p.stdin.write(user_input + '\n')
                                    self.p.stdin.flush()
                                    print(f"[BACKEND-INPUT-DEBUG] Input flushed to subprocess")
                                    waiting_for_input = False
                                    input_received = True
                                    
                                    # Send confirmation that input was processed
                                    self.response_to_client(2001, {
                                        'type': 'input_processed',
                                        'input': user_input
                                    })
                                    
                                    # Don't echo here - the custom_input function will handle it
                                    print(f"[BACKEND-INPUT-DEBUG] Input processing complete")
                                    break
                                except Empty:
                                    timeout_count += 1
                                    if timeout_count % 100 == 0:  # Log every 10 seconds
                                        print(f"[BACKEND-INPUT-DEBUG] Still waiting for input... ({timeout_count/10} seconds)")
                                    continue
                            
                            if not input_received and waiting_for_input:
                                # Timeout or cancelled
                                self.response_to_client(0, {'stdout': '\n[Input timeout or cancelled]'})
                                # Send empty input to unblock
                                self.p.stdin.write('\n')
                                self.p.stdin.flush()
                                waiting_for_input = False
                            
                            continue
                        
                        # Check for errors and enhance them
                        if any(err in line for err in ['Traceback', 'Error:', 'Exception']):
                            self.error_buffer.append(line)
                        elif self.error_buffer:
                            # Process collected error
                            self.error_buffer.append(line)
                            if line == '' or not line.startswith(' '):
                                # End of error, process it
                                full_error = '\n'.join(self.error_buffer)
                                enhanced = self.error_handler.process_error_output(full_error)
                                self.response_to_client(0, {'stdout': enhanced})
                                self.error_buffer = []
                            continue
                        else:
                            # Regular output - send immediately to avoid delays
                            if line:  # Only send non-empty lines
                                self.response_to_client(0, {'stdout': line})
                    
                except Exception as e:
                    # Handle read errors
                    if self.alive:
                        print(f"Read error: {e}")
                    break
                
                # Small delay to prevent CPU spinning
                time.sleep(0.001)
            
            # Process any remaining error buffer
            if self.error_buffer:
                full_error = '\n'.join(self.error_buffer)
                enhanced = self.error_handler.process_error_output(full_error)
                self.response_to_client(0, {'stdout': enhanced})
            
            # Get final output if any
            if self.p and self.p.stdout:
                try:
                    remaining = self.p.stdout.read()
                    if remaining:
                        self.response_to_client(0, {'stdout': remaining})
                except:
                    pass
            
            # Send completion message
            if not self.alive:
                self.response_to_client(1111, {'stdout': '[Program terminated]'})
            else:
                exit_code = self.p.returncode if self.p else -1
                elapsed = time.time() - start_time
                msg = f'[Finished in {elapsed:.2f}s with exit code {exit_code}]'
                self.response_to_client(1111, {'stdout': msg})
            
            self.client.handler_info.remove_subprogram(self.cmd_id)
            
            if self.p and self.p.returncode == 0:
                print(f'{self.client.id}-Program {self.cmd_id} success')
            else:
                print(f'{self.client.id}-Program {self.cmd_id} failed')
                
        except Exception as e:
            print(f'[{self.client.id}-Program {self.cmd_id} exception]: {e}')
            self.response_to_client(1111, {'stdout': f'[Program exception]: {e}'})
        finally:
            # Clean up wrapper script
            if wrapper_path and os.path.exists(wrapper_path):
                try:
                    os.remove(wrapper_path)
                except:
                    pass
            if self.p:
                try:
                    self.p.kill()
                except:
                    pass
            try:
                self.client.handler_info.remove_subprogram(self.cmd_id)
            except:
                pass
            self.alive = False
    
    def run(self):
        """Main thread run method"""
        self.alive = True
        try:
            self.run_python_program()
        except Exception as e:
            print(f"Thread exception: {e}")
        self.alive = False