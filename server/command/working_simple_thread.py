#!/usr/bin/env python3
"""
Working simple interactive Python execution using character-by-character reading.
This approach actually works by reading one character at a time to detect prompts.
"""

import subprocess
import threading
import time
import os
import asyncio
import select
import fcntl
from queue import Queue, Empty

from common.config import Config
from command.error_handler import EducationalErrorHandler
from command.response import response

class WorkingSimpleThread(threading.Thread):
    """Working implementation with character-by-character reading"""
    
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
        """Run Python program with character-by-character reading"""
        start_time = time.time()
        asyncio.set_event_loop(self.event_loop)
        
        print(f'[{self.client.id}-Program {self.cmd_id} starting with working I/O]')
        
        try:
            script_path = self.cmd[-1]
            
            # Start subprocess
            self.p = subprocess.Popen(
                self.cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,  # Unbuffered binary mode
                cwd=os.path.dirname(script_path) if script_path else None,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            
            # Make stdout non-blocking
            fd = self.p.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            
            buffer = b""
            last_activity = time.time()
            waiting_for_input = False
            initial_check = True  # Flag to check for immediate input
            
            while self.alive and self.p.poll() is None:
                # Check client connection
                if not self.client.connected:
                    self.alive = False
                    self.p.kill()
                    self.client.handler_info.remove_subprogram(self.cmd_id)
                    return
                
                # Check for available data
                readable, _, _ = select.select([self.p.stdout], [], [], 0.01)
                
                if readable:
                    try:
                        # Read one byte at a time
                        char = os.read(fd, 1)
                        if char:
                            buffer += char
                            last_activity = time.time()
                            
                            # If we have a newline, send the complete line
                            if char == b'\n':
                                try:
                                    line = buffer.decode('utf-8', errors='replace')
                                    self.response_to_client(0, {'stdout': line})
                                    buffer = b""
                                except:
                                    pass
                    except (OSError, IOError) as e:
                        if e.errno != 11:  # Ignore EAGAIN
                            raise
                
                # Special case: Check immediately after start for input() on first line
                if initial_check and time.time() - start_time > 0.1:
                    initial_check = False
                    # If we have any output that looks like a prompt right at start
                    if buffer and not waiting_for_input:
                        try:
                            partial = buffer.decode('utf-8', errors='replace')
                            # If it doesn't end with newline, it's likely a prompt
                            if not partial.endswith('\n'):
                                # Send the prompt
                                self.response_to_client(0, {'stdout': partial})
                                buffer = b""
                                
                                # Send input request
                                self.response_to_client(2000, {
                                    'type': 'input_request',
                                    'prompt': partial.strip()
                                })
                                
                                waiting_for_input = True
                                last_activity = time.time()
                        except:
                            pass
                
                # Check if we're likely waiting for input
                # If no activity for 0.2 seconds and we have a partial line
                elif buffer and time.time() - last_activity > 0.2 and not waiting_for_input:
                    try:
                        partial = buffer.decode('utf-8', errors='replace')
                        
                        # Check if this looks like an input prompt
                        prompt_indicators = [
                            ':', '?', '>', 
                            'enter', 'input', 'name', 'password', 
                            'age', 'choice', 'type', 'provide'
                        ]
                        
                        is_prompt = any(ind in partial.lower() for ind in prompt_indicators)
                        
                        if is_prompt or (partial and not partial.endswith('\n')):
                            # Send the partial line as output
                            self.response_to_client(0, {'stdout': partial})
                            buffer = b""
                            
                            # Send input request
                            self.response_to_client(2000, {
                                'type': 'input_request',
                                'prompt': partial.strip()
                            })
                            
                            waiting_for_input = True
                            last_activity = time.time()
                    except:
                        pass
                
                # Handle user input
                if waiting_for_input:
                    try:
                        user_input = self.input_queue.get(timeout=0.01)
                        
                        # Send input to program
                        self.p.stdin.write((user_input + '\n').encode())
                        self.p.stdin.flush()
                        
                        # Echo input
                        self.response_to_client(0, {'stdout': user_input + '\n'})
                        
                        waiting_for_input = False
                        last_activity = time.time()
                        
                        # Send confirmation
                        self.response_to_client(2001, {
                            'type': 'input_processed',
                            'input': user_input
                        })
                    except Empty:
                        pass
                
                # Also check if we should send partial output after a timeout
                if buffer and time.time() - last_activity > 1.0:
                    try:
                        partial = buffer.decode('utf-8', errors='replace')
                        if partial:
                            self.response_to_client(0, {'stdout': partial})
                            buffer = b""
                    except:
                        pass
            
            # Send any remaining output
            if buffer:
                try:
                    remaining = buffer.decode('utf-8', errors='replace')
                    if remaining:
                        self.response_to_client(0, {'stdout': remaining})
                except:
                    pass
            
            # Read any final output
            try:
                final = self.p.stdout.read()
                if final:
                    self.response_to_client(0, {'stdout': final.decode('utf-8', errors='replace')})
            except:
                pass
            
            # Get exit code
            exit_code = self.p.wait() if self.p else 1
            
            # Send completion
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
            if self.p:
                try:
                    self.p.terminate()
                except:
                    pass
            
            self.client.handler_info.remove_subprogram(self.cmd_id)
            print(f'[{self.client.id}-Program {self.cmd_id} finished]')
    
    def run(self):
        """Thread entry point"""
        self.run_python_program()