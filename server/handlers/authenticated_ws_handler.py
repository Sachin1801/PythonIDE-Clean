#!/usr/bin/env python3

import json
import datetime
import threading
from tornado import websocket
from tornado import ioloop
import tornado.web
from tornado import gen, httputil
from typing import Optional, Awaitable, Union, Any
from utils.log import logger
from common.msg import req_put
from .handler_info import HandlerInfo
import sys
import os
from collections import defaultdict
from time import time
from .websocket_keepalive import WebSocketKeepaliveMixin

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager
from command.secure_file_manager import SecureFileManager
from command.file_sync import file_sync


class RateLimiter:
    """Rate limiting for user actions"""

    def __init__(self):
        # Track different types of actions separately
        self.executions = defaultdict(list)  # Code executions
        self.file_ops = defaultdict(list)  # File operations
        self.messages = defaultdict(list)  # General messages

    def check_execution_limit(self, username, limit=10, window=60):
        """Check if user can execute code (10 per minute default)"""
        return self._check_limit(self.executions, username, limit, window)

    def check_file_ops_limit(self, username, limit=100, window=60):
        """Check if user can perform file operations (100 per minute default)"""
        return self._check_limit(self.file_ops, username, limit, window)

    def check_message_limit(self, username, limit=300, window=60):
        """Check general message rate limit (300 per minute default)"""
        return self._check_limit(self.messages, username, limit, window)

    def _check_limit(self, tracker, username, limit, window):
        """Generic rate limit check"""
        now = time()
        # Remove old entries outside the time window
        tracker[username] = [t for t in tracker[username] if now - t < window]

        # Check if limit exceeded
        if len(tracker[username]) >= limit:
            return False

        # Add current timestamp
        tracker[username].append(now)
        return True

    def get_wait_time(self, tracker, username, window=60):
        """Get seconds until next action allowed"""
        if not tracker[username]:
            return 0

        now = time()
        oldest = min(tracker[username])
        wait = window - (now - oldest)
        return max(0, wait)


# Global rate limiter instance
rate_limiter = RateLimiter()


class WebSocketConnectionRegistry:
    """Global registry to track active WebSocket connections per user (single-session enforcement)"""

    def __init__(self):
        self._connections = {}  # username -> handler
        self._lock = threading.Lock()

    def register(self, username, handler):
        """
        Register new WebSocket connection for user.
        If user already has active connection, terminate the old one.
        """
        with self._lock:
            # Check if user already has active connection
            if username in self._connections:
                old_handler = self._connections[username]
                logger.info(f"User {username} logging in from new location. Terminating old session.")

                # Send termination message to old connection
                try:
                    old_handler.write_message(
                        json.dumps(
                            {
                                "type": "session_terminated",
                                "reason": "logged_in_elsewhere",
                                "message": "Another login for the same account detected. You have been logged out.",
                            }
                        )
                    )
                    # Close old connection gracefully
                    old_handler.close(code=4001, reason="Logged in from another location")
                except Exception as e:
                    logger.error(f"Error terminating old connection for {username}: {e}")

            # Register new connection
            self._connections[username] = handler
            logger.info(f"Registered WebSocket connection for {username}")

    def unregister(self, username):
        """Remove WebSocket connection for user"""
        with self._lock:
            if username in self._connections:
                del self._connections[username]
                logger.info(f"Unregistered WebSocket connection for {username}")

    def get_handler(self, username):
        """Get active WebSocket handler for username"""
        with self._lock:
            return self._connections.get(username)

    def terminate_session(self, username, reason="inactivity"):
        """Terminate active WebSocket connection for user"""
        with self._lock:
            if username in self._connections:
                handler = self._connections[username]
                try:
                    handler.write_message(
                        json.dumps(
                            {
                                "type": "session_terminated",
                                "reason": reason,
                                "message": f"Session terminated due to {reason}.",
                            }
                        )
                    )
                    handler.close(code=4002, reason=f"Session terminated: {reason}")
                except Exception as e:
                    logger.error(f"Error terminating session for {username}: {e}")

                del self._connections[username]
                logger.info(f"Terminated session for {username} (reason: {reason})")
                return True
        return False

    def terminate_sessions_by_token(self, tokens, reason="logged_in_elsewhere"):
        """
        Terminate WebSocket connections for sessions with given tokens.
        Used for database-level single-session enforcement.
        """
        terminated_count = 0
        with self._lock:
            # Find handlers with matching session tokens
            handlers_to_terminate = []
            for username, handler in list(self._connections.items()):
                if hasattr(handler, "session_id") and handler.session_id in tokens:
                    handlers_to_terminate.append((username, handler))

            # Terminate each matching handler
            for username, handler in handlers_to_terminate:
                try:
                    handler.write_message(
                        json.dumps(
                            {
                                "type": "session_terminated",
                                "reason": reason,
                                "message": "Another login for the same account detected. You have been logged out.",
                            }
                        )
                    )
                    handler.close(code=4001, reason="Logged in from another location")
                    del self._connections[username]
                    terminated_count += 1
                    logger.info(f"Terminated session for {username} (token: {handler.session_id[:8]}...)")
                except Exception as e:
                    logger.error(f"Error terminating connection for {username}: {e}")

        return terminated_count


# Global connection registry instance
ws_connection_registry = WebSocketConnectionRegistry()


class AuthenticatedWebSocketHandler(websocket.WebSocketHandler, WebSocketKeepaliveMixin):
    """WebSocket handler with authentication and secure file operations"""

    def __init__(
        self, application: tornado.web.Application, request: httputil.HTTPServerRequest, **kwargs: Any
    ) -> None:
        super().__init__(application, request, **kwargs)
        self.connected = False
        self.authenticated = False
        self.handler_info = HandlerInfo()

        # Authentication and file management
        self.user_manager = UserManager()
        self.file_manager = SecureFileManager()

        # User session info
        self.username = None
        self.role = None
        self.session_id = None
        self.full_name = None

    @property
    def id(self):
        return id(self)

    def check_origin(self, origin: str) -> bool:
        # Allow connections from localhost for development
        # In production, restrict to your domain
        allowed_origins = [
            "http://localhost:8080",
            "http://localhost:10086",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:10086",
        ]
        # For development, allow all origins
        return True

    def open(self, *args: str, **kwargs: str) -> Optional[Awaitable[None]]:
        self.connected = True
        self.set_nodelay(True)

        # Setup keepalive mechanism
        self.setup_keepalive()

        logger.info(
            f"WebSocket connection established: ip={self.request.remote_ip}, id={self.id}, time={datetime.datetime.now()}"
        )

        # Send authentication request
        self.write_message(json.dumps({"type": "auth_required", "message": "Please authenticate to continue"}))

    def on_close(self) -> None:
        self.connected = False
        self.authenticated = False

        # Cleanup keepalive
        self.cleanup_keepalive()

        # SINGLE-SESSION: Unregister WebSocket connection
        if self.username:
            ws_connection_registry.unregister(self.username)

        # Cleanup REPL handlers if they exist
        if hasattr(self, "repl_handlers"):
            for file_path, handler in self.repl_handlers.items():
                try:
                    if handler and hasattr(handler, "cleanup"):
                        handler.cleanup()
                        logger.info(f"Cleaned up REPL handler for {file_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up REPL handler for {file_path}: {e}")
            self.repl_handlers.clear()

        logger.info(
            f"WebSocket connection closed: ip={self.request.remote_ip}, user={self.username}, time={datetime.datetime.now()}"
        )

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            cmd = data.get("cmd")

            # Handle keepalive pong responses
            if cmd == "pong" or data.get("type") == "pong":
                if hasattr(self, "last_pong_time"):
                    self.last_pong_time = time()
                # AUTO-LOGOUT: Update activity on keepalive pong
                if self.authenticated and self.session_id:
                    self.user_manager.update_session_activity(self.session_id)
                return

            # Handle authentication first
            if cmd == "authenticate":
                self.handle_authentication(data)
            elif not self.authenticated:
                self.write_error("Not authenticated. Please login first.")
            else:
                # AUTO-LOGOUT: Update last_activity on every authenticated message
                if self.session_id:
                    self.user_manager.update_session_activity(self.session_id)

                # Route to appropriate handler based on command
                # Pass the entire message for legacy compatibility
                self.handle_command(cmd, data)

        except json.JSONDecodeError:
            # Fall back to legacy message handling for backward compatibility
            if self.authenticated:
                self._run_callback(req_put, self, message)
            else:
                self.write_error("Not authenticated")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self.write_error(str(e))

    def handle_authentication(self, data):
        """Handle authentication request"""
        session_id = data.get("session_id")

        if not session_id:
            # Try username/password authentication
            username = data.get("username")
            password = data.get("password")

            if username and password:
                result, error = self.user_manager.authenticate(username, password)
                if result:
                    self.authenticated = True
                    self.username = result["username"]
                    self.role = result["role"]
                    self.session_id = result["token"]  # Store the token as session_id
                    self.full_name = result["full_name"]
                    logger.info(f"User authenticated: {self.username} with role: {self.role}")

                    # Sync user files with database
                    try:
                        file_count = file_sync.sync_user_files(result["user_id"], self.username)
                        logger.info(f"Synced {file_count} files for {self.username}")

                        # Create initial files if user directory is empty
                        if file_count == 0:
                            file_sync.create_initial_files(result["user_id"], self.username, self.role)
                    except Exception as e:
                        logger.error(f"Error syncing files for {self.username}: {e}")

                    # SINGLE-SESSION ENFORCEMENT: Database-level invalidation + WebSocket termination
                    # Invalidate all other active sessions for this user in the database
                    other_tokens = self.user_manager.invalidate_other_sessions(result["user_id"], self.session_id)
                    if other_tokens:
                        # Terminate WebSocket connections for those invalidated sessions
                        terminated = ws_connection_registry.terminate_sessions_by_token(other_tokens)
                        logger.info(f"Terminated {terminated} other WebSocket connections for {self.username}")

                    # Register this WebSocket connection (also handles in-memory registry check)
                    ws_connection_registry.register(self.username, self)

                    self.write_message(
                        json.dumps(
                            {
                                "type": "auth_success",
                                "username": self.username,
                                "role": self.role,
                                "session_id": self.session_id,
                                "full_name": self.full_name,
                            }
                        )
                    )
                    logger.info(f"User authenticated: {self.username} ({self.role})")
                    return

            self.write_error("Invalid credentials")
            return

        # Validate existing session
        session = self.user_manager.validate_session(session_id)
        if session:
            self.authenticated = True
            self.username = session["username"]
            self.role = session["role"]
            self.session_id = session_id
            self.full_name = session.get("full_name", session["username"])

            # Sync user files with database
            try:
                file_count = file_sync.sync_user_files(session["user_id"], self.username)
                logger.info(f"Synced {file_count} files for {self.username}")

                # Create initial files if user directory is empty
                if file_count == 0:
                    file_sync.create_initial_files(session["user_id"], self.username, self.role)
            except Exception as e:
                logger.error(f"Error syncing files for {self.username}: {e}")

            # SINGLE-SESSION ENFORCEMENT: Database-level invalidation + WebSocket termination
            # Invalidate all other active sessions for this user in the database
            other_tokens = self.user_manager.invalidate_other_sessions(session["user_id"], self.session_id)
            if other_tokens:
                # Terminate WebSocket connections for those invalidated sessions
                terminated = ws_connection_registry.terminate_sessions_by_token(other_tokens)
                logger.info(f"Terminated {terminated} other WebSocket connections for {self.username}")

            # Register this WebSocket connection (also handles in-memory registry check)
            ws_connection_registry.register(self.username, self)

            self.write_message(
                json.dumps(
                    {"type": "auth_success", "username": self.username, "role": self.role, "full_name": self.full_name}
                )
            )
            logger.info(f"Session validated for: {self.username} ({self.role})")
        else:
            self.write_error("Invalid or expired session")

    def handle_command(self, cmd, data):
        """Route commands to appropriate handlers"""
        logger.info(f"Handling command: '{cmd}' (type: {type(cmd)}) from user: {self.username}")

        # Check general message rate limit first
        if not rate_limiter.check_message_limit(self.username):
            wait_time = rate_limiter.get_wait_time(rate_limiter.messages, self.username)
            self.write_error(f"Rate limit exceeded. Please wait {int(wait_time)} seconds before sending more requests.")
            return

        # Map legacy IDE commands to new secure operations
        ide_commands = {
            "ide_list_projects": self.handle_list_projects,
            "ide_get_project": self.handle_get_project,
            "ide_get_file": self.handle_get_file,
            "ide_write_file": self.handle_write_file,
            "ide_save_file": self.handle_write_file,  # Alias for write
            "ide_create_file": self.handle_create_file,
            "ide_delete_file": self.handle_delete_file,
            "ide_del_file": self.handle_delete_file,  # Alias
            "ide_rename_file": self.handle_rename_file,
            "ide_create_folder": self.handle_create_folder,
            "ide_delete_folder": self.handle_delete_folder,
            "ide_del_folder": self.handle_delete_folder,  # Alias
            "ide_rename_folder": self.handle_rename_folder,
            "ide_create_project": self.handle_create_project,
            "ide_delete_project": self.handle_delete_project,
            "ide_rename_project": self.handle_rename_project,
        }

        if cmd in ide_commands:
            # Check file operations rate limit
            if not rate_limiter.check_file_ops_limit(self.username):
                wait_time = rate_limiter.get_wait_time(rate_limiter.file_ops, self.username)
                self.write_error(f"File operation rate limit exceeded. Please wait {int(wait_time)} seconds.")
                return

            result = ide_commands[cmd](data)
            self.write_message(json.dumps(result))
            return

        # File operations using SecureFileManager
        file_commands = {
            "save_file": self.file_manager.save_file,
            "get_file": self.file_manager.get_file,
            "list_directory": self.file_manager.list_directory,
            "create_directory": self.file_manager.create_directory,
            "delete_file": self.file_manager.delete_file,
            "rename_file": self.file_manager.rename_file,
        }

        if cmd in file_commands:
            # Execute file command with user context
            result = file_commands[cmd](self.username, self.role, data)
            self.write_message(json.dumps({"type": f"{cmd}_result", "cmd": cmd, **result}))

        # Legacy command handling for code execution
        elif cmd in [
            "run",
            "execute",
            "stop",
            "run_python_program",
            "stop_python_program",
            "send_program_input",
            "start_python_repl",
            "stop_python_repl",
        ]:
            # Check execution rate limit for run commands
            if cmd in ["run", "execute", "run_python_program", "start_python_repl"]:
                if not rate_limiter.check_execution_limit(self.username):
                    wait_time = rate_limiter.get_wait_time(rate_limiter.executions, self.username)
                    self.write_error(
                        f"Execution rate limit exceeded (max 10 per minute). Please wait {int(wait_time)} seconds."
                    )
                    return

            # Get the actual data payload
            actual_data = data.get("data", {})

            # Add user context to the actual data
            actual_data["username"] = self.username
            actual_data["role"] = self.role

            # Pass to legacy handler with the correct structure
            message_with_auth = json.dumps(
                {"cmd": cmd, "cmd_id": data.get("cmd_id", data.get("id", 0)), "data": actual_data}
            )
            self._run_callback(req_put, self, message_with_auth)

        else:
            # Pass unrecognized commands to legacy handler (for ide_move_file, ide_move_folder, etc.)
            actual_data = data.get("data", {})
            actual_data["username"] = self.username
            actual_data["role"] = self.role

            message_with_auth = json.dumps(
                {"cmd": cmd, "cmd_id": data.get("cmd_id", data.get("id", 0)), "data": actual_data}
            )
            self._run_callback(req_put, self, message_with_auth)

    def handle_list_projects(self, data):
        """Handle ide_list_projects command - returns available projects for user"""
        import os

        print(f"\n========== HANDLE_LIST_PROJECTS DEBUG ==========")
        print(f"User: {self.username}, Role: {self.role}")
        print(f"IDE base path: {self.file_manager.base_path}")

        if self.role == "professor":
            # Professor can see all top-level directories (scan actual filesystem)
            projects = []
            try:
                if os.path.exists(self.file_manager.base_path):
                    raw_items = os.listdir(self.file_manager.base_path)
                    print(f"Raw directory listing: {raw_items}")
                    for item in raw_items:
                        item_path = os.path.join(self.file_manager.base_path, item)
                        print(f"  Checking item: '{item}' at path: '{item_path}' - isdir: {os.path.isdir(item_path)}")
                        if os.path.isdir(item_path):
                            projects.append(item)
                    projects.sort()  # Keep consistent ordering
                    print(f"Found root directories: {projects}")
                else:
                    # Fallback if ide_base doesn't exist
                    projects = ["Local", "Lecture Notes"]
                    print(f"IDE base doesn't exist, using fallback: {projects}")
            except Exception as e:
                print(f"Error scanning directories: {e}")
                projects = ["Local", "Lecture Notes"]  # Fallback
        else:
            # Students get a curated list: their own Local directory + read-only root folders
            # This prevents them from seeing other students' Local/{other-username} directories
            projects = []
            try:
                if os.path.exists(self.file_manager.base_path):
                    # Always add the student's own Local directory as "Local"
                    student_local_path = os.path.join(self.file_manager.base_path, "Local", self.username)
                    if os.path.exists(student_local_path):
                        projects.append("Local")
                        print(f"Student {self.username}: Added Local project (points to Local/{self.username})")

                    # Scan for other root directories (but exclude the Local container)
                    raw_items = os.listdir(self.file_manager.base_path)
                    print(f"Student scanning for additional root directories: {raw_items}")
                    for item in raw_items:
                        if item == "Local":
                            # Skip the Local container - we already handled the student's personal Local above
                            print(f"  Student skipping 'Local' container to prevent access to other students")
                            continue

                        item_path = os.path.join(self.file_manager.base_path, item)
                        print(
                            f"  Student checking item: '{item}' at path: '{item_path}' - isdir: {os.path.isdir(item_path)}"
                        )
                        if os.path.isdir(item_path):
                            projects.append(item)

                    projects.sort()  # Keep consistent ordering
                    print(f"Student found additional root directories: {[p for p in projects if p != 'Local']}")
                else:
                    # Fallback if ide_base doesn't exist
                    projects = ["Local", "Lecture Notes"]
                    print(f"Student fallback - IDE base doesn't exist: {projects}")
            except Exception as e:
                print(f"Student error scanning directories: {e}")
                projects = ["Local", "Lecture Notes"]  # Fallback
            print(f"Student final projects list: {projects}")

        print(f"Final projects list: {projects}")
        print(f"================================================\n")

        return {"code": 0, "data": projects, "id": data.get("id", 1)}

    def handle_get_project(self, data):
        """Handle ide_get_project command - returns directory tree for a project"""
        project_name = data.get("data", {}).get("projectName", "")

        # Special handling for students accessing "Local" project
        # For students, "Local" project should map to their personal "Local/{username}" directory
        if self.role == "student" and project_name == "Local":
            actual_project_path = f"Local/{self.username}"
            print(f"Student {self.username} requesting 'Local' project, mapping to: {actual_project_path}")
        else:
            actual_project_path = project_name

        # Build file tree for the project
        result = self.build_file_tree(actual_project_path)

        return {"code": 0 if result else -1, "data": result, "id": data.get("id", 1)}

    def build_file_tree(self, project_path):
        """Build a file tree structure for the frontend"""
        import os
        from pathlib import Path
        from common.file_storage import file_storage

        # Validate access
        if not project_path:
            return None

        # For students, ensure they're accessing their own directory
        if self.role == "student":
            if project_path.startswith("Local/"):
                if not project_path.startswith(f"Local/{self.username}"):
                    return None

        # Use the correct storage path (EFS in production, local in dev)
        base_path = Path(self.file_manager.base_path)
        full_path = base_path / project_path

        if not full_path.exists():
            return None

        def build_tree_node(path, name=None):
            """Recursively build tree node"""
            node = {
                "name": name or path.name,
                "path": str(path.relative_to(base_path)),
                "type": "folder" if path.is_dir() else "file",
            }

            if path.is_dir():
                node["children"] = []
                try:
                    for item in sorted(path.iterdir()):
                        if not item.name.startswith("."):  # Skip hidden files
                            child_node = build_tree_node(item)
                            if child_node:
                                node["children"].append(child_node)
                except PermissionError:
                    pass
            else:
                # Add file size and extension
                node["size"] = path.stat().st_size
                node["ext"] = path.suffix[1:] if path.suffix else ""

            return node

        return build_tree_node(full_path, project_path)

    def handle_get_file(self, data):
        """Handle ide_get_file command"""
        request_data = data.get("data", {})
        project_name = request_data.get("projectName", "")
        file_path = request_data.get("filePath", "")

        logger.info(f"handle_get_file: projectName='{project_name}', filePath='{file_path}'")

        # Construct full path from project name and file path
        if project_name and file_path:
            # If filePath already includes project name, use it as is
            if file_path.startswith(project_name):
                full_path = file_path
            else:
                full_path = f"{project_name}/{file_path}"
        else:
            full_path = file_path or request_data.get("path", "")

        logger.info(f"handle_get_file: constructed full_path='{full_path}'")

        # Check if requesting binary file
        is_binary = request_data.get("binary", False)

        # Use secure file manager to get file
        result = self.file_manager.get_file(self.username, self.role, {"path": full_path})

        if result["success"]:
            # Log successful file retrieval
            logger.info(f"File retrieved successfully: {full_path}, size: {len(result.get('content', ''))}")

            # Handle binary files
            if is_binary and result.get("binary"):
                return {
                    "code": 0,
                    "data": {"content": result["content"], "binary": True, "mime_type": result.get("mime_type")},
                    "id": data.get("id", 1),
                }
            else:
                response = {"code": 0, "data": result["content"], "id": data.get("id", 1)}
                logger.info(f"Sending text file response for {full_path}")
                return response
        else:
            logger.warning(f"Failed to get file {full_path}: {result.get('error')}")
            return {"code": -1, "msg": result.get("error", "Failed to get file"), "id": data.get("id", 1)}

    def handle_write_file(self, data):
        """Handle ide_write_file command"""
        file_data = data.get("data", {})
        project_name = file_data.get("projectName", "")
        file_path = file_data.get("filePath", "")
        # Frontend sends 'fileData' not 'content'
        content = file_data.get("fileData") or file_data.get("content", "")

        # Construct full path from project name and file path
        if project_name and file_path:
            # If filePath already includes project name, use it as is
            if file_path.startswith(project_name):
                full_path = file_path
            else:
                full_path = f"{project_name}/{file_path}"
        else:
            full_path = file_path or file_data.get("path", "")

        # Log the save operation
        logger.info(f"Saving file: {full_path}, content_length: {len(content)}")

        # Use secure file manager to save file
        result = self.file_manager.save_file(self.username, self.role, {"path": full_path, "content": content})

        logger.info(f"Save result: {result}")

        # If saving a Python file, terminate any existing REPL to ensure fresh execution
        if result["success"] and full_path.endswith(".py"):
            try:
                from command.repl_registry import repl_registry

                # Convert relative path to absolute path for REPL registry
                import os
                from common.config import Config

                abs_path = os.path.normpath(os.path.join(self.file_manager.base_path, full_path))
                terminated = repl_registry.terminate_repl(self.username, abs_path)
                if terminated:
                    logger.info(f"Terminated existing REPL for {abs_path} after file save")
            except Exception as e:
                logger.warning(f"Failed to terminate REPL for {full_path}: {e}")

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "File saved") if not result["success"] else "File saved",
            "id": data.get("id", 1),
        }

    def handle_create_file(self, data):
        """Handle ide_create_file command"""
        file_data = data.get("data", {})

        # Extract path from frontend format
        parent_path = file_data.get("parentPath", "")
        file_name = file_data.get("fileName", "")

        # Construct full path
        if parent_path and file_name:
            file_path = f"{parent_path}/{file_name}"
        else:
            file_path = file_data.get("path", "")  # Fallback to direct path

        if not file_path:
            return {"code": -1, "msg": "No file path specified", "id": data.get("id", 1)}

        logger.info(f"Creating file: {file_path} for user: {self.username}")

        # Create empty file
        result = self.file_manager.save_file(self.username, self.role, {"path": file_path, "content": ""})

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "File created") if not result["success"] else "File created",
            "id": data.get("id", 1),
        }

    def handle_delete_file(self, data):
        """Handle ide_delete_file or ide_del_file command"""
        request_data = data.get("data", {})
        project_name = request_data.get("projectName", "")
        file_path = request_data.get("filePath", "")

        # Construct full path from project name and file path
        if project_name and file_path:
            # If filePath already includes project name, use it as is
            if file_path.startswith(project_name):
                full_path = file_path
            else:
                full_path = f"{project_name}/{file_path}"
        else:
            full_path = file_path or request_data.get("path", "")

        result = self.file_manager.delete_file(self.username, self.role, {"path": full_path})

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "File deleted") if not result["success"] else "File deleted",
            "id": data.get("id", 1),
        }

    def handle_rename_file(self, data):
        """Handle ide_rename_file command"""
        file_data = data.get("data", {})
        project_name = file_data.get("projectName", "")
        old_path_input = file_data.get("oldPath", "")
        new_name = file_data.get("newName", "")

        # Construct full old path
        if project_name and old_path_input:
            if old_path_input.startswith(project_name):
                old_full_path = old_path_input
            else:
                old_full_path = f"{project_name}/{old_path_input}"
        else:
            old_full_path = old_path_input

        # Construct new path (keep same directory, just change name)
        if new_name and old_full_path:
            import os

            dir_path = os.path.dirname(old_full_path)
            if dir_path:
                new_full_path = f"{dir_path}/{new_name}"
            else:
                new_full_path = new_name
        else:
            new_full_path = file_data.get("newPath", "")

        result = self.file_manager.rename_file(
            self.username, self.role, {"old_path": old_full_path, "new_path": new_full_path}
        )

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "File renamed") if not result["success"] else "File renamed",
            "id": data.get("id", 1),
        }

    def handle_create_folder(self, data):
        """Handle ide_create_folder command"""
        request_data = data.get("data", {})
        project_name = request_data.get("projectName", "")
        folder_path = request_data.get("folderPath", "") or request_data.get("path", "")
        is_root_creation = request_data.get("isRootCreation", False)

        print(f"\n========== HANDLE_CREATE_FOLDER DEBUG ==========")
        print(f"Raw request_data: {request_data}")
        print(f"project_name: '{project_name}'")
        print(f"folder_path: '{folder_path}'")
        print(f"is_root_creation: {is_root_creation}")

        # Construct full path
        if is_root_creation:
            # For root creation, folder_path is the folder name and should be created at root level
            full_path = folder_path
            print(f"ROOT CREATION - full_path: '{full_path}'")
        elif project_name and folder_path:
            if folder_path.startswith(project_name):
                full_path = folder_path
            else:
                full_path = f"{project_name}/{folder_path}"
            print(f"PROJECT CREATION - full_path: '{full_path}'")
        else:
            full_path = folder_path
            print(f"DEFAULT CREATION - full_path: '{full_path}'")

        print(f"Final full_path to create: '{full_path}'")
        print(f"================================================\n")

        result = self.file_manager.create_directory(self.username, self.role, {"path": full_path})

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "Folder created") if not result["success"] else "Folder created",
            "id": data.get("id", 1),
        }

    def handle_delete_folder(self, data):
        """Handle ide_delete_folder or ide_del_folder command"""
        request_data = data.get("data", {})
        project_name = request_data.get("projectName", "")
        folder_path = request_data.get("folderPath", "") or request_data.get("path", "")

        # Construct full path
        if project_name and folder_path:
            if folder_path.startswith(project_name):
                full_path = folder_path
            else:
                full_path = f"{project_name}/{folder_path}"
        else:
            full_path = folder_path

        # Use delete_file which handles directories too
        result = self.file_manager.delete_file(self.username, self.role, {"path": full_path})

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "Folder deleted") if not result["success"] else "Folder deleted",
            "id": data.get("id", 1),
        }

    def handle_rename_folder(self, data):
        """Handle ide_rename_folder command"""
        folder_data = data.get("data", {})
        project_name = folder_data.get("projectName", "")
        old_path_input = folder_data.get("oldPath", "")
        new_name = folder_data.get("newName", "")

        # Construct full old path
        if project_name and old_path_input:
            if old_path_input.startswith(project_name):
                old_full_path = old_path_input
            else:
                old_full_path = f"{project_name}/{old_path_input}"
        else:
            old_full_path = old_path_input

        # Construct new path
        if new_name and old_full_path:
            import os

            dir_path = os.path.dirname(old_full_path)
            if dir_path:
                new_full_path = f"{dir_path}/{new_name}"
            else:
                new_full_path = new_name
        else:
            new_full_path = folder_data.get("newPath", "")

        result = self.file_manager.rename_file(
            self.username, self.role, {"old_path": old_full_path, "new_path": new_full_path}
        )

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "Folder renamed") if not result["success"] else "Folder renamed",
            "id": data.get("id", 1),
        }

    def handle_create_project(self, data):
        """Handle ide_create_project command"""
        request_data = data.get("data", {})
        project_name = request_data.get("projectName", "")

        # Students can only create under their own directory
        if self.role == "student":
            full_path = f"Local/{self.username}/{project_name}"
        else:
            full_path = project_name

        result = self.file_manager.create_directory(self.username, self.role, {"path": full_path})

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "Project created") if not result["success"] else "Project created",
            "id": data.get("id", 1),
        }

    def handle_delete_project(self, data):
        """Handle ide_delete_project command"""
        request_data = data.get("data", {})
        project_name = request_data.get("projectName", "")

        # Use delete_file which handles directories
        result = self.file_manager.delete_file(self.username, self.role, {"path": project_name})

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "Project deleted") if not result["success"] else "Project deleted",
            "id": data.get("id", 1),
        }

    def handle_rename_project(self, data):
        """Handle ide_rename_project command"""
        request_data = data.get("data", {})
        old_name = request_data.get("oldName", "")
        new_name = request_data.get("newName", "")

        result = self.file_manager.rename_file(self.username, self.role, {"old_path": old_name, "new_path": new_name})

        return {
            "code": 0 if result["success"] else -1,
            "msg": result.get("error", "Project renamed") if not result["success"] else "Project renamed",
            "id": data.get("id", 1),
        }

    def write_error(self, error_message):
        """Send error message to client"""
        self.write_message(json.dumps({"type": "error", "message": error_message}))

    def write_message(self, message, binary=False):
        """Override to ensure connection is still open"""
        if self.connected:
            try:
                super().write_message(message, binary)
            except Exception as e:
                logger.error(f"Error writing message: {e}")

    @staticmethod
    def _run_callback(callback, *args, **kwargs):
        """Run callback with error handling"""
        try:
            result = callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Callback error: {e}")
            return None
        else:
            if result is not None:
                result = gen.convert_yielded(result)
                ioloop.IOLoop.current().add_future(result, lambda f: f.result())
            return result
