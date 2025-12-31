"""
Admin Authentication Handler
Handles admin login, logout, and session validation.
"""

import json
import logging
import os
import sys

from tornado.web import RequestHandler

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from auth.admin_session_manager import admin_session_manager
from utils.audit_logger import log_admin_action, AuditActionType

logger = logging.getLogger(__name__)


class BaseAdminHandler(RequestHandler):
    """Base handler for admin API endpoints with common functionality"""

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def get_client_ip(self):
        """Get client IP address (considering proxies)"""
        x_forwarded_for = self.request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        x_real_ip = self.request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip
        return self.request.remote_ip

    def get_user_agent(self):
        """Get client user agent"""
        return self.request.headers.get("User-Agent", "")

    def get_auth_token(self):
        """Extract token from Authorization header"""
        auth_header = self.request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None

    def validate_admin_session(self):
        """
        Validate admin session from Authorization header.
        Returns user data if valid, None otherwise.
        """
        token = self.get_auth_token()
        if not token:
            return None
        return admin_session_manager.validate_admin_session(token)

    def require_admin(self):
        """
        Require valid admin session. Returns user data or sends 401 response.
        """
        user = self.validate_admin_session()
        if not user:
            self.set_status(401)
            self.write({"success": False, "error": "Unauthorized. Please log in."})
            return None
        return user

    def write_error_response(self, status_code, error_message):
        """Write a standard error response"""
        self.set_status(status_code)
        self.write({"success": False, "error": error_message})

    def write_success_response(self, data=None):
        """Write a standard success response"""
        response = {"success": True}
        if data:
            response.update(data)
        self.write(response)


class AdminAuthHandler(BaseAdminHandler):
    """Handle admin login and logout"""

    async def post(self):
        """Handle login or logout based on path"""
        path = self.request.path

        if path.endswith("/login"):
            await self._handle_login()
        elif path.endswith("/logout"):
            await self._handle_logout()
        else:
            self.write_error_response(404, "Not found")

    async def _handle_login(self):
        """Process admin login request"""
        try:
            # Parse request body
            try:
                data = json.loads(self.request.body.decode())
            except json.JSONDecodeError:
                self.write_error_response(400, "Invalid JSON")
                return

            username = data.get("username", "").strip()
            password = data.get("password", "")

            if not username or not password:
                self.write_error_response(400, "Username and password are required")
                return

            # Authenticate
            ip_address = self.get_client_ip()
            user_agent = self.get_user_agent()

            session_data, error = admin_session_manager.authenticate_admin(
                username=username,
                password=password,
                ip_address=ip_address,
                user_agent=user_agent
            )

            if error:
                self.write_error_response(401, error)
                return

            # Log successful login
            log_admin_action(
                admin_user_id=session_data["user_id"],
                action_type=AuditActionType.ADMIN_LOGIN,
                details={"ip_address": ip_address},
                ip_address=ip_address
            )

            self.write_success_response({
                "token": session_data["token"],
                "user": {
                    "id": session_data["user_id"],
                    "username": session_data["username"],
                    "full_name": session_data["full_name"],
                    "email": session_data["email"],
                    "role": session_data["role"]
                },
                "expires_at": session_data["expires_at"]
            })

        except Exception as e:
            logger.error(f"Admin login error: {e}")
            self.write_error_response(500, "Internal server error")

    async def _handle_logout(self):
        """Process admin logout request"""
        try:
            user = self.validate_admin_session()
            token = self.get_auth_token()

            if user and token:
                # Log logout before invalidating
                log_admin_action(
                    admin_user_id=user["user_id"],
                    action_type=AuditActionType.ADMIN_LOGOUT,
                    ip_address=self.get_client_ip()
                )

                admin_session_manager.logout(token)

            self.write_success_response({"message": "Logged out successfully"})

        except Exception as e:
            logger.error(f"Admin logout error: {e}")
            self.write_error_response(500, "Internal server error")


class AdminSessionHandler(BaseAdminHandler):
    """Handle admin session validation and renewal"""

    async def get(self):
        """Validate current session"""
        try:
            user = self.validate_admin_session()

            if not user:
                self.write_error_response(401, "Invalid or expired session")
                return

            self.write_success_response({
                "valid": True,
                "user": {
                    "id": user["user_id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "role": user["role"]
                }
            })

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            self.write_error_response(500, "Internal server error")

    async def post(self):
        """Renew session (extend expiration)"""
        try:
            token = self.get_auth_token()
            if not token:
                self.write_error_response(401, "No session token provided")
                return

            result = admin_session_manager.renew_session(token)

            if result.get("success"):
                self.write_success_response({
                    "expires_at": result["expires_at"],
                    "message": "Session renewed successfully"
                })
            else:
                self.write_error_response(401, result.get("error", "Failed to renew session"))

        except Exception as e:
            logger.error(f"Session renewal error: {e}")
            self.write_error_response(500, "Internal server error")
