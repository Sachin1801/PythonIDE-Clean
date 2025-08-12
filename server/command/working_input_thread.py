#!/usr/bin/env python3
"""
Working input handler - properly handles multiple inputs
"""

import os
import time
import threading
import subprocess
import select
from queue import Queue, Empty

class WorkingInputThread(threading.Thread):
    """Properly working input handler using select for non-blocking I/O"""
    
    def __init__(self, cmd, cmd_id, client, event_loop):
        super().__init__()
        self.cmd = cmd
        self.cmd_id = cmd_id
        self.client = client
        self.alive = True
        self.daemon = True
        self.process = None
        self.input_queue = Queue()
        # Store main loop reference
        from tornado.ioloop import IOLoop
        self.main_loop = IOLoop.current()
        
    def stop(self):
        """Stop the program"""
        self.alive = False
        if self.process:
            try:
                self.process.terminate()
                self.process.kill()
            except:
                pass
    
    def send_input(self, user_input):
        """Queue input to send"""
        # Queue the input
        self.input_queue.put(user_input)
        return True
    
    def send_to_client(self, code, data):
        """Send to client via main loop"""
        from .response import response
        self.main_loop.add_callback(response, self.client, self.cmd_id, code, data)
    
    def run(self):
        """Run with proper non-blocking I/O"""
        print(f'[{self.client.id}-Program {self.cmd_id} starting with interactive I/O]')
        
        try:
            # Start process with pipes
            self.process = subprocess.Popen(
                self.cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=0  # Unbuffered
            )
            
            # Make stdout non-blocking using select
            import fcntl
            fd = self.process.stdout.fileno()
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            
            buffer = ""
            last_char_time = time.time()
            last_input_check = time.time()
            waiting_for_input = False
            
            while self.alive and self.process.poll() is None:
                # Use select to check if data is available
                readable, _, _ = select.select([self.process.stdout], [], [], 0.01)
                
                if readable:
                    try:
                        # Read available data
                        chunk = os.read(fd, 4096).decode('utf-8', errors='replace')
                        if chunk:
                            buffer += chunk
                            last_char_time = time.time()
                            waiting_for_input = False  # Reset input flag when we get output
                            # Successfully read chunk
                            
                            # Process complete lines
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                self.send_to_client(0, {'stdout': line})
                                # Line sent to client
                    except:
                        pass
                
                # Enhanced input detection logic
                current_time = time.time()
                
                # Pattern-based input detection (existing logic)
                if buffer and (current_time - last_char_time) > 0.1:
                    # Check if it looks like an input prompt
                    if (buffer.endswith(': ') or buffer.endswith('? ') or 
                        buffer.endswith('> ') or buffer.endswith('>>> ') or
                        ': ' in buffer[-30:]):  # Check last 30 chars for prompt pattern
                        
                        # Detected input prompt with pattern
                        self.send_to_client(0, {'stdout': buffer})
                        self.send_to_client(2000, {
                            'type': 'input_request',
                            'prompt': buffer
                        })
                        buffer = ""
                        waiting_for_input = True
                        last_input_check = current_time
                        
                    elif len(buffer) > 200:  # Flush large buffers
                        self.send_to_client(0, {'stdout': buffer})
                        buffer = ""
                
                # Silent input detection (NEW LOGIC)
                elif not waiting_for_input and (current_time - last_input_check) > 0.5:
                    # Check if process is potentially waiting for input
                    # Conditions: no recent output, buffer is empty/small, process still running
                    if len(buffer) == 0 and (current_time - last_char_time) > 0.5:
                        # Check if stdin is ready for writing (process is waiting)
                        try:
                            _, writable, _ = select.select([], [self.process.stdin], [], 0)
                            if writable:
                                # Process is likely waiting for input silently
                                self.send_to_client(2000, {
                                    'type': 'input_request',
                                    'prompt': ''  # Empty prompt for silent input
                                })
                                waiting_for_input = True
                                last_input_check = current_time
                        except Exception as e:
                            pass
                
                # Handle input when we're waiting for it
                if waiting_for_input:
                    try:
                        user_input = self.input_queue.get(timeout=0.1)
                        # Got user input
                        
                        # Send to process
                        if not user_input.endswith('\n'):
                            user_input += '\n'
                        self.process.stdin.write(user_input)
                        self.process.stdin.flush()
                        
                        # Echo to console
                        self.send_to_client(0, {'stdout': user_input.strip()})
                        
                        waiting_for_input = False
                        last_input_check = current_time
                        
                    except Empty:
                        # Check for input timeout (60 seconds)
                        if (current_time - last_input_check) > 60:
                            self.send_to_client(0, {'stdout': '[Input timeout]'})
                            self.process.stdin.write('\n')
                            self.process.stdin.flush()
                            waiting_for_input = False

            
            # Send any remaining output
            if buffer:
                self.send_to_client(0, {'stdout': buffer})
            
            # Send completion
            exit_code = self.process.returncode if self.process else -1
            self.send_to_client(1111, {'stdout': f'\n[Program finished with exit code {exit_code}]'})
            # Program finished
            
        except Exception as e:
            print(f'[Program {self.cmd_id} exception]: {e}')
            self.send_to_client(1111, {'stdout': f'[Error: {e}]'})
        finally:
            self.stop()
            # Program terminated