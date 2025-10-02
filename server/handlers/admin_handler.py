#!/usr/bin/env python3
"""
Admin-only API handlers for password management
Only accessible to admin_editor role
"""
import json
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tornado.web import RequestHandler
from auth.user_manager_postgres import UserManager
from utils.password_generator import PasswordGenerator

logger = logging.getLogger(__name__)


class AdminPasswordHandler(RequestHandler):
    """Handle admin password management operations"""

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

    def options(self):
        self.set_status(204)
        self.finish()

    async def post(self):
        """Handle password management operations"""
        try:
            # Parse request body
            try:
                data = json.loads(self.request.body.decode())
            except json.JSONDecodeError:
                self.set_status(400)
                self.write({"success": False, "error": "Invalid JSON"})
                return

            action = data.get("action")
            admin_username = data.get("admin_username")

            if not admin_username:
                self.set_status(400)
                self.write({"success": False, "error": "admin_username is required"})
                return

            # Verify admin permissions
            user_manager = UserManager()

            if action == "get_users":
                result = user_manager.get_all_users_for_admin(admin_username)

            elif action == "reset_password":
                target_username = data.get("target_username")
                new_password = data.get("new_password")

                if not target_username or not new_password:
                    self.set_status(400)
                    self.write({"success": False, "error": "target_username and new_password are required"})
                    return

                result = user_manager.admin_force_password_reset(admin_username, target_username, new_password)

            elif action == "generate_password":
                length = data.get("length", 12)

                generator = PasswordGenerator()
                new_password = generator.generate_password(length=length)

                result = {
                    "success": True,
                    "password": new_password,
                    "length": length,
                    "generated_at": datetime.now().isoformat(),
                }

            elif action == "generate_random_password_for_user":
                target_username = data.get("target_username")
                length = data.get("length", 12)

                if not target_username:
                    self.set_status(400)
                    self.write({"success": False, "error": "target_username is required"})
                    return

                # Generate random password
                generator = PasswordGenerator()
                new_password = generator.generate_password(length=length)

                # Reset the user's password
                result = user_manager.admin_force_password_reset(admin_username, target_username, new_password)

                if result["success"]:
                    result["new_password"] = new_password
                    result["generated_at"] = datetime.now().isoformat()

            elif action == "bulk_password_export":
                # Get all users and generate new passwords
                users_result = user_manager.get_all_users_for_admin(admin_username)

                if not users_result["success"]:
                    result = users_result
                else:
                    generator = PasswordGenerator()
                    users_with_passwords = []

                    for user in users_result["users"]:
                        # Generate new password
                        new_password = generator.generate_password(length=12)

                        # Reset password in database
                        reset_result = user_manager.admin_force_password_reset(
                            admin_username, user["username"], new_password
                        )

                        if reset_result["success"]:
                            users_with_passwords.append(
                                {
                                    "username": user["username"],
                                    "full_name": user["full_name"],
                                    "password": new_password,
                                    "role": user["role"],
                                    "email": user["email"],
                                    "password_generated_at": datetime.now().isoformat(),
                                }
                            )

                    # Export to CSV
                    if users_with_passwords:
                        csv_path = generator.export_to_csv(users_with_passwords, "admin_bulk_password_reset")

                        result = {
                            "success": True,
                            "message": f"Bulk password reset completed for {len(users_with_passwords)} users",
                            "csv_path": csv_path,
                            "users_updated": len(users_with_passwords),
                            "export_file": os.path.basename(csv_path),
                        }
                    else:
                        result = {"success": False, "error": "No users were updated"}

            else:
                self.set_status(400)
                result = {"success": False, "error": f"Unknown action: {action}"}

            # Return result
            if result.get("success", False):
                self.set_status(200)
            else:
                self.set_status(403 if "permissions" in result.get("error", "").lower() else 400)

            self.write(result)

        except Exception as e:
            logger.error(f"Admin password handler error: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Internal server error"})


class AdminUserListHandler(RequestHandler):
    """Handle admin user list operations (GET only)"""

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.set_header("Access-Control-Allow-Methods", "GET, OPTIONS")

    def options(self):
        self.set_status(204)
        self.finish()

    async def get(self):
        """Get list of all users (admin only)"""
        try:
            # Get admin username from query parameters or headers
            admin_username = self.get_query_argument("admin_username", None)

            if not admin_username:
                # Try to get from Authorization header
                auth_header = self.request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    # In a real implementation, you'd validate the token
                    # For now, we'll expect admin_username as a query parameter
                    pass

            if not admin_username:
                self.set_status(400)
                self.write({"success": False, "error": "admin_username parameter is required"})
                return

            user_manager = UserManager()
            result = user_manager.get_all_users_for_admin(admin_username)

            if result.get("success", False):
                self.set_status(200)
            else:
                self.set_status(403 if "permissions" in result.get("error", "").lower() else 400)

            self.write(result)

        except Exception as e:
            logger.error(f"Admin user list handler error: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Internal server error"})


# Handler registration for server.py
def get_admin_handlers():
    """Return list of admin handler routes"""
    return [
        (r"/api/admin/password", AdminPasswordHandler),
        (r"/api/admin/users", AdminUserListHandler),
    ]
