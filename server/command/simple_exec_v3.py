#!/usr/bin/env python3
"""
Simple Execution Engine V3 - Using Python's code module
Clean implementation using Python's built-in InteractiveConsole
"""

import subprocess
import threading
import time
import os
import sys
import json
import asyncio
import select
import pty
import re
import code
import io
import contextlib
from queue import Queue, Empty
import signal
import traceback
from typing import Optional, Dict, Any
import tempfile
import resource
import builtins

from command.exec_protocol import (
    MessageType, ExecutionState, create_message,
    debug_log, set_debug_mode
)


class InteractiveREPLConsole(code.InteractiveConsole):
    """Custom InteractiveConsole that sends output to WebSocket"""

    def __init__(self, locals, executor):
        super().__init__(locals=locals)
        self.executor = executor
        self.output_buffer = io.StringIO()

    def write(self, data):
        """Override write to capture output"""
        if data:
            # Send to WebSocket (includes infinite loop check)
            self.executor.send_message(MessageType.STDOUT, data)
            # Also buffer it
            self.output_buffer.write(data)

    def raw_input(self, prompt=""):
        """Override raw_input to handle input via WebSocket"""
        if prompt:
            self.executor.send_message(MessageType.INPUT_REQUEST, prompt)

        # Wait for input from WebSocket
        self.executor.waiting_for_input = True
        input_value = None

        try:
            # Wait up to 5 minutes for user input
            input_value = self.executor.input_queue.get(timeout=300)
            self.executor.waiting_for_input = False

            # Don't echo the input - the user already sees it in the input field
            
            self.executor.send_message(MessageType.STDOUT, input_value + "\n")
            # Standard Python input() doesn't echo either
            return input_value

        except Empty:
            self.executor.waiting_for_input = False
            raise EOFError("No input received")

    def push(self, line):
        """Override push to track activity"""
        self.executor.last_activity = time.time()
        return super().push(line)


class SimpleExecutorV3(threading.Thread):
    """
    Enhanced executor using Python's code module for proper REPL
    """

    def __init__(self, cmd_id: str, client, event_loop,
                 script_path: Optional[str] = None, username: Optional[str] = None, role: Optional[str] = None):
        super().__init__()
        self.cmd_id = cmd_id
        self.client = client
        self.event_loop = event_loop
        self.script_path = script_path
        self.username = username
        self.role = role or "student"  # Default to student if not provided

        # Process management
        self.process = None
        self.master_fd = None
        self.alive = True
        self.state = ExecutionState.IDLE

        # Input handling
        self.input_queue = Queue()
        self.waiting_for_input = False
        self.last_activity = time.time()

        # Timing
        self.start_time = None
        self.script_timeout = 30
        self.repl_timeout = 300  # 5 minutes for REPL

        # REPL console
        self.console = None
        self.namespace = {}

        # Debug mode
        set_debug_mode(os.environ.get("DEBUG_MODE", "false").lower() == "true")

        # Thread management - CRITICAL for cleanup
        self.daemon = True
        self._stop_event = threading.Event()  # For clean shutdown
        self._cleanup_done = False  # Prevent double cleanup
        self._lock_released = False  # Track if execution lock has been released
        self._lock_release_mutex = threading.Lock()  # Mutex to protect lock release

        # ===== INFINITE LOOP DETECTION VARIABLES =====
        # Layer 1: Output rate limiting
        self.output_start_time = time.time()
        self.output_line_count = 0
        self.MAX_LINES_PER_SECOND = 100  # Kill if > 100 lines/sec
        self.last_rate_check = time.time()

        # Layer 2: Total output limiting
        self.total_output_lines = 0
        self.MAX_TOTAL_LINES = 10000  # Kill at 10,000 lines

        # Layer 3: Identical line detection
        self.last_output_line = None
        self.identical_line_count = 0
        self.MAX_IDENTICAL_LINES = 500  # Kill if same line 500x

        # Fast flood detection (catches immediate spam)
        self.flood_check_buffer = []
        self.flood_check_time = time.time()

        # ===== RESOURCE LIMITS =====
        self.MEMORY_LIMIT_MB = 128  # 128MB memory limit
        self.CPU_TIME_LIMIT = 10    # 10 seconds CPU time (different from wall time)

        # print(f"[SimpleExecutorV3-INIT] Thread ID: {threading.get_ident()}")
        # print(f"[SimpleExecutorV3-INIT] cmd_id: {cmd_id}, script: {script_path}")
        # print(f"[SimpleExecutorV3-INIT] username: {username}")
        # print(f"[SimpleExecutorV3-INIT] alive: {self.alive}, state: {self.state}")
        # print(f"[SimpleExecutorV3-INIT] Infinite loop detection enabled:"
            #   f" rate_limit={self.MAX_LINES_PER_SECOND}/sec,"
            #   f" total_limit={self.MAX_TOTAL_LINES},"
            #   f" identical_limit={self.MAX_IDENTICAL_LINES}")

    def send_message(self, msg_type: MessageType, data: Any):
        """Send message to frontend via WebSocket"""
        # CRITICAL: Check if we're still alive before sending
        if not self.alive:
            print(f"[SimpleExecutorV3-SEND] WARNING: Attempt to send message after executor stopped")
            print(f"[SimpleExecutorV3-SEND] cmd_id: {self.cmd_id}, msg_type: {msg_type}, alive: {self.alive}")
            return

        # Update heartbeat when sending messages (shows executor is active)
        if hasattr(self, 'username') and hasattr(self, 'script_path') and self.username and self.script_path:
            try:
                from .execution_lock_manager import execution_lock_manager
                execution_lock_manager.update_heartbeat(self.username, self.script_path)
            except (ImportError, AttributeError, Exception) as e:
                # Don't fail if heartbeat update fails - log for debugging
                print(f"[SimpleExecutorV3-HEARTBEAT] Non-critical error updating heartbeat: {e}")
                pass

        # Check for infinite loop on STDOUT/STDERR messages
        if msg_type in [MessageType.STDOUT, MessageType.STDERR] and data:
            self._check_infinite_loop(data)

        message = create_message(self.cmd_id, msg_type, data)
        message["cmd"] = "repl_output"

        # write_message is synchronous, so we need to schedule it properly
        def _send():
            try:
                if self.client and hasattr(self.client, 'write_message'):
                    self.client.write_message(json.dumps(message))
                else:
                    print(f"[SimpleExecutorV3-SEND] ERROR: Client not available or invalid")
            except Exception as e:
                print(f"[SimpleExecutorV3-SEND] ERROR sending message: {e}")
                print(f"[SimpleExecutorV3-SEND] cmd_id: {self.cmd_id}, msg_type: {msg_type}")

        # Schedule the synchronous write_message to run in the event loop
        try:
            self.event_loop.call_soon_threadsafe(_send)
        except Exception as e:
            print(f"[SimpleExecutorV3-SEND] ERROR scheduling message: {e}")

        if msg_type != MessageType.DEBUG:
            data_preview = str(data)[:100] if data else "None"
            # print(f"[SimpleExecutorV3-SEND] Sent {msg_type.value}: {data_preview}")

    def _release_execution_lock_once(self, context="unknown"):
        """
        Centralized method to release execution lock exactly once.
        Uses mutex to prevent race conditions and double-release.

        Args:
            context: String describing where the release is being called from (for debugging)

        Returns:
            bool: True if lock was released, False if already released or error
        """
        with self._lock_release_mutex:
            # Check if already released while holding the mutex
            if self._lock_released:
                print(f"[SimpleExecutorV3-LOCK] Lock already released, skipping ({context})")
                return False

            # Check if we have the necessary attributes
            if not (hasattr(self, 'username') and hasattr(self, 'script_path') and
                    self.username and self.script_path):
                print(f"[SimpleExecutorV3-LOCK] Missing required attributes for lock release ({context})")
                return False

            try:
                from .execution_lock_manager import execution_lock_manager
                execution_lock_manager.release_execution_lock(self.username, self.script_path, self.cmd_id)
                self._lock_released = True  # Mark as released AFTER successful release
                print(f"[SimpleExecutorV3-LOCK] ✅ Successfully released lock ({context})")
                return True
            except Exception as e:
                print(f"[SimpleExecutorV3-LOCK] ❌ Failed to release lock ({context}): {e}")
                # Don't set _lock_released to True on error - allow retry
                return False

    def handle_input(self, text: str):
        """Handle input from WebSocket"""
        # print(f"[SimpleExecutorV3] Received input: {text}")
        self.input_queue.put(text)

    def send_input(self, text: str):
        """Alias for handle_input to match expected interface"""
        return self.handle_input(text)

    def run(self):
        """Main execution thread"""
        print(f"[SimpleExecutorV3-RUN] ===== THREAD STARTED =====")
        # print(f"[SimpleExecutorV3-RUN] Thread ID: {threading.get_ident()}")
        # print(f"[SimpleExecutorV3-RUN] cmd_id: {self.cmd_id}")
        # print(f"[SimpleExecutorV3-RUN] script_path: {self.script_path}")
        # print(f"[SimpleExecutorV3-RUN] alive: {self.alive}, state: {self.state}")

        self.start_time = time.time()

        try:
            # Set resource limits before execution
            self.set_resource_limits()

            # Configure matplotlib for headless operation (server environment)
            # Must be set BEFORE any matplotlib imports in user code
            os.environ['MPLBACKEND'] = 'Agg'

            # Configure matplotlib cache directory to prevent permission errors
            # Matplotlib tries to write font cache to ~/.matplotlib/ which may not be writable
            # Set cache to a temp directory that gets cleaned up after execution
            import tempfile
            self.mpl_cache_dir = tempfile.mkdtemp(prefix='mpl_cache_')
            os.environ['MPLCONFIGDIR'] = self.mpl_cache_dir

            # Create namespace for execution
            self.namespace = {
                '__name__': '__main__',
                '__doc__': None,
                'input': self.repl_input  # Custom input function
            }
            # print(f"[SimpleExecutorV3-RUN] Namespace created")

            # Execute script if provided
            if self.script_path:
                # print(f"[SimpleExecutorV3-RUN] Executing script: {self.script_path}")
                self.execute_script()

                # CRITICAL: Release execution lock after script completes, BEFORE REPL starts
                # This allows the same file to be run again while REPL is still active
                self._release_execution_lock_once("after script completion, before REPL")
            else:
                # print(f"[SimpleExecutorV3-RUN] No script provided, starting REPL directly")
                pass  # Keep the block valid even with commented prints

            # Start REPL (whether script was run or not)
            if self.alive:  # Only start REPL if still alive
                # print(f"[SimpleExecutorV3-RUN] Starting REPL mode")
                self.start_repl()
            else:
                print(f"[SimpleExecutorV3-RUN] Skipping REPL (alive=False)")

        except Exception as e:
            print(f"[SimpleExecutorV3-RUN] ERROR: Execution failed")
            print(f"[SimpleExecutorV3-RUN] Exception: {e}")
            traceback.print_exc()

            if self.alive:  # Only send error if still alive
                self.send_message(MessageType.ERROR, {
                    "error": f"Execution failed: {str(e)}",
                    "traceback": traceback.format_exc()
                })

        finally:
            # print(f"[SimpleExecutorV3-RUN] Entering cleanup phase")
            self.cleanup()
            # print(f"[SimpleExecutorV3-RUN] ===== THREAD ENDED =====")

    def set_resource_limits(self):
        """Set memory and CPU resource limits for the execution"""
        # NOTE: Resource limits in threads affect the entire process
        # For true isolation, we'd need to use subprocess or containers
        # For now, we'll rely on:
        # 1. 3-second timeout (wall clock time)
        # 2. Output rate limiting (prevents memory exhaustion from output)
        # 3. Total output limiting (10,000 lines max)

        # Log that resource limits are enforced through other mechanisms
        print(f"[RESOURCE-LIMITS] Using timeout (3s) and output limits for resource protection")
        # In production, consider using Docker containers with memory limits
        # or subprocess with ulimit for true process isolation

    def repl_input(self, prompt=""):
        """Custom input function for use in scripts and REPL"""
        if prompt:
            self.send_message(MessageType.INPUT_REQUEST, prompt)

        self.waiting_for_input = True
        try:
            # Wait for input from WebSocket
            input_value = self.input_queue.get(timeout=300)
            self.waiting_for_input = False

            # Don't echo the input - the user already sees it in the input field
            # self.send_message(MessageType.STDOUT, input_value + "\n")
            # Standard Python input() doesn't echo either
            return input_value

        except Empty:
            self.waiting_for_input = False
            raise EOFError("No input received")

    def execute_script(self):
        """Execute the script file with strict 3-second timeout"""
        # print(f"[SimpleExecutorV3-SCRIPT] ===== SCRIPT EXECUTION START =====")
        # print(f"[SimpleExecutorV3-SCRIPT] Path: {self.script_path}")
        # print(f"[SimpleExecutorV3-SCRIPT] File exists: {os.path.exists(self.script_path)}")

        self.state = ExecutionState.SCRIPT_RUNNING
        script_start_time = time.time()
        self.timeout_occurred = False  # Flag for timeout

        # Create a trace function for timeout checking
        def trace_function(frame, event, arg):
            """Trace function to interrupt execution on timeout"""
            if self.timeout_occurred or not self.alive:
                raise KeyboardInterrupt("Script terminated by timeout")
            return trace_function

        # Set up a timer to kill script after 3 seconds
        def timeout_killer():
            time.sleep(3.0)  # Wait exactly 3 seconds
            if self.state == ExecutionState.SCRIPT_RUNNING and not self.waiting_for_input:
                elapsed = time.time() - script_start_time
                print(f"[SCRIPT-TIMEOUT] Script exceeded 3-second limit (elapsed: {elapsed:.2f}s)")

                # Kill the script
                self._kill_for_timeout("Script execution time limit exceeded (3 seconds)")

        # Start the timeout thread
        timeout_thread = threading.Thread(target=timeout_killer, daemon=True)
        timeout_thread.start()
        # print(f"[SimpleExecutorV3-SCRIPT] Started 3-second timeout monitor")

        try:
            # Read script content
            with open(self.script_path, 'r') as f:
                script_code = f.read()

            # print(f"[SimpleExecutorV3-SCRIPT] Script size: {len(script_code)} bytes")
            # print(f"[SimpleExecutorV3-SCRIPT] First 100 chars: {script_code[:100]}")

            # Get script's directory for file operations
            script_dir = os.path.dirname(os.path.abspath(self.script_path))
            # print(f"[SimpleExecutorV3-SCRIPT] Script directory: {script_dir}")

            # CRITICAL: Actually change working directory for C-level operations
            # Libraries like PIL/Pillow (used by matplotlib) use C's getcwd() which
            # bypasses our Python monkey-patches. We MUST use os.chdir() here.
            # This is safe because each script execution runs in isolation.
            original_cwd = os.getcwd()
            os.chdir(script_dir)
            print(f"[CWD-DEBUG] Changed working directory from {original_cwd} to {script_dir}")

            # Add __file__ and __dir__ to namespace so scripts can access their location
            self.namespace['__file__'] = os.path.abspath(self.script_path)
            self.namespace['__dir__'] = script_dir

            # Store original working directory in namespace for scripts that need it
            # This allows scripts to construct absolute paths without changing global cwd
            self.namespace['__original_cwd__'] = os.getcwd()

            # Security: Validate student file access
            # Students can only access files within their Local/{username}/ directory
            # and can read from other directories (like Lecture Notes) but NOT write to them
            def validate_student_path(path, mode='r', username=None, role=None):
                """
                Validate that a student's file operation respects directory permissions.

                Args:
                    path: File path to validate (absolute or relative)
                    mode: File open mode ('r', 'w', 'a', 'rb', 'wb', etc.)
                    username: Student's username
                    role: User's role ('student' or 'professor')

                Returns:
                    Validated absolute path

                Raises:
                    PermissionError: If student attempts unauthorized access
                """
                # Debug logging to diagnose role issues
                print(f"[VALIDATE-PATH-DEBUG] path={path}, mode={mode}, username={username}, role={role}, role_type={type(role)}")

                # Professors have unrestricted access
                if role == 'professor':
                    print(f"[VALIDATE-PATH-DEBUG] ✅ Professor access granted for {username}")
                    return path

                # Convert to absolute path
                if not os.path.isabs(path):
                    path = os.path.join(script_dir, path)

                # Resolve any .. or . in the path to prevent directory traversal
                path = os.path.abspath(path)

                # Get the base data directory (e.g., /mnt/efs/pythonide-data or /app/server/projects)
                base_data_path = os.environ.get('IDE_DATA_PATH', '/mnt/efs/pythonide-data')

                # Normalize base path (resolve symlinks, remove trailing slashes)
                base_data_path = os.path.realpath(base_data_path)
                path = os.path.realpath(path)

                # Ensure path is within the data directory
                if not path.startswith(base_data_path):
                    raise PermissionError(f"Access denied: Path outside IDE workspace: {path}")

                # Get relative path from base (e.g., "ide/Local/sa9082/test.py" or "Local/sa9082/test.py")
                rel_path = os.path.relpath(path, base_data_path)

                # Normalize path separators and remove leading "ide/" if present
                # (Docker uses /app/server/projects/ide/Local/..., AWS uses /mnt/efs/pythonide-data/ide/Local/...)
                rel_path = rel_path.replace('\\', '/')
                if rel_path.startswith('ide/'):
                    rel_path = rel_path[4:]  # Remove 'ide/' prefix

                # Determine if this is a write operation
                is_write_mode = False
                if isinstance(mode, str):
                    # Check for write modes: 'w', 'a', 'w+', 'r+', 'wb', 'ab', etc.
                    is_write_mode = any(m in mode for m in ['w', 'a', '+'])

                # For students, enforce directory restrictions
                if role == 'student' and username:
                    student_prefix = f"Local/{username}/"

                    # Students can READ from anywhere in the workspace
                    if not is_write_mode:
                        return path

                    # Students can WRITE only within their Local/{username}/ directory
                    if not rel_path.startswith(student_prefix):
                        raise PermissionError(
                            f"Permission denied: Students can only write to their own directory (Local/{username}/). "
                            f"Attempted write to: {rel_path}"
                        )

                return path

            # Monkey-patch open() to use script directory as base for relative paths
            # AND validate student permissions for absolute paths
            original_open = builtins.open
            def contextualized_open(file, mode='r', *args, **kwargs):
                # Handle file descriptors (not paths)
                if not isinstance(file, str):
                    return original_open(file, mode, *args, **kwargs)

                # If path is relative, make it relative to script directory
                if not os.path.isabs(file):
                    file = os.path.join(script_dir, file)

                # Validate student permissions (raises PermissionError if denied)
                file = validate_student_path(file, mode, self.username, self.role)

                return original_open(file, mode, *args, **kwargs)

            # Monkey-patch os.getcwd() to return script directory
            # This helps libraries like pandas that use getcwd() for relative paths
            def contextualized_getcwd():
                return script_dir

            # Monkey-patch os.path.abspath to resolve relative to script dir
            original_abspath = os.path.abspath
            def contextualized_abspath(path):
                if not os.path.isabs(path):
                    # Make relative paths relative to script directory
                    path = os.path.join(script_dir, path)
                return original_abspath(path)

            # Monkey-patch os.path.exists to check relative to script dir
            original_exists = os.path.exists
            def contextualized_exists(path):
                if isinstance(path, str) and not os.path.isabs(path):
                    path = os.path.join(script_dir, path)
                return original_exists(path)

            # Monkey-patch os.path.isfile to check relative to script dir
            original_isfile = os.path.isfile
            def contextualized_isfile(path):
                if isinstance(path, str) and not os.path.isabs(path):
                    path = os.path.join(script_dir, path)
                return original_isfile(path)

            # Monkey-patch os.path.isdir to check relative to script dir
            original_isdir = os.path.isdir
            def contextualized_isdir(path):
                if isinstance(path, str) and not os.path.isabs(path):
                    path = os.path.join(script_dir, path)
                return original_isdir(path)

            # Monkey-patch os.listdir to list relative to script dir
            original_listdir = os.listdir
            def contextualized_listdir(path='.'):
                if path == '.' or (isinstance(path, str) and not os.path.isabs(path)):
                    if path == '.':
                        path = script_dir
                    else:
                        path = os.path.join(script_dir, path)
                return original_listdir(path)

            # Monkey-patch os.path.getsize to get size relative to script dir
            original_getsize = os.path.getsize
            def contextualized_getsize(path):
                if isinstance(path, str) and not os.path.isabs(path):
                    path = os.path.join(script_dir, path)
                return original_getsize(path)

            # Monkey-patch os.path.getmtime to get mtime relative to script dir
            original_getmtime = os.path.getmtime
            def contextualized_getmtime(path):
                if isinstance(path, str) and not os.path.isabs(path):
                    path = os.path.join(script_dir, path)
                return original_getmtime(path)

            # Security: Monkey-patch destructive file operations
            # These operations can modify/delete files, so they need permission validation

            # Monkey-patch os.remove (delete files)
            original_remove = os.remove
            def contextualized_remove(path):
                if isinstance(path, str):
                    if not os.path.isabs(path):
                        path = os.path.join(script_dir, path)
                    # Validate as write operation (deleting = writing)
                    path = validate_student_path(path, 'w', self.username, self.role)
                return original_remove(path)

            # Monkey-patch os.rename (rename/move files)
            original_rename = os.rename
            def contextualized_rename(src, dst):
                if isinstance(src, str):
                    if not os.path.isabs(src):
                        src = os.path.join(script_dir, src)
                    # Validate source as write operation (moving from = modifying)
                    src = validate_student_path(src, 'w', self.username, self.role)

                if isinstance(dst, str):
                    if not os.path.isabs(dst):
                        dst = os.path.join(script_dir, dst)
                    # Validate destination as write operation
                    dst = validate_student_path(dst, 'w', self.username, self.role)

                return original_rename(src, dst)

            # Monkey-patch os.mkdir (create directories)
            original_mkdir = os.mkdir
            def contextualized_mkdir(path, *args, **kwargs):
                if isinstance(path, str):
                    if not os.path.isabs(path):
                        path = os.path.join(script_dir, path)
                    # Validate as write operation
                    path = validate_student_path(path, 'w', self.username, self.role)
                return original_mkdir(path, *args, **kwargs)

            # Monkey-patch os.makedirs (create directories recursively)
            original_makedirs = os.makedirs
            def contextualized_makedirs(path, *args, **kwargs):
                if isinstance(path, str):
                    if not os.path.isabs(path):
                        path = os.path.join(script_dir, path)
                    # Validate as write operation
                    path = validate_student_path(path, 'w', self.username, self.role)
                return original_makedirs(path, *args, **kwargs)

            # Monkey-patch os.rmdir (remove empty directory)
            original_rmdir = os.rmdir
            def contextualized_rmdir(path):
                if isinstance(path, str):
                    if not os.path.isabs(path):
                        path = os.path.join(script_dir, path)
                    # Validate as write operation
                    path = validate_student_path(path, 'w', self.username, self.role)
                return original_rmdir(path)

            # Monkey-patch os.open (low-level file descriptor operations)
            # This is CRITICAL for matplotlib/PIL which uses os.open() instead of builtins.open()
            original_os_open = os.open
            def contextualized_os_open(path, flags, mode=0o777, *args, **kwargs):
                """
                Secure wrapper for os.open() - validates file paths for write operations.

                os.open() is used by C libraries like PIL/Pillow (matplotlib's backend).
                It returns a file descriptor (integer), not a file object.

                Args:
                    path: File path
                    flags: os.O_RDONLY, os.O_WRONLY, os.O_RDWR, os.O_CREAT, etc.
                    mode: File permissions (default 0o777)
                """
                print(f"[OS-OPEN-DEBUG] os.open called: path={path}, flags={flags}, username={self.username}, role={self.role}")

                if isinstance(path, str):
                    # Convert relative paths to absolute
                    if not os.path.isabs(path):
                        path = os.path.join(script_dir, path)

                    # Check if this is a write operation
                    # os.O_WRONLY (write-only), os.O_RDWR (read-write), os.O_CREAT (create file)
                    is_write = (flags & os.O_WRONLY) or (flags & os.O_RDWR) or (flags & os.O_CREAT)

                    if is_write:
                        # Professors bypass validation
                        if self.role == 'professor':
                            print(f"[OS-OPEN-DEBUG] Professor bypass for write: {path}")
                        else:
                            # Validate write operations for students
                            path = validate_student_path(path, 'w', self.username, self.role)
                            print(f"[OS-OPEN-DEBUG] Student write validated: {path}")
                    else:
                        # Read operations - just contextualize the path
                        print(f"[OS-OPEN-DEBUG] Read operation: {path}")

                return original_os_open(path, flags, mode, *args, **kwargs)

            # Apply monkey patches in the namespace
            self.namespace['open'] = contextualized_open

            # Create a patched os module for the namespace
            import types
            import sys
            patched_os = types.ModuleType('os')
            # Copy all attributes from original os
            for attr in dir(os):
                if not attr.startswith('_'):
                    setattr(patched_os, attr, getattr(os, attr))

            # Create a patched os.path submodule
            patched_path = types.ModuleType('path')
            # Copy all attributes from original os.path
            for attr in dir(os.path):
                if not attr.startswith('_'):
                    setattr(patched_path, attr, getattr(os.path, attr))

            # Override specific path functions
            patched_path.abspath = contextualized_abspath
            patched_path.exists = contextualized_exists
            patched_path.isfile = contextualized_isfile
            patched_path.isdir = contextualized_isdir
            patched_path.getsize = contextualized_getsize
            patched_path.getmtime = contextualized_getmtime

            # Override specific os functions
            patched_os.getcwd = contextualized_getcwd
            patched_os.listdir = contextualized_listdir
            patched_os.path = patched_path

            # Override destructive file operations with security validation
            patched_os.remove = contextualized_remove
            patched_os.rename = contextualized_rename
            patched_os.mkdir = contextualized_mkdir
            patched_os.makedirs = contextualized_makedirs
            patched_os.rmdir = contextualized_rmdir
            patched_os.open = contextualized_os_open  # Critical for matplotlib/PIL

            # Security: Monkey-patch pathlib.Path operations
            # pathlib provides an object-oriented interface to file operations
            from pathlib import Path as OriginalPath

            class SecurePath(type(OriginalPath())):
                """Secure wrapper for pathlib.Path with permission validation"""

                def __new__(cls, *args, **kwargs):
                    # Create the path object
                    if args and isinstance(args[0], str):
                        path_str = args[0]
                        # Convert relative paths to absolute based on script_dir
                        if not os.path.isabs(path_str):
                            path_str = os.path.join(script_dir, path_str)
                        args = (path_str,) + args[1:]
                    return super().__new__(cls, *args, **kwargs)

                def open(self, mode='r', *args, **kwargs):
                    # Validate permissions before opening
                    validated_path = validate_student_path(str(self), mode, self._username, self._role)
                    return OriginalPath(validated_path).open(mode, *args, **kwargs)

                def write_text(self, data, *args, **kwargs):
                    # Validate as write operation
                    validated_path = validate_student_path(str(self), 'w', self._username, self._role)
                    return OriginalPath(validated_path).write_text(data, *args, **kwargs)

                def write_bytes(self, data, *args, **kwargs):
                    # Validate as write operation
                    validated_path = validate_student_path(str(self), 'wb', self._username, self._role)
                    return OriginalPath(validated_path).write_bytes(data, *args, **kwargs)

                def mkdir(self, *args, **kwargs):
                    # Validate as write operation
                    validated_path = validate_student_path(str(self), 'w', self._username, self._role)
                    return OriginalPath(validated_path).mkdir(*args, **kwargs)

                def rmdir(self, *args, **kwargs):
                    # Validate as write operation
                    validated_path = validate_student_path(str(self), 'w', self._username, self._role)
                    return OriginalPath(validated_path).rmdir(*args, **kwargs)

                def unlink(self, *args, **kwargs):
                    # Validate as write operation (delete file)
                    validated_path = validate_student_path(str(self), 'w', self._username, self._role)
                    return OriginalPath(validated_path).unlink(*args, **kwargs)

                def rename(self, target, *args, **kwargs):
                    # Validate both source and destination
                    validate_student_path(str(self), 'w', self._username, self._role)
                    target_str = str(target)
                    if not os.path.isabs(target_str):
                        target_str = os.path.join(script_dir, target_str)
                    validated_target = validate_student_path(target_str, 'w', self._username, self._role)
                    return OriginalPath(str(self)).rename(validated_target)

                def replace(self, target, *args, **kwargs):
                    # Validate both source and destination
                    validate_student_path(str(self), 'w', self._username, self._role)
                    target_str = str(target)
                    if not os.path.isabs(target_str):
                        target_str = os.path.join(script_dir, target_str)
                    validated_target = validate_student_path(target_str, 'w', self._username, self._role)
                    return OriginalPath(str(self)).replace(validated_target)

            # Store username and role in the SecurePath class for access in methods
            SecurePath._username = self.username
            SecurePath._role = self.role

            # Create patched pathlib module
            import pathlib
            patched_pathlib = types.ModuleType('pathlib')
            # Copy all attributes from original pathlib
            for attr in dir(pathlib):
                if not attr.startswith('_'):
                    setattr(patched_pathlib, attr, getattr(pathlib, attr))

            # Override Path class
            patched_pathlib.Path = SecurePath

            # Store original modules
            original_pathlib_module = sys.modules.get('pathlib')

            # Security: Monkey-patch pandas DataFrame.to_csv and read_csv
            # Pandas uses C-level file operations that bypass our open() patches
            try:
                import pandas as pd

                # Store original pandas functions
                original_to_csv = pd.DataFrame.to_csv
                original_read_csv = pd.read_csv

                # Create wrapped version of to_csv that validates path
                def secure_to_csv(df_self, path_or_buf=None, *args, **kwargs):
                    if isinstance(path_or_buf, str):
                        # Validate path before allowing write
                        validated_path = validate_student_path(path_or_buf, 'w', self.username, self.role)
                        path_or_buf = validated_path
                    return original_to_csv(df_self, path_or_buf, *args, **kwargs)

                # Create wrapped version of read_csv that validates path
                def secure_read_csv(filepath_or_buffer, *args, **kwargs):
                    if isinstance(filepath_or_buffer, str):
                        # Validate path (read mode is allowed)
                        validated_path = validate_student_path(filepath_or_buffer, 'r', self.username, self.role)
                        filepath_or_buffer = validated_path
                    return original_read_csv(filepath_or_buffer, *args, **kwargs)

                # Replace pandas functions with secure versions
                pd.DataFrame.to_csv = secure_to_csv
                pd.read_csv = secure_read_csv

                # Store in namespace so student imports get patched version
                self.namespace['__original_pandas_to_csv__'] = original_to_csv
                self.namespace['__original_pandas_read_csv__'] = original_read_csv

            except ImportError:
                # Pandas not installed, skip patching
                pass

            # Security: Monkey-patch matplotlib Figure.savefig and pyplot.savefig
            # Matplotlib uses PIL/Pillow and C-level file operations that bypass open() patches
            try:
                import matplotlib
                import matplotlib.pyplot as plt
                import matplotlib.figure

                # Store original matplotlib functions
                original_figure_savefig = matplotlib.figure.Figure.savefig
                original_pyplot_savefig = plt.savefig

                # Create wrapped version of Figure.savefig that validates path
                def secure_figure_savefig(fig_self, fname, *args, **kwargs):
                    """Secure wrapper for Figure.savefig that validates file paths"""
                    print(f"[MATPLOTLIB-DEBUG] Figure.savefig called: fname={fname}, username={self.username}, role={self.role}")
                    if isinstance(fname, str):
                        # Note: matplotlib also accepts file-like objects (io.BytesIO, etc.)
                        # which don't need validation

                        # Convert relative paths to absolute based on script directory
                        if not os.path.isabs(fname):
                            fname = os.path.join(script_dir, fname)

                        # CRITICAL: Normalize the path to resolve any .. or .
                        fname = os.path.normpath(fname)

                        # For professors, skip validation but still use absolute path
                        if self.role == 'professor':
                            print(f"[MATPLOTLIB-DEBUG] Professor bypass - saving to: {fname}")
                        else:
                            # Validate path for students
                            fname = validate_student_path(fname, 'w', self.username, self.role)
                            print(f"[MATPLOTLIB-DEBUG] Student validated_path={fname}")

                        print(f"[MATPLOTLIB-DEBUG] Final save path: {fname}")
                    return original_figure_savefig(fig_self, fname, *args, **kwargs)

                # Create wrapped version of pyplot.savefig that validates path
                def secure_pyplot_savefig(fname, *args, **kwargs):
                    """Secure wrapper for pyplot.savefig that validates file paths"""
                    print(f"[MATPLOTLIB-DEBUG] pyplot.savefig called: fname={fname}, username={self.username}, role={self.role}")
                    if isinstance(fname, str):
                        # Convert relative paths to absolute based on script directory
                        if not os.path.isabs(fname):
                            fname = os.path.join(script_dir, fname)

                        # CRITICAL: Normalize the path to resolve any .. or .
                        fname = os.path.normpath(fname)

                        # For professors, skip validation but still use absolute path
                        if self.role == 'professor':
                            print(f"[MATPLOTLIB-DEBUG] Professor bypass - saving to: {fname}")
                        else:
                            # Validate path for students
                            fname = validate_student_path(fname, 'w', self.username, self.role)
                            print(f"[MATPLOTLIB-DEBUG] Student validated_path={fname}")

                        print(f"[MATPLOTLIB-DEBUG] Final save path: {fname}")
                    return original_pyplot_savefig(fname, *args, **kwargs)

                # Replace matplotlib functions with secure versions
                matplotlib.figure.Figure.savefig = secure_figure_savefig
                plt.savefig = secure_pyplot_savefig

                # CRITICAL: Update sys.modules so student imports get patched version
                # Without this, "import matplotlib.pyplot as plt" in student code
                # gets a fresh pyplot module that bypasses our security patches
                sys.modules['matplotlib.figure'].Figure.savefig = secure_figure_savefig
                sys.modules['matplotlib.pyplot'].savefig = secure_pyplot_savefig

                # Store in namespace for restoration
                self.namespace['__original_figure_savefig__'] = original_figure_savefig
                self.namespace['__original_pyplot_savefig__'] = original_pyplot_savefig

            except ImportError:
                # Matplotlib not installed, skip patching
                pass

            # Store original os module to restore later
            original_os_module = sys.modules.get('os')
            original_os_path_module = sys.modules.get('os.path')

            # Replace os and pathlib modules in sys.modules so imports get our patched versions
            sys.modules['os'] = patched_os
            sys.modules['os.path'] = patched_path
            sys.modules['pathlib'] = patched_pathlib

            # CRITICAL: Patch PIL's internal os reference if it was already imported
            # PIL/Pillow (used by matplotlib) may have cached the original os module
            try:
                import PIL.Image as _pil_image
                if hasattr(_pil_image, 'os'):
                    _pil_image.os = patched_os
            except ImportError:
                pass  # PIL not installed, skip

            self.namespace['os'] = patched_os
            self.namespace['pathlib'] = patched_pathlib
            self.namespace['__original_os_module__'] = original_os_module
            self.namespace['__original_os_path_module__'] = original_os_path_module
            self.namespace['__original_pathlib_module__'] = original_pathlib_module

            # Compile and execute in namespace
            compiled_code = compile(script_code, self.script_path, 'exec')

            # Capture stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            try:
                sys.stdout = stdout_buffer
                sys.stderr = stderr_buffer

                # Set trace function for timeout checking
                sys.settrace(trace_function)

                try:
                    # Execute the script (trace function will interrupt if timeout)
                    exec(compiled_code, self.namespace)
                finally:
                    # Always clear trace function
                    sys.settrace(None)

                # Script completed successfully - mark as SCRIPT_COMPLETE
                self.state = ExecutionState.SCRIPT_COMPLETE
                elapsed = time.time() - script_start_time
                # print(f"[SimpleExecutorV3-SCRIPT] Script completed in {elapsed:.2f} seconds")

                # Send any output
                stdout_text = stdout_buffer.getvalue()
                stderr_text = stderr_buffer.getvalue()

                if stdout_text:
                    self.send_message(MessageType.STDOUT, stdout_text)
                if stderr_text:
                    self.send_message(MessageType.STDERR, stderr_text)

                # Report variables loaded (disabled for cleaner output)
                # user_vars = [k for k in self.namespace.keys()
                #             if not k.startswith('_') and k != 'input']
                # if user_vars:
                #     var_msg = f"\n🎯 Script variables loaded into REPL: {', '.join(user_vars)}\n"
                #     self.send_message(MessageType.STDOUT, var_msg)
                #     print(f"[SimpleExecutorV3-SCRIPT] Variables loaded: {user_vars}")

                # print(f"[SimpleExecutorV3-SCRIPT] Script executed successfully in {elapsed:.2f}s")

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                # Restore original working directory
                os.chdir(original_cwd)
                print(f"[CWD-DEBUG] Restored working directory to {original_cwd}")

        except KeyboardInterrupt:
            # This is from our timeout killer
            print(f"[SimpleExecutorV3-SCRIPT] Script interrupted by timeout")
            # Restore working directory even on timeout
            try:
                os.chdir(original_cwd)
                print(f"[CWD-DEBUG] Restored working directory to {original_cwd} (after timeout)")
            except:
                pass  # If restoration fails, continue anyway
            # The error message was already sent by _kill_for_timeout
            self.alive = False
            self.state = ExecutionState.TERMINATED
            # Don't start REPL after timeout
            return

        except Exception as e:
            print(f"[SimpleExecutorV3-SCRIPT] ERROR: Script execution failed")
            print(f"[SimpleExecutorV3-SCRIPT] Exception: {e}")
            traceback.print_exc()

            # Restore working directory even on error
            try:
                os.chdir(original_cwd)
                print(f"[CWD-DEBUG] Restored working directory to {original_cwd} (after error)")
            except:
                pass  # If restoration fails, continue anyway

            # Only send error if not already terminated
            if self.state != ExecutionState.TERMINATED:
                self.send_message(MessageType.ERROR, {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })

            # Mark as not alive to prevent REPL from starting
            self.alive = False
            print(f"[SimpleExecutorV3-SCRIPT] Set alive=False due to error")
            # Don't start REPL if script had errors
            raise

        finally:
            # print(f"[SimpleExecutorV3-SCRIPT] ===== SCRIPT EXECUTION END =====")
            pass  # Keep the block valid even with commented prints

    def start_repl(self):
        """Start the interactive REPL"""
        # print(f"[SimpleExecutorV3-REPL] ===== REPL START =====")
        # print(f"[SimpleExecutorV3-REPL] alive: {self.alive}, state: {self.state}")

        if not self.alive:
            print(f"[SimpleExecutorV3-REPL] Not starting REPL (alive=False)")
            return

        self.state = ExecutionState.REPL_ACTIVE

        # Create custom console
        self.console = InteractiveREPLConsole(self.namespace, self)
        # print(f"[SimpleExecutorV3-REPL] Console created")

        # Send REPL ready message
        self.send_message(MessageType.REPL_READY, {"prompt": ">>>"})
        # print(f"[SimpleExecutorV3-REPL] REPL ready message sent")

        # REPL loop
        iteration = 0
        while self.alive and self.state == ExecutionState.REPL_ACTIVE and not self._stop_event.is_set():
            # Check for timeout
            if time.time() - self.last_activity > self.repl_timeout:
                print(f"[SimpleExecutorV3] REPL timeout")
                self.send_message(MessageType.STDOUT, "\n⏰ REPL session timed out\n")
                break

            # Check every 10 iterations for debugging
            if iteration % 10 == 0:
                # print(f"[SimpleExecutorV3-REPL] Loop iteration {iteration}, alive: {self.alive}, stop_event: {self._stop_event.is_set()}")
                pass  # Keep the block valid even with commented prints

            iteration += 1

            # Wait for input
            if not self.waiting_for_input:
                try:
                    # Get command from queue
                    command = self.input_queue.get(timeout=0.1)
                    self.last_activity = time.time()

                    # print(f"[SimpleExecutorV3-REPL] Received command: {command[:50]}...")

                    # Handle special commands
                    if command.strip() in ['exit()', 'quit()', 'exit', 'quit']:
                        # print(f"[SimpleExecutorV3-REPL] Exit command received")
                        self.send_message(MessageType.STDOUT, "\nGoodbye!\n")
                        break

                    # Execute in console
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    stdout_buffer = io.StringIO()
                    stderr_buffer = io.StringIO()

                    try:
                        sys.stdout = stdout_buffer
                        sys.stderr = stderr_buffer

                        # Push line to console
                        more_input_needed = self.console.push(command)

                        # Get output
                        stdout_text = stdout_buffer.getvalue()
                        stderr_text = stderr_buffer.getvalue()

                        if stdout_text:
                            self.send_message(MessageType.STDOUT, stdout_text)
                        if stderr_text:
                            self.send_message(MessageType.STDERR, stderr_text)

                        # Send appropriate prompt
                        if more_input_needed:
                            self.send_message(MessageType.STDOUT, "... ")
                        else:
                            self.console.resetbuffer()
                            self.send_message(MessageType.STDOUT, ">>> ")

                    finally:
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr

                except Empty:
                    # No input available, continue waiting
                    continue
                except Exception as e:
                    print(f"[SimpleExecutorV3] REPL error: {e}")
                    self.send_message(MessageType.ERROR, {
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    })
                    self.send_message(MessageType.STDOUT, ">>> ")
            else:
                # Waiting for input() response
                time.sleep(0.1)

        print(f"[SimpleExecutorV3-REPL] ===== REPL END =====")

    def stop(self):
        """Stop the executor - CRITICAL for preventing frozen state"""
        print(f"[SimpleExecutorV3-STOP] ===== STOP REQUESTED =====")
        print(f"[SimpleExecutorV3-STOP] cmd_id: {self.cmd_id}")
        print(f"[SimpleExecutorV3-STOP] Current state: {self.state}")
        print(f"[SimpleExecutorV3-STOP] Thread alive: {self.is_alive()}")
        print(f"[SimpleExecutorV3-STOP] self.alive: {self.alive}")

        # Set flags to stop execution
        self.alive = False
        self.state = ExecutionState.TERMINATED
        self._stop_event.set()

        # For script running, mark timeout to interrupt trace function
        if self.state == ExecutionState.SCRIPT_RUNNING:
            self.timeout_occurred = True

        # Release execution lock if not already released (only relevant for scripts stopped mid-execution)
        self._release_execution_lock_once("stop() method")

        # Wake up any waiting input
        if self.waiting_for_input:
            print(f"[SimpleExecutorV3-STOP] Interrupting input wait")
            self.input_queue.put("")  # Send empty input to unblock

        # Clear input queue
        cleared_count = 0
        while not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
                cleared_count += 1
            except Empty:
                break

        if cleared_count > 0:
            print(f"[SimpleExecutorV3-STOP] Cleared {cleared_count} items from input queue")

        # If in REPL mode, try to interrupt the console
        if self.console and self.state in (ExecutionState.REPL_RUNNING, ExecutionState.REPL_READY):
            print(f"[SimpleExecutorV3-STOP] Attempting to stop REPL console")
            # The console will check self.alive in its push() method

        print(f"[SimpleExecutorV3-STOP] Stop completed")

    def _check_infinite_loop(self, output_text: str):
        """
        Check for infinite loop patterns in output
        Implements 3 layers of protection
        """
        if not output_text or not self.alive:
            return

        lines = output_text.split('\n')
        line_count = len(lines)

        # Update counters
        self.output_line_count += line_count
        self.total_output_lines += line_count

        # Layer 1: Output Rate Limiting (100 lines/sec)
        current_time = time.time()
        elapsed_since_start = current_time - self.output_start_time

        # Check rate every 0.5 seconds to avoid too frequent checks
        if current_time - self.last_rate_check >= 0.5 and elapsed_since_start > 0.1:
            rate = self.output_line_count / elapsed_since_start

            if rate > self.MAX_LINES_PER_SECOND:
                print(f"[INFINITE-LOOP] RATE LIMIT EXCEEDED: {rate:.1f} lines/sec > {self.MAX_LINES_PER_SECOND}")
                self._kill_for_infinite_loop(
                    f"Output rate limit exceeded: {rate:.1f} lines/sec (limit: {self.MAX_LINES_PER_SECOND}/sec)"
                )
                return

            self.last_rate_check = current_time

            # Log rate for debugging (only when high)
            if rate > 50:
                # print(f"[INFINITE-LOOP] High output rate: {rate:.1f} lines/sec")
                pass  # Keep the block valid even with commented prints

        # Layer 2: Total Output Limit (10,000 lines)
        if self.total_output_lines > self.MAX_TOTAL_LINES:
            print(f"[INFINITE-LOOP] TOTAL LIMIT EXCEEDED: {self.total_output_lines} > {self.MAX_TOTAL_LINES}")
            self._kill_for_infinite_loop(
                f"Total output limit exceeded: {self.total_output_lines} lines (limit: {self.MAX_TOTAL_LINES})"
            )
            return

        # Layer 3: Identical Line Detection (500x repeats)
        for line in lines:
            if not line.strip():  # Skip empty lines
                continue

            if line == self.last_output_line:
                self.identical_line_count += 1

                if self.identical_line_count >= self.MAX_IDENTICAL_LINES:
                    print(f"[INFINITE-LOOP] IDENTICAL LINES: '{line[:50]}...' repeated {self.identical_line_count} times")
                    self._kill_for_infinite_loop(
                        f"Identical line repeated {self.identical_line_count} times: '{line[:100]}...'"
                    )
                    return

                # Log when getting close to limit
                if self.identical_line_count > 0 and self.identical_line_count % 100 == 0:
                    # print(f"[INFINITE-LOOP] Warning: '{line[:30]}...' repeated {self.identical_line_count} times")
                    pass  # Keep the block valid even with commented prints
            else:
                # Reset counter when line changes
                self.last_output_line = line
                self.identical_line_count = 1

        # Layer 4: Fast Flood Detection (catches immediate bursts)
        # If we get > 4KB of data with > 50 lines in < 0.5 seconds, it's likely spam
        if len(output_text) >= 4000 and line_count >= 50:
            flood_elapsed = current_time - self.flood_check_time
            if flood_elapsed < 0.5:
                print(f"[INFINITE-LOOP] FLOOD DETECTED: {len(output_text)} bytes, {line_count} lines in {flood_elapsed:.2f}s")
                self._kill_for_infinite_loop(
                    f"Flood detected: {line_count} lines in {flood_elapsed:.2f} seconds"
                )
                return
            # Reset flood check timer after 0.5 seconds
            self.flood_check_time = current_time

    def _kill_for_infinite_loop(self, reason: str):
        """Kill the process due to detected infinite loop"""
        print(f"[INFINITE-LOOP-KILL] Terminating process: {reason}")

        # Send error message to user
        error_msg = f"\n⚠️ PROCESS TERMINATED: Infinite loop detected!\n"
        error_msg += f"Reason: {reason}\n"
        error_msg += f"\nCommon causes:\n"
        error_msg += f"  • while True: without break condition\n"
        error_msg += f"  • for loop with excessive iterations\n"
        error_msg += f"  • Recursive function without base case\n"
        error_msg += f"\nPlease review your code and add proper loop termination conditions.\n"

        # Send error to console
        self.send_message(MessageType.ERROR, {
            "error": "Infinite loop detected",
            "traceback": error_msg
        })

        # Force stop
        self.alive = False
        self.state = ExecutionState.TERMINATED
        self._stop_event.set()

        # If in REPL, exit it
        if self.console:
            try:
                # Send interrupt to break out of any running code
                os.kill(os.getpid(), signal.SIGINT)
            except (OSError, ProcessLookupError) as e:
                # Process might have already terminated
                print(f"[SimpleExecutorV3-TIMEOUT] Could not send interrupt signal: {e}")
                pass

    def _kill_for_timeout(self, reason: str):
        """Kill the script due to timeout (3-second limit)"""
        print(f"[TIMEOUT-KILL] Terminating script: {reason}")

        # Send error message to user
        error_msg = f"\n⏰ SCRIPT TERMINATED: Time limit exceeded!\n"
        # error_msg += f"Reason: {reason}\n"
        # error_msg += f"\nScript execution is limited to 3 seconds.\n"
        # error_msg += f"\nPossible issues:\n"
        # error_msg += f"  • Infinite loop (while True, endless for loop)\n"
        # error_msg += f"  • Very large data processing\n"
        # error_msg += f"  • Recursive function without proper termination\n"
        # error_msg += f"  • Memory-intensive operations (creating huge lists)\n"
        # error_msg += f"\nTip: Use smaller data sets or add loop limits for testing.\n"

        # Send error to console
        self.send_message(MessageType.ERROR, {
            "error": "Script timeout (3 seconds)",
            "traceback": error_msg
        })

        # Force stop the script
        self.alive = False
        self.state = ExecutionState.TERMINATED
        self._stop_event.set()

        # Mark timeout occurred
        self.timeout_occurred = True

    def cleanup(self):
        """Clean up resources - CRITICAL for preventing zombie threads"""
        # print(f"[SimpleExecutorV3-CLEANUP] Starting cleanup")
        # print(f"[SimpleExecutorV3-CLEANUP] cmd_id: {self.cmd_id}")
        # print(f"[SimpleExecutorV3-CLEANUP] cleanup_done: {self._cleanup_done}")

        # Prevent double cleanup
        if self._cleanup_done:
            # print(f"[SimpleExecutorV3-CLEANUP] Already cleaned up, skipping")
            return

        self._cleanup_done = True

        # Restore original os, pathlib, and pandas modules if they were patched
        try:
            import sys
            if '__original_os_module__' in self.namespace:
                if self.namespace['__original_os_module__']:
                    sys.modules['os'] = self.namespace['__original_os_module__']
            if '__original_os_path_module__' in self.namespace:
                if self.namespace['__original_os_path_module__']:
                    sys.modules['os.path'] = self.namespace['__original_os_path_module__']
            if '__original_pathlib_module__' in self.namespace:
                if self.namespace['__original_pathlib_module__']:
                    sys.modules['pathlib'] = self.namespace['__original_pathlib_module__']

            # Restore pandas functions if they were patched
            if '__original_pandas_to_csv__' in self.namespace:
                try:
                    import pandas as pd
                    pd.DataFrame.to_csv = self.namespace['__original_pandas_to_csv__']
                    pd.read_csv = self.namespace['__original_pandas_read_csv__']
                except:
                    pass

            # Restore matplotlib functions if they were patched
            if '__original_figure_savefig__' in self.namespace:
                try:
                    import matplotlib.figure
                    import matplotlib.pyplot as plt
                    matplotlib.figure.Figure.savefig = self.namespace['__original_figure_savefig__']
                    plt.savefig = self.namespace['__original_pyplot_savefig__']
                except:
                    pass
        except Exception as e:
            print(f"[SimpleExecutorV3-CLEANUP] Error restoring os/pathlib/pandas/matplotlib modules: {e}")

        # Clean up matplotlib cache directory
        if hasattr(self, 'mpl_cache_dir') and os.path.exists(self.mpl_cache_dir):
            try:
                import shutil
                shutil.rmtree(self.mpl_cache_dir)
            except Exception as e:
                print(f"[SimpleExecutorV3-CLEANUP] Error removing matplotlib cache dir: {e}")

        # Send completion message if still connected
        if self.alive and self.client:
            duration = time.time() - self.start_time if self.start_time else 0
            # print(f"[SimpleExecutorV3-CLEANUP] Sending completion message, duration: {duration:.2f}s")
            self.send_message(MessageType.COMPLETE, {
                "exit_code": 0,
                "duration": duration
            })

        # Final state update
        self.alive = False
        self.state = ExecutionState.TERMINATED
        self._stop_event.set()

        # Release any execution locks (if not already released)
        self._release_execution_lock_once("cleanup() method")

        # print(f"[SimpleExecutorV3-CLEANUP] Cleanup completed")