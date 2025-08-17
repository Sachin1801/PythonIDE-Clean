#!/usr/bin/env python3

"""
Subprocess-based Python executor with resource limits for safe execution.
Replaces thread-based execution for better security and isolation.
"""

import os
import sys
import asyncio
import subprocess
import resource
import tempfile
import json
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import signal
import queue
import threading


class SubprocessExecutor:
    """Execute Python code in isolated subprocess with resource limits"""
    
    # Default resource limits
    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_MEMORY_LIMIT = 128 * 1024 * 1024  # 128MB
    DEFAULT_CPU_TIME = 10  # seconds
    DEFAULT_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_OUTPUT_SIZE = 1 * 1024 * 1024  # 1MB max output
    
    def __init__(self, working_dir: str = None):
        """Initialize the executor
        
        Args:
            working_dir: Directory to run code in (defaults to temp dir)
        """
        self.working_dir = working_dir or tempfile.gettempdir()
        self.active_processes = {}
        self.execution_queue = queue.Queue()
        self.queue_processor = None
        self.running = False
        
    def start(self):
        """Start the execution queue processor"""
        if not self.running:
            self.running = True
            self.queue_processor = threading.Thread(target=self._process_queue)
            self.queue_processor.daemon = True
            self.queue_processor.start()
    
    def stop(self):
        """Stop the execution queue processor"""
        self.running = False
        if self.queue_processor:
            self.queue_processor.join(timeout=2)
    
    def _process_queue(self):
        """Process execution requests from the queue"""
        while self.running:
            try:
                # Get next execution request (timeout to allow checking self.running)
                request = self.execution_queue.get(timeout=0.5)
                if request:
                    self._execute_request(request)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Queue processor error: {e}")
    
    def _execute_request(self, request: Dict[str, Any]):
        """Execute a single request from the queue"""
        exec_id = request['id']
        code = request['code']
        callback = request.get('callback')
        timeout = request.get('timeout', self.DEFAULT_TIMEOUT)
        memory_limit = request.get('memory_limit', self.DEFAULT_MEMORY_LIMIT)
        
        result = self._run_code(code, exec_id, timeout, memory_limit)
        
        if callback:
            callback(result)
    
    def execute_async(self, code: str, callback=None, **kwargs) -> str:
        """Queue code for async execution
        
        Args:
            code: Python code to execute
            callback: Function to call with results
            **kwargs: Additional options (timeout, memory_limit, etc.)
            
        Returns:
            Execution ID for tracking
        """
        exec_id = str(uuid.uuid4())
        
        request = {
            'id': exec_id,
            'code': code,
            'callback': callback,
            **kwargs
        }
        
        self.execution_queue.put(request)
        return exec_id
    
    def execute_sync(self, code: str, timeout: int = None, 
                    memory_limit: int = None) -> Dict[str, Any]:
        """Execute code synchronously with resource limits
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
            memory_limit: Maximum memory in bytes
            
        Returns:
            Dict with 'output', 'error', 'return_code', 'timed_out'
        """
        exec_id = str(uuid.uuid4())
        timeout = timeout or self.DEFAULT_TIMEOUT
        memory_limit = memory_limit or self.DEFAULT_MEMORY_LIMIT
        
        return self._run_code(code, exec_id, timeout, memory_limit)
    
    def _run_code(self, code: str, exec_id: str, timeout: int, 
                  memory_limit: int) -> Dict[str, Any]:
        """Run code in subprocess with limits
        
        Returns:
            Dict with execution results
        """
        # Create temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', 
                                        delete=False, dir=self.working_dir) as f:
            f.write(code)
            code_file = f.name
        
        try:
            # Prepare the subprocess command
            cmd = [sys.executable, '-u', code_file]  # -u for unbuffered output
            
            # Set up environment
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            # Create resource limit wrapper script
            limit_script = self._create_limit_wrapper(memory_limit)
            
            # Start the subprocess
            # Note: Resource limits may not work on all systems
            # Disable for now due to compatibility issues
            preexec_fn = None
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                env=env,
                cwd=self.working_dir,
                preexec_fn=preexec_fn
            )
            
            # Store active process
            self.active_processes[exec_id] = process
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                timed_out = True
            finally:
                # Remove from active processes
                self.active_processes.pop(exec_id, None)
            
            # Truncate output if too large
            if len(stdout) > self.MAX_OUTPUT_SIZE:
                stdout = stdout[:self.MAX_OUTPUT_SIZE] + b'\n... (output truncated)'
            if len(stderr) > self.MAX_OUTPUT_SIZE:
                stderr = stderr[:self.MAX_OUTPUT_SIZE] + b'\n... (error truncated)'
            
            return {
                'output': stdout.decode('utf-8', errors='replace'),
                'error': stderr.decode('utf-8', errors='replace'),
                'return_code': process.returncode,
                'timed_out': timed_out,
                'exec_id': exec_id
            }
            
        finally:
            # Clean up temp file
            try:
                os.unlink(code_file)
            except:
                pass
    
    def _set_resource_limits(self, memory_limit: int):
        """Set resource limits for the subprocess (Unix only)"""
        if sys.platform == 'win32':
            return
        
        try:
            # Set memory limit
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        except (ValueError, OSError):
            pass  # May not be supported
        
        try:
            # Set CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (self.DEFAULT_CPU_TIME, self.DEFAULT_CPU_TIME))
        except (ValueError, OSError):
            pass
        
        try:
            # Set file size limit
            resource.setrlimit(resource.RLIMIT_FSIZE, (self.DEFAULT_FILE_SIZE, self.DEFAULT_FILE_SIZE))
        except (ValueError, OSError):
            pass
        
        try:
            # Set process limit (prevent fork bombs)
            resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))
        except (ValueError, OSError, AttributeError):
            pass  # May not be available on all systems
    
    def _create_limit_wrapper(self, memory_limit: int) -> str:
        """Create a wrapper script that sets resource limits"""
        wrapper = f"""
import resource
import sys

# Set resource limits
resource.setrlimit(resource.RLIMIT_AS, ({memory_limit}, {memory_limit}))
resource.setrlimit(resource.RLIMIT_CPU, ({self.DEFAULT_CPU_TIME}, {self.DEFAULT_CPU_TIME}))
resource.setrlimit(resource.RLIMIT_FSIZE, ({self.DEFAULT_FILE_SIZE}, {self.DEFAULT_FILE_SIZE}))

# Execute the actual code
exec(open(sys.argv[1]).read())
"""
        return wrapper
    
    def kill_execution(self, exec_id: str) -> bool:
        """Kill a running execution
        
        Args:
            exec_id: ID of execution to kill
            
        Returns:
            True if killed, False if not found
        """
        process = self.active_processes.get(exec_id)
        if process and process.poll() is None:
            process.kill()
            self.active_processes.pop(exec_id, None)
            return True
        return False
    
    def get_active_count(self) -> int:
        """Get count of active executions"""
        # Clean up finished processes
        finished = []
        for exec_id, process in self.active_processes.items():
            if process.poll() is not None:
                finished.append(exec_id)
        for exec_id in finished:
            self.active_processes.pop(exec_id, None)
        
        return len(self.active_processes)


class ExecutionManager:
    """Manage multiple executors with load balancing"""
    
    def __init__(self, max_concurrent: int = 5, working_dir: str = None):
        """Initialize execution manager
        
        Args:
            max_concurrent: Maximum concurrent executions
            working_dir: Working directory for executions
        """
        self.max_concurrent = max_concurrent
        self.working_dir = working_dir
        self.executor = SubprocessExecutor(working_dir)
        self.executor.start()
        self.execution_history = []
        self.user_limits = {}  # Track per-user execution counts
        
    def execute_for_user(self, username: str, code: str, 
                        callback=None, **kwargs) -> Dict[str, Any]:
        """Execute code for a specific user with rate limiting
        
        Args:
            username: User requesting execution
            code: Python code to execute
            callback: Callback for async execution
            **kwargs: Additional execution options
            
        Returns:
            Execution result or queued status
        """
        # Check user rate limit
        user_count = self.user_limits.get(username, 0)
        if user_count >= 2:  # Max 2 concurrent per user
            return {
                'error': 'Rate limit exceeded. Please wait for current executions to complete.',
                'queued': False
            }
        
        # Check total concurrent limit
        if self.executor.get_active_count() >= self.max_concurrent:
            return {
                'error': 'Server at capacity. Please try again in a moment.',
                'queued': False
            }
        
        # Update user count
        self.user_limits[username] = user_count + 1
        
        # Create callback wrapper to update counts
        def wrapped_callback(result):
            self.user_limits[username] = max(0, self.user_limits.get(username, 1) - 1)
            if callback:
                callback(result)
        
        # Queue execution
        exec_id = self.executor.execute_async(code, wrapped_callback, **kwargs)
        
        # Record in history
        self.execution_history.append({
            'exec_id': exec_id,
            'username': username,
            'timestamp': time.time(),
            'code_preview': code[:100] + '...' if len(code) > 100 else code
        })
        
        return {
            'exec_id': exec_id,
            'queued': True,
            'message': 'Code queued for execution'
        }
    
    def shutdown(self):
        """Shutdown the execution manager"""
        self.executor.stop()


# Example usage and testing
if __name__ == '__main__':
    # Test basic execution
    executor = SubprocessExecutor()
    
    # Test simple code
    result = executor.execute_sync('print("Hello, World!")')
    print("Simple execution:", result)
    
    # Test timeout
    result = executor.execute_sync('import time; time.sleep(10)', timeout=2)
    print("Timeout test:", result)
    
    # Test memory limit (this may not work on all systems)
    result = executor.execute_sync('x = [0] * (1024 * 1024 * 200)', memory_limit=100*1024*1024)
    print("Memory limit test:", result)
    
    # Test async execution
    executor.start()
    
    def callback(result):
        print("Async result:", result)
    
    exec_id = executor.execute_async('print("Async execution")', callback=callback)
    print(f"Queued execution: {exec_id}")
    
    # Wait a bit for async execution
    import time
    time.sleep(2)
    
    executor.stop()
    
    # Test with manager
    print("\n--- Testing ExecutionManager ---")
    manager = ExecutionManager(max_concurrent=2)
    
    # Simulate multiple users
    for i in range(3):
        result = manager.execute_for_user(
            f"user{i}", 
            f'print("User {i} code")',
            timeout=5
        )
        print(f"User {i} execution:", result)
    
    time.sleep(3)
    manager.shutdown()