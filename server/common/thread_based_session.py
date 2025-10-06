#!/usr/bin/env python3
"""
Thread-Based User Session Architecture
Single process per user with multiple threads for different operations
Much more resource-efficient than multi-process approach
"""

import threading
import subprocess
import time
import queue
import json
import os
import sys
import tempfile
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ThreadType(Enum):
    SCRIPT_EXECUTION = "script_execution"
    REPL_SESSION = "repl_session"
    FILE_OPERATION = "file_operation"
    INTERACTIVE_INPUT = "interactive_input"


@dataclass
class ThreadInfo:
    """Information about a user thread"""

    thread_id: str
    thread_type: ThreadType
    start_time: float
    last_activity: float
    status: str  # 'running', 'idle', 'completed', 'error'
    resource_usage: Dict[str, Any]


class UserSession:
    """
    Single process managing all operations for one user via threads
    Replaces the multi-process approach with thread-based architecture
    """

    def __init__(self, username: str, session_id: str):
        self.username = username
        self.session_id = session_id
        self.created_at = time.time()
        self.last_activity = time.time()

        # Thread management
        self.threads: Dict[str, threading.Thread] = {}
        self.thread_info: Dict[str, ThreadInfo] = {}
        self.active_executions: Dict[str, subprocess.Popen] = {}
        self.thread_lock = threading.RLock()

        # Shared state between threads (for REPL continuity)
        self.python_process = None  # Single Python interpreter process
        self.global_namespace = {}  # Shared variables between script and REPL
        self.execution_history = []

        # Communication queues
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.command_queue = queue.Queue()

        # Resource limits (per user session)
        self.max_memory_mb = 100  # Total memory for all user threads
        self.max_execution_time = 300  # 5 minutes max per script
        self.max_idle_time = 1800  # 30 minutes idle timeout

        # Initialize persistent Python process
        self._initialize_python_process()

        logger.info(f"UserSession created for {username} (session: {session_id})")

    def _initialize_python_process(self):
        """Initialize persistent Python interpreter for this user"""
        try:
            # Create a persistent Python REPL process
            self.python_process = subprocess.Popen(
                [sys.executable, "-u", "-i"],  # Unbuffered, interactive
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=self._get_user_workspace(),
            )

            # Set up the Python environment
            init_commands = [
                "import sys, os, json",
                f"os.chdir('{self._get_user_workspace()}')",
                "print('Python session initialized')",
            ]

            for cmd in init_commands:
                self._send_to_python(cmd)

            logger.info(f"Python process initialized for {self.username} (PID: {self.python_process.pid})")

        except Exception as e:
            logger.error(f"Failed to initialize Python process for {self.username}: {e}")
            self.python_process = None

    def _get_user_workspace(self) -> str:
        """Get user's workspace directory"""
        base_path = os.getenv("IDE_DATA_PATH", "/mnt/efs/pythonide-data")
        return os.path.join(base_path, "ide", "Local", self.username)

    def _send_to_python(self, command: str) -> bool:
        """Send command to persistent Python process"""
        if not self.python_process or self.python_process.poll() is not None:
            logger.error(f"Python process not available for {self.username}")
            return False

        try:
            self.python_process.stdin.write(command + "\n")
            self.python_process.stdin.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to send command to Python process: {e}")
            return False

    def execute_script(self, script_content: str, file_path: str, cmd_id: str) -> str:
        """Execute script in a dedicated thread"""

        def script_execution_thread():
            thread_id = f"script_{cmd_id}"

            try:
                # Register thread
                self._register_thread(thread_id, ThreadType.SCRIPT_EXECUTION)

                # Write script to temporary file
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                    f.write(script_content)
                    temp_script = f.name

                # Execute script in persistent Python process
                exec_command = f"exec(open('{temp_script}').read())"

                if self._send_to_python(exec_command):
                    # Capture output (this would need more sophisticated implementation)
                    output = self._capture_python_output()
                    self._send_result(cmd_id, "success", output)
                else:
                    self._send_result(cmd_id, "error", "Failed to execute script")

                # Cleanup
                os.unlink(temp_script)

            except Exception as e:
                logger.error(f"Script execution error for {self.username}: {e}")
                self._send_result(cmd_id, "error", str(e))
            finally:
                self._unregister_thread(thread_id)

        # Start thread
        thread = threading.Thread(target=script_execution_thread, daemon=True)
        thread.start()

        return cmd_id

    def start_repl_session(self, cmd_id: str) -> str:
        """Start REPL session in a dedicated thread"""

        def repl_thread():
            thread_id = f"repl_{cmd_id}"

            try:
                self._register_thread(thread_id, ThreadType.REPL_SESSION)

                # REPL loop
                while self._is_thread_active(thread_id):
                    try:
                        # Wait for user input
                        user_input = self.input_queue.get(timeout=1.0)

                        if user_input.strip() == "__EXIT_REPL__":
                            break

                        # Send to Python process
                        if self._send_to_python(user_input):
                            output = self._capture_python_output()
                            self.output_queue.put({"type": "repl_output", "content": output, "cmd_id": cmd_id})

                        self._update_thread_activity(thread_id)

                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"REPL error for {self.username}: {e}")
                        break

            finally:
                self._unregister_thread(thread_id)

        # Start thread
        thread = threading.Thread(target=repl_thread, daemon=True)
        thread.start()

        return cmd_id

    def perform_file_operation(self, operation: str, file_path: str, content: str = None, cmd_id: str = None) -> Dict:
        """Perform file operation in a dedicated thread"""

        def file_operation_thread():
            thread_id = f"file_{cmd_id or int(time.time())}"

            try:
                self._register_thread(thread_id, ThreadType.FILE_OPERATION)

                workspace = self._get_user_workspace()
                full_path = os.path.join(workspace, file_path)

                # Ensure path is within user workspace (security)
                if not full_path.startswith(workspace):
                    raise ValueError("Path outside user workspace")

                result = {"success": False, "data": None}

                if operation == "read":
                    if os.path.exists(full_path):
                        with open(full_path, "r") as f:
                            result = {"success": True, "data": f.read()}
                    else:
                        result = {"success": False, "error": "File not found"}

                elif operation == "write":
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w") as f:
                        f.write(content or "")
                    result = {"success": True, "data": "File written successfully"}

                elif operation == "list":
                    if os.path.exists(full_path):
                        files = os.listdir(full_path)
                        result = {"success": True, "data": files}
                    else:
                        result = {"success": False, "error": "Directory not found"}

                self.output_queue.put(
                    {"type": "file_result", "operation": operation, "result": result, "cmd_id": cmd_id}
                )

            except Exception as e:
                logger.error(f"File operation error for {self.username}: {e}")
                self.output_queue.put(
                    {
                        "type": "file_result",
                        "operation": operation,
                        "result": {"success": False, "error": str(e)},
                        "cmd_id": cmd_id,
                    }
                )
            finally:
                self._unregister_thread(thread_id)

        # Start thread
        thread = threading.Thread(target=file_operation_thread, daemon=True)
        thread.start()

        return {"status": "started", "cmd_id": cmd_id}

    def _capture_python_output(self) -> str:
        """Capture output from Python process (simplified implementation)"""
        # This is a simplified version - real implementation would need
        # proper stdout/stderr handling with timeouts
        try:
            # Read available output (non-blocking)
            output = ""
            # Implementation would use select() or similar for non-blocking read
            return output
        except Exception as e:
            return f"Output capture error: {e}"

    def _register_thread(self, thread_id: str, thread_type: ThreadType):
        """Register a new thread"""
        with self.thread_lock:
            current_time = time.time()
            self.threads[thread_id] = threading.current_thread()
            self.thread_info[thread_id] = ThreadInfo(
                thread_id=thread_id,
                thread_type=thread_type,
                start_time=current_time,
                last_activity=current_time,
                status="running",
                resource_usage={"memory_mb": 0, "cpu_percent": 0},
            )
            self.last_activity = current_time

            logger.debug(f"Thread registered: {thread_id} ({thread_type.value}) for {self.username}")

    def _unregister_thread(self, thread_id: str):
        """Unregister a thread"""
        with self.thread_lock:
            if thread_id in self.threads:
                del self.threads[thread_id]
            if thread_id in self.thread_info:
                del self.thread_info[thread_id]

            logger.debug(f"Thread unregistered: {thread_id} for {self.username}")

    def _update_thread_activity(self, thread_id: str):
        """Update thread activity timestamp"""
        with self.thread_lock:
            if thread_id in self.thread_info:
                self.thread_info[thread_id].last_activity = time.time()
                self.last_activity = time.time()

    def _is_thread_active(self, thread_id: str) -> bool:
        """Check if thread should continue running"""
        with self.thread_lock:
            if thread_id not in self.thread_info:
                return False

            thread_info = self.thread_info[thread_id]

            # Check if thread exceeded execution time
            if time.time() - thread_info.start_time > self.max_execution_time:
                return False

            # Check if thread is idle too long
            if time.time() - thread_info.last_activity > self.max_idle_time:
                return False

            return True

    def _send_result(self, cmd_id: str, status: str, content: Any):
        """Send execution result to output queue"""
        self.output_queue.put(
            {
                "type": "execution_result",
                "cmd_id": cmd_id,
                "status": status,
                "content": content,
                "timestamp": time.time(),
            }
        )

    def get_session_stats(self) -> Dict:
        """Get current session statistics"""
        with self.thread_lock:
            active_threads = len(self.threads)
            thread_types = {}

            for thread_info in self.thread_info.values():
                ttype = thread_info.thread_type.value
                thread_types[ttype] = thread_types.get(ttype, 0) + 1

            return {
                "username": self.username,
                "session_id": self.session_id,
                "uptime_seconds": time.time() - self.created_at,
                "idle_seconds": time.time() - self.last_activity,
                "active_threads": active_threads,
                "thread_types": thread_types,
                "python_process_pid": self.python_process.pid if self.python_process else None,
                "python_process_alive": self.python_process and self.python_process.poll() is None,
                "memory_usage_mb": self._estimate_memory_usage(),
                "execution_history_count": len(self.execution_history),
            }

    def _estimate_memory_usage(self) -> float:
        """Estimate session memory usage"""
        try:
            if self.python_process and self.python_process.poll() is None:
                import psutil

                process = psutil.Process(self.python_process.pid)
                return process.memory_info().rss / 1024 / 1024
            return 0.0
        except:
            return 0.0

    def cleanup(self):
        """Cleanup session resources"""
        logger.info(f"Cleaning up session for {self.username}")

        # Stop all threads
        with self.thread_lock:
            for thread_id in list(self.threads.keys()):
                self._unregister_thread(thread_id)

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


class SessionManager:
    """Manages all user sessions with thread-based architecture"""

    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}  # username -> UserSession
        self.session_lock = threading.RLock()

        # Limits for 38 users
        self.max_concurrent_sessions = 38
        self.max_threads_per_session = 5  # script + repl + 3 file operations
        self.max_total_threads = 190  # 38 * 5

        # Start cleanup service
        self._start_cleanup_service()

    def get_or_create_session(self, username: str) -> UserSession:
        """Get existing session or create new one"""
        with self.session_lock:
            if username not in self.sessions:
                if len(self.sessions) >= self.max_concurrent_sessions:
                    raise RuntimeError(f"Maximum concurrent sessions ({self.max_concurrent_sessions}) reached")

                session_id = f"{username}_{int(time.time())}"
                self.sessions[username] = UserSession(username, session_id)

            return self.sessions[username]

    def remove_session(self, username: str):
        """Remove and cleanup user session"""
        with self.session_lock:
            if username in self.sessions:
                session = self.sessions[username]
                session.cleanup()
                del self.sessions[username]
                logger.info(f"Session removed for {username}")

    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        with self.session_lock:
            total_threads = 0
            total_memory = 0.0
            session_stats = []

            for session in self.sessions.values():
                stats = session.get_session_stats()
                session_stats.append(stats)
                total_threads += stats["active_threads"]
                total_memory += stats["memory_usage_mb"]

            return {
                "active_sessions": len(self.sessions),
                "total_threads": total_threads,
                "total_memory_mb": total_memory,
                "average_threads_per_session": total_threads / max(len(self.sessions), 1),
                "sessions": session_stats,
                "limits": {
                    "max_sessions": self.max_concurrent_sessions,
                    "max_threads_per_session": self.max_threads_per_session,
                    "max_total_threads": self.max_total_threads,
                },
            }

    def _start_cleanup_service(self):
        """Start background cleanup service"""

        def cleanup_loop():
            while True:
                try:
                    time.sleep(300)  # Check every 5 minutes
                    self._cleanup_idle_sessions()
                except Exception as e:
                    logger.error(f"Session cleanup error: {e}")

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("Session cleanup service started")

    def _cleanup_idle_sessions(self):
        """Remove idle sessions"""
        with self.session_lock:
            idle_sessions = []

            for username, session in self.sessions.items():
                stats = session.get_session_stats()
                if stats["idle_seconds"] > 3600:  # 1 hour idle
                    idle_sessions.append(username)

            for username in idle_sessions:
                self.remove_session(username)

            if idle_sessions:
                logger.info(f"Cleaned up {len(idle_sessions)} idle sessions")


# Global session manager
session_manager = SessionManager()
