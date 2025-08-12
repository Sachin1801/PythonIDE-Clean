#!/usr/bin/env python3
"""
PTY-based interactive Python execution thread.

This approach uses a pseudo-terminal (PTY) which properly handles input/output
like a real terminal, solving the buffering and prompt detection issues.
"""

import subprocess
import threading
import time
import os
import sys
import pty
import select
import termios
import tty
import asyncio
from queue import Queue, Empty

from common.config import Config
from command.error_handler import EducationalErrorHandler
from command.response import response

class PTYInteractiveThread(threading.Thread):
    """Thread for running Python programs with PTY-based interactive I/O"""
    
    def __init__(self, cmd, cmd_id, client, event_loop):
        super().__init__()
        self.cmd = cmd
        self.cmd_id = cmd_id
        self.client = client
        self.event_loop = event_loop
        self.alive = True
        self.master_fd = None
        self.p = None
        self.error_buffer = []
        self.error_handler = EducationalErrorHandler()
        self.input_queue = Queue()
        
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
            asyncio.run_coroutine_threadsafe(
                response(self.client, self.cmd_id, code, data),
                self.event_loop
            )
    
    def run_python_program(self):
        """Run Python program using PTY for proper terminal emulation"""
        start_time = time.time()
        asyncio.set_event_loop(self.event_loop)
        
        print(f'[{self.client.id}-Program {self.cmd_id} starting with PTY I/O]')
        
        try:
            # Create a pseudo-terminal
            master_fd, slave_fd = pty.openpty()
            self.master_fd = master_fd
            
            # Get the script path
            script_path = self.cmd[-1]
            
            # Start the subprocess with the PTY
            self.p = subprocess.Popen(
                self.cmd,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=os.path.dirname(script_path) if script_path else None,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'},
                close_fds=True
            )
            
            # Close the slave end in parent process
            os.close(slave_fd)
            
            # Make the master non-blocking
            import fcntl
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            
            # Variables for handling output
            output_buffer = ""
            prompt_buffer = ""
            waiting_for_input = False
            last_output_time = time.time()
            
            while self.alive and self.p.poll() is None:
                # Check client connection
                if not self.client.connected:
                    self.alive = False
                    self.p.kill()
                    self.client.handler_info.remove_subprogram(self.cmd_id)
                    return
                
                # Check for available output from PTY
                readable, writable, _ = select.select([master_fd], [], [], 0.01)
                
                if readable:
                    try:
                        # Read from PTY
                        data = os.read(master_fd, 1024)
                        if data:
                            # Decode the data
                            text = data.decode('utf-8', errors='replace')
                            output_buffer += text
                            last_output_time = time.time()
                            
                            # Process complete lines immediately
                            while '\n' in output_buffer:
                                line_end = output_buffer.find('\n')
                                line = output_buffer[:line_end + 1]
                                output_buffer = output_buffer[line_end + 1:]
                                
                                # Send line to client
                                self.response_to_client(0, {'stdout': line})
                            
                            # Check if we have a prompt (incomplete line waiting)
                            # Common patterns: ">>> ", "... ", "Enter ", "Input:", "Password:", ending with ": "
                            if output_buffer:
                                prompt_patterns = [
                                    '>>> ',  # Python REPL
                                    '... ',  # Python REPL continued
                                    ': ',    # Common prompt ending
                                    '? ',    # Question prompt
                                    '> ',    # Generic prompt
                                ]
                                
                                # Check if buffer ends with a prompt pattern
                                is_prompt = any(output_buffer.endswith(p) for p in prompt_patterns)
                                
                                # Also check for common input keywords
                                input_keywords = ['enter', 'input', 'password', 'name', 'age', 'choice']
                                has_input_keyword = any(k in output_buffer.lower() for k in input_keywords)
                                
                                # If it looks like a prompt and hasn't changed for a bit
                                if (is_prompt or has_input_keyword) and time.time() - last_output_time > 0.1:
                                    # Send the prompt to client
                                    if output_buffer.strip():
                                        self.response_to_client(0, {'stdout': output_buffer})
                                    
                                    # Signal that we're waiting for input
                                    self.response_to_client(2000, {
                                        'type': 'input_request',
                                        'prompt': output_buffer.strip()
                                    })
                                    
                                    output_buffer = ""
                                    waiting_for_input = True
                    
                    except (OSError, IOError) as e:
                        if e.errno == 11:  # EAGAIN
                            pass
                        else:
                            raise
                
                # Check for user input to send
                if waiting_for_input or not self.input_queue.empty():
                    try:
                        user_input = self.input_queue.get_nowait()
                        # Write to PTY
                        os.write(master_fd, (user_input + '\n').encode('utf-8'))
                        waiting_for_input = False
                        
                        # Send confirmation
                        self.response_to_client(2001, {
                            'type': 'input_processed',
                            'input': user_input
                        })
                    except Empty:
                        pass
                
                # Send partial output if it's been waiting too long
                if output_buffer and time.time() - last_output_time > 0.5:
                    self.response_to_client(0, {'stdout': output_buffer})
                    output_buffer = ""
            
            # Send any remaining output
            if output_buffer:
                self.response_to_client(0, {'stdout': output_buffer})
            
            # Get exit code
            exit_code = self.p.wait() if self.p else 1
            
            # Send completion message
            elapsed = time.time() - start_time
            completion_msg = f"\n[Program finished in {elapsed:.2f}s with exit code {exit_code}]"
            self.response_to_client(1111, {'stdout': completion_msg})
            
        except Exception as e:
            error_msg = f"Error running program: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            self.response_to_client(1111, {'stdout': error_msg})
        
        finally:
            # Cleanup
            if self.master_fd:
                try:
                    os.close(self.master_fd)
                except:
                    pass
            
            self.client.handler_info.remove_subprogram(self.cmd_id)
            print(f'[{self.client.id}-Program {self.cmd_id} finished]')
    
    def run(self):
        """Thread entry point"""
        self.run_python_program()