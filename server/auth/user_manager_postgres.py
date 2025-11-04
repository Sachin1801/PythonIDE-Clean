import bcrypt
import secrets
from datetime import datetime, timedelta
import os
import sys
import threading
import time as time_module
import logging

logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database import db_manager
from common.file_storage import file_storage


class UserManager:
    def __init__(self):
        self.db = db_manager

    def create_user(self, username, email, password, full_name, role="student"):
        """Create new user with hashed password"""
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")

        try:
            query = (
                """
                INSERT INTO users (username, email, password_hash, full_name, role) 
                VALUES (%s, %s, %s, %s, %s)
            """
                if self.db.is_postgres
                else """
                INSERT INTO users (username, email, password_hash, full_name, role) 
                VALUES (?, ?, ?, ?, ?)
            """
            )

            result = self.db.execute_query(query, (username, email, password_hash, full_name, role))

            # Create user directory using persistent storage
            user_dir = file_storage.create_user_directories(username, full_name)

            return True, f"User {username} created successfully"

        except Exception as e:
            if "UNIQUE" in str(e) or "duplicate" in str(e).lower():
                return False, f"User already exists: {e}"
            return False, f"Failed to create user: {e}"

    def authenticate(self, username, password):
        """Authenticate user and create session"""
        try:
            query = (
                "SELECT * FROM users WHERE username = %s"
                if self.db.is_postgres
                else "SELECT * FROM users WHERE username = ?"
            )

            users = self.db.execute_query(query, (username,))

            if not users:
                return None, "Invalid username or password"

            user = users[0]

            # Debug logging
            import logging

            logger = logging.getLogger(__name__)
            logger.info(f"User type: {type(user)}")
            logger.info(f"User data: {user}")

            # Access as dictionary (works for both PostgreSQL RealDictCursor and SQLite Row)
            try:
                password_hash = user["password_hash"]
                user_id = user["id"]
                user_role = user["role"]
                user_full_name = user.get("full_name", user["username"])
            except (KeyError, TypeError) as e:
                logger.error(f"Error accessing user data: {e}")
                logger.error(f"User object: {user}")
                logger.error(f"User type: {type(user)}")
                raise

            if not bcrypt.checkpw(password.encode(), password_hash.encode()):
                return None, "Invalid username or password"

            # SINGLE-SESSION ENFORCEMENT: Invalidate all existing active sessions for this user
            invalidate_query = (
                """
                UPDATE sessions SET is_active = false
                WHERE user_id = %s AND is_active = true
            """
                if self.db.is_postgres
                else """
                UPDATE sessions SET is_active = 0
                WHERE user_id = ? AND is_active = 1
            """
            )
            self.db.execute_query(invalidate_query, (user_id,))
            logger.info(f"Invalidated existing sessions for user {username} (user_id: {user_id})")

            # Create session token
            token = secrets.token_urlsafe(32)
            current_time = datetime.now()
            expires_at = current_time + timedelta(hours=24)

            # DEBUG LOGGING - Remove after debugging
            logger.info(f"[SESSION-CREATE] Creating session for user {username}")
            logger.info(f"[SESSION-CREATE] Current time: {current_time} (type: {type(current_time)}, tz: {current_time.tzinfo})")
            logger.info(f"[SESSION-CREATE] Expires at: {expires_at}")
            logger.info(f"[SESSION-CREATE] Initial last_activity: {current_time}")

            session_query = (
                """
                INSERT INTO sessions (user_id, token, expires_at, last_activity)
                VALUES (%s, %s, %s, %s)
            """
                if self.db.is_postgres
                else """
                INSERT INTO sessions (user_id, token, expires_at, last_activity)
                VALUES (?, ?, ?, ?)
            """
            )

            self.db.execute_query(session_query, (user_id, token, expires_at, current_time))
            logger.info(f"[SESSION-CREATE] Session created successfully for {username}")

            # Update last login
            update_query = (
                "UPDATE users SET last_login = %s WHERE id = %s"
                if self.db.is_postgres
                else "UPDATE users SET last_login = ? WHERE id = ?"
            )

            self.db.execute_query(update_query, (datetime.now(), user_id))

            return {
                "user_id": user_id,
                "username": username,
                "token": token,
                "role": user_role,
                "full_name": user_full_name,
                "expires_at": expires_at.isoformat(),
            }, None

        except Exception as e:
            return None, f"Authentication failed: {e}"

    def validate_session(self, token):
        """Validate session token and check for inactivity timeout (1 hour)"""
        try:
            query = (
                """
                SELECT s.*, u.username, u.role, u.full_name
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = %s AND s.is_active = true AND s.expires_at > %s
            """
                if self.db.is_postgres
                else """
                SELECT s.*, u.username, u.role, u.full_name
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ? AND s.is_active = 1 AND s.expires_at > ?
            """
            )

            sessions = self.db.execute_query(query, (token, datetime.now()))

            if not sessions:
                return None

            session = sessions[0]

            # AUTO-LOGOUT: TEMPORARILY DISABLED
            #
            # The auto-logout after 1 hour of inactivity has been temporarily disabled
            # because users were getting logged out prematurely (5-6 minutes instead of 1 hour).
            #
            # Single-session enforcement (lines 89-102) is still ACTIVE and working correctly.
            # Activity tracking (update_session_activity) is still ACTIVE for future debugging.
            #
            # Session still expires after 24 hours (checked at line 152 via expires_at column).
            #
            # TO RE-ENABLE AFTER FIXING:
            # 1. Switch back to the feat/user-session branch (has the full implementation)
            # 2. Review DEBUG_SESSION_TIMEOUT.md for debugging steps
            # 3. Collect production logs to identify root cause
            # 4. Fix the timezone/timing issue
            # 5. Test thoroughly with debug logging
            # 6. Merge the fix back
            #
            # Original code preserved in git history and feat/user-session branch

            # With RealDictCursor, this will always be a dict
            return {
                "user_id": session["user_id"],
                "username": session["username"],
                "role": session["role"],
                "full_name": session.get("full_name", session["username"]),
            }

        except Exception as e:
            print(f"Session validation error: {e}")
            return None

    def get_all_students(self):
        """Get all users with role='student'"""
        try:
            query = (
                "SELECT username, full_name, email FROM users WHERE role = %s ORDER BY username"
                if self.db.is_postgres
                else "SELECT username, full_name, email FROM users WHERE role = ? ORDER BY username"
            )

            students = self.db.execute_query(query, ("student",))
            return students if students else []

        except Exception as e:
            logger.error(f"Failed to get all students: {e}")
            return []

    def update_session_activity(self, token):
        """Update last_activity timestamp for a session"""
        try:
            current_time = datetime.now()

            # DEBUG LOGGING - Remove after debugging
            logger.info(f"[ACTIVITY-UPDATE] Updating session activity to: {current_time} (type: {type(current_time)}, tz: {current_time.tzinfo})")

            query = (
                """
                UPDATE sessions SET last_activity = %s
                WHERE token = %s AND is_active = true
            """
                if self.db.is_postgres
                else """
                UPDATE sessions SET last_activity = ?
                WHERE token = ? AND is_active = 1
            """
            )

            self.db.execute_query(query, (current_time, token))
            logger.info(f"[ACTIVITY-UPDATE] Session activity updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            return False

    def invalidate_other_sessions(self, user_id, current_token):
        """
        Invalidate all other active sessions for a user except the current one.
        Returns list of invalidated session tokens (for WebSocket termination).
        """
        try:
            # Get all other active session tokens for this user
            query = (
                """
                SELECT token FROM sessions
                WHERE user_id = %s AND token != %s AND is_active = true
            """
                if self.db.is_postgres
                else """
                SELECT token FROM sessions
                WHERE user_id = ? AND token != ? AND is_active = 1
            """
            )

            other_sessions = self.db.execute_query(query, (user_id, current_token))
            other_tokens = [row["token"] for row in other_sessions] if other_sessions else []

            if other_tokens:
                # Invalidate all other sessions
                invalidate_query = (
                    """
                    UPDATE sessions SET is_active = false
                    WHERE user_id = %s AND token != %s AND is_active = true
                """
                    if self.db.is_postgres
                    else """
                    UPDATE sessions SET is_active = 0
                    WHERE user_id = ? AND token != ? AND is_active = 1
                """
                )
                self.db.execute_query(invalidate_query, (user_id, current_token))
                logger.info(f"Invalidated {len(other_tokens)} other sessions for user_id {user_id}")

            return other_tokens
        except Exception as e:
            logger.error(f"Failed to invalidate other sessions: {e}")
            return []

    def logout(self, token):
        """Invalidate a session token"""
        try:
            query = (
                "UPDATE sessions SET is_active = false WHERE token = %s"
                if self.db.is_postgres
                else "UPDATE sessions SET is_active = 0 WHERE token = ?"
            )

            self.db.execute_query(query, (token,))
            return True
        except Exception as e:
            print(f"Logout error: {e}")
            return False

    def renew_session(self, token):
        """Extend session expiration by 24 hours (sliding window)"""
        try:
            # First validate the session is still active
            session = self.validate_session(token)
            if not session:
                return {"success": False, "error": "Invalid session"}

            # Extend expiration by 24 hours from now
            new_expires_at = datetime.now() + timedelta(hours=24)

            query = (
                "UPDATE sessions SET expires_at = %s WHERE token = %s AND is_active = true"
                if self.db.is_postgres
                else "UPDATE sessions SET expires_at = ? WHERE token = ? AND is_active = 1"
            )

            self.db.execute_query(query, (new_expires_at, token))

            return {
                "success": True,
                "expires_at": new_expires_at.isoformat(),
                "message": "Session renewed for 24 hours",
            }

        except Exception as e:
            print(f"Session renewal error: {e}")
            return {"success": False, "error": "Failed to renew session"}

    def change_password(self, username, old_password, new_password):
        """Change user password"""
        try:
            # Get user and verify old password
            query = (
                "SELECT password_hash FROM users WHERE username = %s"
                if self.db.is_postgres
                else "SELECT password_hash FROM users WHERE username = ?"
            )

            users = self.db.execute_query(query, (username,))

            if not users:
                return {"success": False, "error": "User not found"}

            user = users[0]
            password_hash = user["password_hash"]

            # Check old password
            if not bcrypt.checkpw(old_password.encode(), password_hash.encode()):
                return {"success": False, "error": "Invalid old password"}

            # Hash new password
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

            # Update password
            update_query = (
                "UPDATE users SET password_hash = %s WHERE username = %s"
                if self.db.is_postgres
                else "UPDATE users SET password_hash = ? WHERE username = ?"
            )

            self.db.execute_query(update_query, (new_hash.decode(), username))

            return {"success": True, "message": "Password changed successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_password_reset_token(self, username_or_email):
        """Create a password reset token for a user"""
        try:
            # Find user by username or email
            query = (
                """
                SELECT id, username, email, full_name 
                FROM users 
                WHERE username = %s OR email = %s
            """
                if self.db.is_postgres
                else """
                SELECT id, username, email, full_name 
                FROM users 
                WHERE username = ? OR email = ?
            """
            )

            users = self.db.execute_query(query, (username_or_email, username_or_email))

            if not users:
                return {"success": False, "error": "User not found"}

            user = users[0]
            user_id = user["id"]

            # Generate secure reset token
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour

            # Store reset token in database
            token_query = (
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at) 
                VALUES (%s, %s, %s)
            """
                if self.db.is_postgres
                else """
                INSERT INTO password_reset_tokens (user_id, token, expires_at) 
                VALUES (?, ?, ?)
            """
            )

            self.db.execute_query(token_query, (user_id, reset_token, expires_at))

            return {
                "success": True,
                "token": reset_token,
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "expires_at": expires_at.isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def reset_password_with_token(self, token, new_password):
        """Reset password using a valid reset token"""
        try:
            # Find valid reset token
            query = (
                """
                SELECT prt.*, u.username 
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = %s AND prt.is_used = false AND prt.expires_at > %s
            """
                if self.db.is_postgres
                else """
                SELECT prt.*, u.username 
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = ? AND prt.is_used = 0 AND prt.expires_at > ?
            """
            )

            tokens = self.db.execute_query(query, (token, datetime.now()))

            if not tokens:
                return {"success": False, "error": "Invalid or expired reset token"}

            token_record = tokens[0]
            user_id = token_record["user_id"]
            username = token_record["username"]

            # Hash new password
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

            # Update password
            update_query = (
                "UPDATE users SET password_hash = %s WHERE id = %s"
                if self.db.is_postgres
                else "UPDATE users SET password_hash = ? WHERE id = ?"
            )

            self.db.execute_query(update_query, (new_hash.decode(), user_id))

            # Mark token as used
            mark_used_query = (
                "UPDATE password_reset_tokens SET is_used = true WHERE token = %s"
                if self.db.is_postgres
                else "UPDATE password_reset_tokens SET is_used = 1 WHERE token = ?"
            )

            self.db.execute_query(mark_used_query, (token,))

            return {"success": True, "message": f"Password reset successfully for {username}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def admin_force_password_reset(self, admin_username, target_username, new_password):
        """
        Admin-only function to force reset any user's password without knowing old password
        Only admin_editor role can use this function

        Args:
            admin_username (str): Username of the admin performing the action
            target_username (str): Username of the user whose password to reset
            new_password (str): New password to set

        Returns:
            dict: Success status and message
        """
        try:
            # Verify admin has permission
            admin_query = (
                "SELECT role FROM users WHERE username = %s"
                if self.db.is_postgres
                else "SELECT role FROM users WHERE username = ?"
            )

            admin_users = self.db.execute_query(admin_query, (admin_username,))

            if not admin_users:
                return {"success": False, "error": "Admin user not found"}

            admin_role = admin_users[0]["role"]

            # Only admin_editor can force reset passwords
            if admin_username != "admin_editor":
                return {
                    "success": False,
                    "error": "Insufficient permissions. Only admin_editor can force reset passwords.",
                }

            # Check if target user exists
            target_query = (
                "SELECT id, username, full_name FROM users WHERE username = %s"
                if self.db.is_postgres
                else "SELECT id, username, full_name FROM users WHERE username = ?"
            )

            target_users = self.db.execute_query(target_query, (target_username,))

            if not target_users:
                return {"success": False, "error": f"Target user {target_username} not found"}

            target_user = target_users[0]
            target_user_id = target_user["id"]
            target_full_name = target_user["full_name"]

            # Hash the new password
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

            # Update password
            update_query = (
                "UPDATE users SET password_hash = %s WHERE id = %s"
                if self.db.is_postgres
                else "UPDATE users SET password_hash = ? WHERE id = ?"
            )

            self.db.execute_query(update_query, (new_hash.decode(), target_user_id))

            # Invalidate all existing sessions for the target user (force re-login)
            invalidate_sessions_query = (
                "UPDATE sessions SET is_active = false WHERE user_id = %s"
                if self.db.is_postgres
                else "UPDATE sessions SET is_active = 0 WHERE user_id = ?"
            )

            self.db.execute_query(invalidate_sessions_query, (target_user_id,))

            return {
                "success": True,
                "message": f"Password reset successfully for {target_username} ({target_full_name}). User will need to log in again.",
                "target_user": target_username,
                "target_full_name": target_full_name,
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to reset password: {str(e)}"}

    def get_all_users_for_admin(self, admin_username):
        """
        Get list of all users (admin-only function)
        Only admin_editor role can access this

        Args:
            admin_username (str): Username of the admin requesting data

        Returns:
            dict: Success status and user list
        """
        try:
            # Verify admin has permission
            admin_query = (
                "SELECT role FROM users WHERE username = %s"
                if self.db.is_postgres
                else "SELECT role FROM users WHERE username = ?"
            )

            admin_users = self.db.execute_query(admin_query, (admin_username,))

            if not admin_users:
                return {"success": False, "error": "Admin user not found"}

            # Only admin_editor can access user list
            if admin_username != "admin_editor":
                return {
                    "success": False,
                    "error": "Insufficient permissions. Only admin_editor can access user management.",
                }

            # Get all users
            users_query = """
                SELECT id, username, email, full_name, role, created_at, last_login
                FROM users 
                ORDER BY role DESC, username ASC
            """

            users = self.db.execute_query(users_query)

            # Convert to list of dictionaries for JSON serialization
            users_list = []
            for user in users:
                users_list.append(
                    {
                        "id": user["id"],
                        "username": user["username"],
                        "email": user["email"],
                        "full_name": user["full_name"],
                        "role": user["role"],
                        "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                        "last_login": user["last_login"].isoformat() if user["last_login"] else None,
                    }
                )

            return {"success": True, "users": users_list, "total_count": len(users_list)}

        except Exception as e:
            return {"success": False, "error": f"Failed to get users: {str(e)}"}

    def cleanup_idle_sessions(self):
        """
        Cleanup sessions that have been idle for more than 1 hour.
        TEMPORARILY DISABLED - Returns empty list.

        This is called periodically by IdleSessionCleanupJob (every 5 minutes)
        but does nothing until the auto-logout timeout issue is debugged and fixed.

        The background job will continue running but won't terminate any sessions.

        TO RE-ENABLE AFTER FIXING:
        1. Switch back to feat/user-session branch (has full implementation)
        2. Debug and fix the timeout calculation issue
        3. Test thoroughly with debug logging
        4. Restore this method from git history
        """
        logger.debug("Idle session cleanup temporarily disabled (rollback)")
        return []  # No users to cleanup


# Background job for idle session cleanup
class IdleSessionCleanupJob:
    """Background thread that periodically cleans up idle sessions"""

    def __init__(self, user_manager):
        self.user_manager = user_manager
        self.running = False
        self.thread = None

    def start(self):
        """Start the cleanup background job"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.thread.start()
        logger.info("Idle session cleanup job started (runs every 5 minutes)")

    def stop(self):
        """Stop the cleanup background job"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Idle session cleanup job stopped")

    def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.running:
            try:
                # Run cleanup every 5 minutes
                time_module.sleep(300)

                idle_users = self.user_manager.cleanup_idle_sessions()

                # Terminate WebSocket connections for idle users
                if idle_users:
                    # Import here to avoid circular dependency
                    from handlers.authenticated_ws_handler import ws_connection_registry

                    for username in idle_users:
                        ws_connection_registry.terminate_session(username, reason="inactivity")

                    logger.info(f"Terminated {len(idle_users)} idle WebSocket connections")

            except Exception as e:
                logger.error(f"Error in idle session cleanup loop: {e}")
                time_module.sleep(60)  # Wait 1 minute before retrying on error


# Global cleanup job instance (started by server.py)
idle_cleanup_job = None
