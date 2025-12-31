"""
Admin Session Manager
Handles authentication and session management for the admin panel.
Separate from main IDE sessions for security isolation.
"""

import bcrypt
import secrets
import logging
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database import db_manager

logger = logging.getLogger(__name__)


class AdminSessionManager:
    """Manages admin panel sessions (separate from main IDE sessions)"""

    def __init__(self):
        self.db = db_manager
        self.session_duration_hours = 24

    def authenticate_admin(self, username: str, password: str, ip_address: str = None, user_agent: str = None):
        """
        Authenticate admin user (must be professor role).

        Args:
            username: Admin username
            password: Admin password
            ip_address: Client IP address (for logging)
            user_agent: Client user agent (for logging)

        Returns:
            tuple: (session_data, error_message)
        """
        try:
            # Get user from database
            query = """
                SELECT id, username, password_hash, full_name, role, email
                FROM users
                WHERE username = %s AND is_active = true
            """
            users = self.db.execute_query(query, (username,))

            if not users:
                self._log_login_attempt(None, ip_address, user_agent, success=False)
                return None, "Invalid username or password"

            user = users[0]

            # Verify password
            if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                self._log_login_attempt(user["id"], ip_address, user_agent, success=False)
                return None, "Invalid username or password"

            # Check if user is a professor (admin access)
            if user["role"] != "professor":
                self._log_login_attempt(user["id"], ip_address, user_agent, success=False)
                return None, "Access denied. Admin privileges required."

            # Invalidate any existing admin sessions for this user (single session)
            self._invalidate_user_admin_sessions(user["id"])

            # Create new admin session
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=self.session_duration_hours)

            session_query = """
                INSERT INTO admin_sessions (user_id, token, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            result = self.db.execute_query(
                session_query,
                (user["id"], token, expires_at, ip_address, user_agent)
            )

            # Log successful login
            self._log_login_attempt(user["id"], ip_address, user_agent, success=True, login_type="admin")

            logger.info(f"Admin login successful for user: {username}")

            return {
                "user_id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
                "token": token,
                "expires_at": expires_at.isoformat()
            }, None

        except Exception as e:
            logger.error(f"Admin authentication error: {e}")
            return None, "Authentication failed. Please try again."

    def validate_admin_session(self, token: str):
        """
        Validate an admin session token.

        Args:
            token: Session token to validate

        Returns:
            dict: User data if valid, None otherwise
        """
        try:
            query = """
                SELECT s.*, u.username, u.full_name, u.email, u.role
                FROM admin_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = %s AND s.is_active = true AND s.expires_at > %s
            """
            sessions = self.db.execute_query(query, (token, datetime.now()))

            if not sessions:
                return None

            session = sessions[0]

            # Verify user is still a professor
            if session["role"] != "professor":
                self._invalidate_session(token)
                return None

            return {
                "user_id": session["user_id"],
                "username": session["username"],
                "full_name": session["full_name"],
                "email": session["email"],
                "role": session["role"]
            }

        except Exception as e:
            logger.error(f"Admin session validation error: {e}")
            return None

    def logout(self, token: str):
        """
        Invalidate an admin session (logout).

        Args:
            token: Session token to invalidate

        Returns:
            bool: True if successful
        """
        try:
            # Get session details for logging
            session = self.validate_admin_session(token)
            if session:
                # Log logout time
                self._log_logout(session["user_id"])

            self._invalidate_session(token)
            logger.info(f"Admin logout successful")
            return True

        except Exception as e:
            logger.error(f"Admin logout error: {e}")
            return False

    def renew_session(self, token: str):
        """
        Extend admin session expiration (sliding window).

        Args:
            token: Session token to renew

        Returns:
            dict: New expiration time or error
        """
        try:
            session = self.validate_admin_session(token)
            if not session:
                return {"success": False, "error": "Invalid session"}

            new_expires_at = datetime.now() + timedelta(hours=self.session_duration_hours)

            query = """
                UPDATE admin_sessions
                SET expires_at = %s
                WHERE token = %s AND is_active = true
            """
            self.db.execute_query(query, (new_expires_at, token))

            return {
                "success": True,
                "expires_at": new_expires_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Admin session renewal error: {e}")
            return {"success": False, "error": "Failed to renew session"}

    def _invalidate_session(self, token: str):
        """Invalidate a specific session"""
        query = "UPDATE admin_sessions SET is_active = false WHERE token = %s"
        self.db.execute_query(query, (token,))

    def _invalidate_user_admin_sessions(self, user_id: int):
        """Invalidate all admin sessions for a user"""
        query = "UPDATE admin_sessions SET is_active = false WHERE user_id = %s AND is_active = true"
        self.db.execute_query(query, (user_id,))

    def _log_login_attempt(self, user_id: int, ip_address: str, user_agent: str,
                           success: bool, login_type: str = "admin"):
        """Log a login attempt to login_history table"""
        try:
            query = """
                INSERT INTO login_history (user_id, ip_address, user_agent, success, login_type)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute_query(query, (user_id, ip_address, user_agent, success, login_type))
        except Exception as e:
            logger.error(f"Failed to log login attempt: {e}")

    def _log_logout(self, user_id: int):
        """Update logout time for the most recent login"""
        try:
            query = """
                UPDATE login_history
                SET logout_time = %s
                WHERE id = (
                    SELECT id FROM login_history
                    WHERE user_id = %s AND logout_time IS NULL
                    ORDER BY login_time DESC
                    LIMIT 1
                )
            """
            self.db.execute_query(query, (datetime.now(), user_id))
        except Exception as e:
            logger.error(f"Failed to log logout: {e}")

    def cleanup_expired_sessions(self):
        """Remove expired admin sessions (called periodically)"""
        try:
            query = """
                UPDATE admin_sessions
                SET is_active = false
                WHERE expires_at < %s AND is_active = true
            """
            self.db.execute_query(query, (datetime.now(),))
        except Exception as e:
            logger.error(f"Failed to cleanup expired admin sessions: {e}")

    def get_active_admin_sessions_count(self):
        """Get count of active admin sessions"""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM admin_sessions
                WHERE is_active = true AND expires_at > %s
            """
            result = self.db.execute_query(query, (datetime.now(),))
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Failed to get active admin sessions count: {e}")
            return 0


# Global instance
admin_session_manager = AdminSessionManager()
