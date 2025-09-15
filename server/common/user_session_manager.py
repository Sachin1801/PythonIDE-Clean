#!/usr/bin/env python3
"""
Simple User Session Manager for 8-10 concurrent users
Thread-based architecture for current hardware (1 vCPU, 4GB RAM)
"""

import threading
import subprocess
import time
import queue
import os
import sys
import tempfile
import json
from typing import Dict, Optional, Any
import logging
import psutil

logger = logging.getLogger(__name__)

class SimpleUserSession:
    """
    Simple session with one Python process per user + threads for operations
    Optimized for current hardware constraints (1 vCPU, 4GB RAM)
    """
    
    def __init__(self, username: str):
        self.username = username
        self.created_at = time.time()
        self.last_activity = time.time()
        
        # Single Python interpreter per user
        self.python_process = None
        self.python_lock = threading.RLock()
        
        # Thread management (limit to 2 concurrent operations per user)
        self.active_threads = {}  # operation_type -> thread
        self.max_threads_per_user = 2  # Limit for current hardware
        
        # Communication with Python process
        self.input_queue = queue.Queue()
        self.output_buffer = []
        self.output_lock = threading.Lock()
        
        # Resource limits for 1 vCPU, 4GB RAM
        self.memory_limit_mb = 80  # 80MB per user process (conservative)
        self.max_execution_time = 60  # 1 minute max per script
        self.idle_timeout = 1200  # 20 minutes idle timeout
        
        # Initialize Python process
        self._init_python_process()
        
    def _init_python_process(self):
        """Initialize persistent Python process for this user"""
        try:
            user_workspace = self._get_user_workspace()
            
            self.python_process = subprocess.Popen(
                [sys.executable, '-u', '-i'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=0,
                cwd=user_workspace,
                env=dict(os.environ, PYTHONPATH=user_workspace)
            )
            
            # Initialize environment
            init_script = f"""
import sys, os, traceback
import time as _time
os.chdir('{user_workspace}')
print(">>> Python session ready for {self.username}")
"""
            
            self._write_to_python(init_script)
            time.sleep(0.1)  # Let initialization complete
            
            logger.info(f"Python process initialized for {self.username} (PID: {self.python_process.pid})")
            
        except Exception as e:
            logger.error(f"Failed to initialize Python process for {self.username}: {e}")
            self.python_process = None
    
    def _get_user_workspace(self) -> str:
        """Get user workspace directory"""
        base_path = os.getenv('IDE_DATA_PATH', '/mnt/efs/pythonide-data')
        workspace = os.path.join(base_path, 'ide', 'Local', self.username)
        os.makedirs(workspace, exist_ok=True)
        return workspace
    
    def _write_to_python(self, code: str):
        """Write code to Python process stdin"""
        if not self.python_process or self.python_process.poll() is not None:
            return False
        
        try:
            with self.python_lock:
                self.python_process.stdin.write(code + '\n')
                self.python_process.stdin.flush()
                return True
        except Exception as e:
            logger.error(f"Failed to write to Python process: {e}")
            return False
    
    def _read_python_output(self, timeout=2.0) -> str:
        """Read output from Python process with timeout"""
        if not self.python_process:
            return ""
        
        output_lines = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                if self.python_process.stdout.readable():
                    try:
                        # Non-blocking read attempt
                        line = self.python_process.stdout.readline()
                        if line:
                            output_lines.append(line.rstrip())
                        else:
                            break
                    except:
                        break
                else:
                    time.sleep(0.01)
            
            return '\n'.join(output_lines)
            
        except Exception as e:
            logger.error(f"Error reading Python output: {e}")
            return f"Error reading output: {e}"
    
    def execute_script(self, script_content: str, file_path: str, cmd_id: str, callback=None):
        """Execute script in a thread"""
        
        if len(self.active_threads) >= self.max_threads_per_user:
            if callback:
                callback({
                    'cmd_id': cmd_id,
                    'status': 'error',
                    'output': 'Too many concurrent operations. Please wait.',
                    'type': 'script_result'
                })
            return
        
        def script_thread():
            try:
                logger.info(f"Executing script for {self.username}: {file_path}")
                
                # Prepare script execution
                safe_script = f"""
try:
    # User script execution
{chr(10).join('    ' + line for line in script_content.split(chr(10)))}
except Exception as e:
    print(f"Error: {{e}}")
    import traceback
    traceback.print_exc()
"""
                
                # Execute script
                if self._write_to_python(safe_script):
                    time.sleep(0.1)  # Brief pause for execution
                    output = self._read_python_output(timeout=self.max_execution_time)
                    
                    if callback:
                        callback({
                            'cmd_id': cmd_id,
                            'status': 'completed',
                            'output': output,
                            'type': 'script_result'
                        })
                else:
                    if callback:
                        callback({
                            'cmd_id': cmd_id,
                            'status': 'error',
                            'output': 'Failed to execute script - Python process not available',
                            'type': 'script_result'
                        })
                
                self.last_activity = time.time()
                
            except Exception as e:
                logger.error(f"Script execution error for {self.username}: {e}")
                if callback:
                    callback({
                        'cmd_id': cmd_id,
                        'status': 'error',
                        'output': f'Execution error: {e}',
                        'type': 'script_result'
                    })
            finally:
                # Remove from active threads
                if 'script' in self.active_threads:
                    del self.active_threads['script']
        
        # Start execution thread
        thread = threading.Thread(target=script_thread, daemon=True)
        self.active_threads['script'] = thread
        thread.start()
    
    def execute_repl_command(self, command: str, cmd_id: str, callback=None):
        """Execute REPL command in a thread"""
        
        if len(self.active_threads) >= self.max_threads_per_user:
            if callback:
                callback({
                    'cmd_id': cmd_id,
                    'status': 'error',
                    'output': 'Too many concurrent operations. Please wait.',
                    'type': 'repl_result'
                })
            return
        
        def repl_thread():
            try:
                logger.debug(f"REPL command for {self.username}: {command[:50]}...")
                
                # Execute command in existing Python process
                if self._write_to_python(command):
                    output = self._read_python_output(timeout=30)  # Longer timeout for REPL
                    
                    if callback:
                        callback({
                            'cmd_id': cmd_id,
                            'status': 'completed',
                            'output': output,
                            'type': 'repl_result'
                        })
                else:
                    if callback:
                        callback({
                            'cmd_id': cmd_id,
                            'status': 'error',
                            'output': 'REPL not available',
                            'type': 'repl_result'
                        })
                
                self.last_activity = time.time()
                
            except Exception as e:
                logger.error(f"REPL error for {self.username}: {e}")
                if callback:
                    callback({
                        'cmd_id': cmd_id,
                        'status': 'error',
                        'output': f'REPL error: {e}',
                        'type': 'repl_result'
                    })
            finally:
                if 'repl' in self.active_threads:
                    del self.active_threads['repl']
        
        # Start REPL thread
        thread = threading.Thread(target=repl_thread, daemon=True)
        self.active_threads['repl'] = thread
        thread.start()
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            if self.python_process and self.python_process.poll() is None:
                process = psutil.Process(self.python_process.pid)
                return process.memory_info().rss / 1024 / 1024
            return 0.0
        except:
            return 0.0
    
    def is_idle(self) -> bool:
        """Check if session is idle"""
        return (time.time() - self.last_activity) > self.idle_timeout
    
    def cleanup(self):
        """Clean up session resources"""
        logger.info(f"Cleaning up session for {self.username}")
        
        # Wait for threads to complete (with timeout)
        for thread_type, thread in list(self.active_threads.items()):
            try:
                thread.join(timeout=2.0)
            except:
                pass
        
        self.active_threads.clear()
        
        # Terminate Python process
        if self.python_process and self.python_process.poll() is None:
            try:
                self.python_process.terminate()
                self.python_process.wait(timeout=5)
            except:
                try:
                    self.python_process.kill()
                except:
                    pass
        
        logger.info(f"Session cleanup complete for {self.username}")


class SimpleSessionManager:
    """
    Simple session manager for current hardware constraints
    Supports 8-10 concurrent users on 1 vCPU, 4GB RAM
    """
    
    def __init__(self):
        self.sessions: Dict[str, SimpleUserSession] = {}
        self.session_lock = threading.RLock()
        
        # Limits for current hardware
        self.max_concurrent_users = 10  # Conservative limit for 1 vCPU
        self.max_memory_total_mb = 3000  # Reserve 1GB for server
        
        # Start background services
        self._start_cleanup_service()
        self._start_monitoring_service()
        
        logger.info(f"SimpleSessionManager initialized (max {self.max_concurrent_users} users)")
    
    def get_or_create_session(self, username: str) -> Optional[SimpleUserSession]:
        """Get existing session or create new one"""
        with self.session_lock:
            # Check if user already has session
            if username in self.sessions:
                session = self.sessions[username]
                session.last_activity = time.time()
                return session
            
            # Check limits
            if len(self.sessions) >= self.max_concurrent_users:
                logger.warning(f"Max concurrent users reached ({self.max_concurrent_users}), rejecting {username}")
                return None
            
            # Check total memory usage
            total_memory = sum(session.get_memory_usage() for session in self.sessions.values())
            if total_memory > self.max_memory_total_mb:
                logger.warning(f"Memory limit reached ({total_memory:.1f}MB), rejecting {username}")
                return None
            
            # Create new session
            try:
                session = SimpleUserSession(username)
                self.sessions[username] = session
                logger.info(f"Created session for {username} ({len(self.sessions)}/{self.max_concurrent_users} users)")
                return session
            
            except Exception as e:
                logger.error(f"Failed to create session for {username}: {e}")
                return None
    
    def remove_session(self, username: str):
        """Remove user session"""
        with self.session_lock:
            if username in self.sessions:
                session = self.sessions[username]
                session.cleanup()
                del self.sessions[username]
                logger.info(f"Removed session for {username} ({len(self.sessions)} users remaining)")
    
    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        with self.session_lock:
            total_memory = 0.0
            total_threads = 0
            session_stats = []
            
            for username, session in self.sessions.items():
                memory = session.get_memory_usage()
                threads = len(session.active_threads)
                
                total_memory += memory
                total_threads += threads
                
                session_stats.append({
                    'username': username,
                    'memory_mb': round(memory, 1),
                    'active_threads': threads,
                    'uptime_minutes': round((time.time() - session.created_at) / 60, 1),
                    'idle_minutes': round((time.time() - session.last_activity) / 60, 1)
                })
            
            return {
                'active_users': len(self.sessions),
                'total_memory_mb': round(total_memory, 1),
                'total_threads': total_threads,
                'sessions': session_stats,
                'limits': {
                    'max_users': self.max_concurrent_users,
                    'max_memory_mb': self.max_memory_total_mb
                },
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'timestamp': time.time()
                }
            }
    
    def _start_cleanup_service(self):
        """Start background cleanup for idle sessions"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(300)  # Check every 5 minutes
                    
                    with self.session_lock:
                        idle_users = []
                        for username, session in self.sessions.items():
                            if session.is_idle():
                                idle_users.append(username)
                        
                        for username in idle_users:
                            self.remove_session(username)
                        
                        if idle_users:
                            logger.info(f"Cleaned up {len(idle_users)} idle sessions")
                
                except Exception as e:
                    logger.error(f"Cleanup service error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("Session cleanup service started")
    
    def _start_monitoring_service(self):
        """Start background monitoring"""
        def monitoring_loop():
            while True:
                try:
                    time.sleep(60)  # Monitor every minute
                    
                    stats = self.get_system_stats()
                    
                    # Log warnings if approaching limits
                    if stats['active_users'] > self.max_concurrent_users * 0.8:
                        logger.warning(f"High user count: {stats['active_users']}/{self.max_concurrent_users}")
                    
                    if stats['total_memory_mb'] > self.max_memory_total_mb * 0.8:
                        logger.warning(f"High memory usage: {stats['total_memory_mb']:.1f}MB/{self.max_memory_total_mb}MB")
                    
                    if stats['system']['cpu_percent'] > 80:
                        logger.warning(f"High CPU usage: {stats['system']['cpu_percent']:.1f}%")
                
                except Exception as e:
                    logger.error(f"Monitoring service error: {e}")
        
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        logger.info("System monitoring service started")

# Global session manager instance
session_manager = SimpleSessionManager()