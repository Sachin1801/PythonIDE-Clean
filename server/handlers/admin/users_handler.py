"""
Admin Users Handler
Handles user CRUD operations, bulk import, and password management.
"""

import json
import logging
import os
import sys
import csv
import io
import bcrypt
from datetime import datetime

from tornado.web import RequestHandler

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.database import db_manager
from common.file_storage import file_storage
from auth.admin_session_manager import admin_session_manager
from utils.audit_logger import log_admin_action, AuditActionType
from utils.password_generator import PasswordGenerator
from handlers.admin.auth_handler import BaseAdminHandler

logger = logging.getLogger(__name__)


class AdminUsersHandler(BaseAdminHandler):
    """Handle user listing, creation, and export"""

    async def get(self):
        """Get list of users with pagination and filtering"""
        try:
            admin = self.require_admin()
            if not admin:
                return

            # Parse query parameters
            page = int(self.get_query_argument("page", "1"))
            limit = int(self.get_query_argument("limit", "20"))
            search = self.get_query_argument("search", "").strip()
            role = self.get_query_argument("role", "").strip()
            status = self.get_query_argument("status", "").strip()
            sort_by = self.get_query_argument("sort_by", "username")
            sort_order = self.get_query_argument("sort_order", "asc")
            export_csv = self.get_query_argument("export", "").lower() == "true"

            # Validate sort parameters
            valid_sort_columns = ["username", "full_name", "email", "role", "created_at", "last_login"]
            if sort_by not in valid_sort_columns:
                sort_by = "username"
            if sort_order not in ["asc", "desc"]:
                sort_order = "asc"

            # Build query
            conditions = []
            params = []

            if search:
                conditions.append(
                    "(username ILIKE %s OR full_name ILIKE %s OR email ILIKE %s)"
                )
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern, search_pattern])

            if role in ["student", "professor"]:
                conditions.append("role = %s")
                params.append(role)

            if status == "active":
                conditions.append("is_active = true")
            elif status == "inactive":
                conditions.append("is_active = false")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM users WHERE {where_clause}"
            count_result = db_manager.execute_query(count_query, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            # Handle CSV export
            if export_csv:
                return await self._export_users_csv(where_clause, params, sort_by, sort_order)

            # Get paginated results
            offset = (page - 1) * limit
            query = f"""
                SELECT id, username, full_name, email, role, is_active, created_at, last_login
                FROM users
                WHERE {where_clause}
                ORDER BY {sort_by} {sort_order}
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            users = db_manager.execute_query(query, tuple(params))

            # Format response
            users_list = []
            for user in users:
                users_list.append({
                    "id": user["id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "role": user["role"],
                    "is_active": user["is_active"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                    "last_login": user["last_login"].isoformat() if user["last_login"] else None
                })

            self.write_success_response({
                "users": users_list,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            })

        except Exception as e:
            logger.error(f"Get users error: {e}")
            self.write_error_response(500, "Internal server error")

    async def post(self):
        """Create a new user"""
        try:
            admin = self.require_admin()
            if not admin:
                return

            # Parse request body
            try:
                data = json.loads(self.request.body.decode())
            except json.JSONDecodeError:
                self.write_error_response(400, "Invalid JSON")
                return

            username = data.get("username", "").strip()
            password = data.get("password", "")
            full_name = data.get("full_name", "").strip()
            email = data.get("email", "").strip()
            role = data.get("role", "student").strip()

            # Validate required fields
            if not username:
                self.write_error_response(400, "Username is required")
                return

            if not password:
                self.write_error_response(400, "Password is required")
                return

            if role not in ["student", "professor"]:
                self.write_error_response(400, "Role must be 'student' or 'professor'")
                return

            # Generate email if not provided
            if not email:
                email = f"{username}@college.edu"

            # Check if username already exists
            check_query = "SELECT id FROM users WHERE username = %s"
            existing = db_manager.execute_query(check_query, (username,))
            if existing:
                self.write_error_response(409, f"Username '{username}' already exists")
                return

            # Hash password
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")

            # Create user
            insert_query = """
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            result = db_manager.execute_query(
                insert_query,
                (username, email, password_hash, full_name or username, role)
            )

            if not result:
                self.write_error_response(500, "Failed to create user")
                return

            user_id = result[0]["id"]

            # Create user directory
            try:
                file_storage.create_user_directories(username, full_name or username)
            except Exception as e:
                logger.error(f"Failed to create user directory: {e}")

            # Log action
            log_admin_action(
                admin_user_id=admin["user_id"],
                action_type=AuditActionType.CREATE_USER,
                target_user_id=user_id,
                details={"username": username, "role": role},
                ip_address=self.get_client_ip()
            )

            self.write_success_response({
                "user": {
                    "id": user_id,
                    "username": username,
                    "full_name": full_name or username,
                    "email": email,
                    "role": role
                },
                "message": f"User '{username}' created successfully"
            })

        except Exception as e:
            logger.error(f"Create user error: {e}")
            self.write_error_response(500, "Internal server error")

    async def _export_users_csv(self, where_clause, params, sort_by, sort_order):
        """Export users as CSV download"""
        try:
            query = f"""
                SELECT username, full_name, email, role, is_active, created_at, last_login
                FROM users
                WHERE {where_clause}
                ORDER BY {sort_by} {sort_order}
            """
            users = db_manager.execute_query(query, tuple(params))

            # Build CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["username", "full_name", "email", "role", "is_active", "created_at", "last_login"])

            for user in users:
                writer.writerow([
                    user["username"],
                    user["full_name"],
                    user["email"],
                    user["role"],
                    "active" if user["is_active"] else "inactive",
                    user["created_at"].isoformat() if user["created_at"] else "",
                    user["last_login"].isoformat() if user["last_login"] else ""
                ])

            csv_content = output.getvalue()
            output.close()

            # Set response headers for download
            self.set_header("Content-Type", "text/csv")
            self.set_header("Content-Disposition", f"attachment; filename=users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            self.write(csv_content)

        except Exception as e:
            logger.error(f"Export users CSV error: {e}")
            self.write_error_response(500, "Failed to export users")


class AdminUserDetailHandler(BaseAdminHandler):
    """Handle single user operations: get, update, delete, reset password"""

    async def get(self, user_id):
        """Get user details"""
        try:
            admin = self.require_admin()
            if not admin:
                return

            query = """
                SELECT id, username, full_name, email, role, is_active, created_at, last_login
                FROM users
                WHERE id = %s
            """
            users = db_manager.execute_query(query, (int(user_id),))

            if not users:
                self.write_error_response(404, "User not found")
                return

            user = users[0]
            self.write_success_response({
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "role": user["role"],
                    "is_active": user["is_active"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                    "last_login": user["last_login"].isoformat() if user["last_login"] else None
                }
            })

        except Exception as e:
            logger.error(f"Get user detail error: {e}")
            self.write_error_response(500, "Internal server error")

    async def put(self, user_id):
        """Update user details"""
        try:
            admin = self.require_admin()
            if not admin:
                return

            # Parse request body
            try:
                data = json.loads(self.request.body.decode())
            except json.JSONDecodeError:
                self.write_error_response(400, "Invalid JSON")
                return

            # Build update query dynamically
            updates = []
            params = []

            if "full_name" in data:
                updates.append("full_name = %s")
                params.append(data["full_name"].strip())

            if "email" in data:
                updates.append("email = %s")
                params.append(data["email"].strip())

            if "role" in data and data["role"] in ["student", "professor"]:
                updates.append("role = %s")
                params.append(data["role"])

            if "is_active" in data:
                updates.append("is_active = %s")
                params.append(bool(data["is_active"]))

            if not updates:
                self.write_error_response(400, "No valid fields to update")
                return

            params.append(int(user_id))
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s RETURNING username"

            result = db_manager.execute_query(query, tuple(params))

            if not result:
                self.write_error_response(404, "User not found")
                return

            # Log action
            log_admin_action(
                admin_user_id=admin["user_id"],
                action_type=AuditActionType.UPDATE_USER,
                target_user_id=int(user_id),
                details={"updated_fields": list(data.keys())},
                ip_address=self.get_client_ip()
            )

            self.write_success_response({
                "message": f"User '{result[0]['username']}' updated successfully"
            })

        except Exception as e:
            logger.error(f"Update user error: {e}")
            self.write_error_response(500, "Internal server error")

    async def delete(self, user_id):
        """Delete a user"""
        try:
            admin = self.require_admin()
            if not admin:
                return

            # Get user info before deleting
            query = "SELECT username FROM users WHERE id = %s"
            users = db_manager.execute_query(query, (int(user_id),))

            if not users:
                self.write_error_response(404, "User not found")
                return

            username = users[0]["username"]

            # Prevent deleting self
            if admin["user_id"] == int(user_id):
                self.write_error_response(400, "Cannot delete your own account")
                return

            # Delete user
            delete_query = "DELETE FROM users WHERE id = %s"
            db_manager.execute_query(delete_query, (int(user_id),))

            # Log action
            log_admin_action(
                admin_user_id=admin["user_id"],
                action_type=AuditActionType.DELETE_USER,
                target_user_id=int(user_id),
                details={"username": username},
                ip_address=self.get_client_ip()
            )

            self.write_success_response({
                "message": f"User '{username}' deleted successfully"
            })

        except Exception as e:
            logger.error(f"Delete user error: {e}")
            self.write_error_response(500, "Internal server error")

    async def post(self, user_id):
        """Handle POST operations like reset-password"""
        path = self.request.path

        if path.endswith("/reset-password"):
            await self._reset_password(user_id)
        else:
            self.write_error_response(404, "Not found")

    async def _reset_password(self, user_id):
        """Reset user password"""
        try:
            admin = self.require_admin()
            if not admin:
                return

            # Parse optional new password from body
            new_password = None
            if self.request.body:
                try:
                    data = json.loads(self.request.body.decode())
                    new_password = data.get("new_password")
                except json.JSONDecodeError:
                    pass

            # Generate password if not provided
            if not new_password:
                generator = PasswordGenerator()
                new_password = generator.generate_password(length=12)

            # Get user info
            query = "SELECT username FROM users WHERE id = %s"
            users = db_manager.execute_query(query, (int(user_id),))

            if not users:
                self.write_error_response(404, "User not found")
                return

            username = users[0]["username"]

            # Hash and update password
            password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode("utf-8")
            update_query = "UPDATE users SET password_hash = %s WHERE id = %s"
            db_manager.execute_query(update_query, (password_hash, int(user_id)))

            # Invalidate all sessions for this user
            invalidate_query = "UPDATE sessions SET is_active = false WHERE user_id = %s"
            db_manager.execute_query(invalidate_query, (int(user_id),))

            # Log action
            log_admin_action(
                admin_user_id=admin["user_id"],
                action_type=AuditActionType.RESET_PASSWORD,
                target_user_id=int(user_id),
                details={"username": username},
                ip_address=self.get_client_ip()
            )

            self.write_success_response({
                "new_password": new_password,
                "message": f"Password reset for '{username}'. User will need to log in again."
            })

        except Exception as e:
            logger.error(f"Reset password error: {e}")
            self.write_error_response(500, "Internal server error")


class AdminBulkImportHandler(BaseAdminHandler):
    """Handle bulk user import from CSV"""

    async def get(self):
        """Download CSV template"""
        try:
            admin = self.require_admin()
            if not admin:
                return

            template = "username,password,full_name,email,role\njd1234,temp123,John Doe,jd1234@college.edu,student\n"

            self.set_header("Content-Type", "text/csv")
            self.set_header("Content-Disposition", "attachment; filename=user_import_template.csv")
            self.write(template)

        except Exception as e:
            logger.error(f"Download template error: {e}")
            self.write_error_response(500, "Internal server error")

    async def post(self):
        """Import users from CSV"""
        try:
            admin = self.require_admin()
            if not admin:
                return

            # Check for file upload
            if "file" not in self.request.files:
                # Try to parse CSV from body
                try:
                    csv_content = self.request.body.decode()
                except:
                    self.write_error_response(400, "No file uploaded")
                    return
            else:
                file_info = self.request.files["file"][0]
                csv_content = file_info["body"].decode()

            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content))

            created = 0
            failed = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    # Normalize column names (handle variations)
                    username = (row.get("username") or row.get("Username") or "").strip()
                    password = (row.get("password") or row.get("Password") or "").strip()
                    full_name = (row.get("full_name") or row.get("name") or row.get("Name") or "").strip()
                    email = (row.get("email") or row.get("Email") or "").strip()
                    role = (row.get("role") or row.get("Role") or "student").strip().lower()

                    if not username:
                        errors.append({"row": row_num, "error": "Username is required"})
                        failed += 1
                        continue

                    if not password:
                        errors.append({"row": row_num, "username": username, "error": "Password is required"})
                        failed += 1
                        continue

                    if role not in ["student", "professor"]:
                        role = "student"

                    if not email:
                        email = f"{username}@college.edu"

                    if not full_name:
                        full_name = username

                    # Check if user exists
                    check_query = "SELECT id FROM users WHERE username = %s"
                    existing = db_manager.execute_query(check_query, (username,))
                    if existing:
                        errors.append({"row": row_num, "username": username, "error": "Username already exists"})
                        failed += 1
                        continue

                    # Create user
                    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
                    insert_query = """
                        INSERT INTO users (username, email, password_hash, full_name, role)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """
                    result = db_manager.execute_query(
                        insert_query,
                        (username, email, password_hash, full_name, role)
                    )

                    if result:
                        # Create user directory
                        try:
                            file_storage.create_user_directories(username, full_name)
                        except Exception as e:
                            logger.error(f"Failed to create directory for {username}: {e}")

                        created += 1

                except Exception as e:
                    errors.append({"row": row_num, "error": str(e)})
                    failed += 1

            # Log action
            log_admin_action(
                admin_user_id=admin["user_id"],
                action_type=AuditActionType.BULK_IMPORT_USERS,
                details={"created": created, "failed": failed},
                ip_address=self.get_client_ip()
            )

            self.write_success_response({
                "created": created,
                "failed": failed,
                "errors": errors[:20],  # Limit errors in response
                "message": f"Imported {created} users, {failed} failed"
            })

        except Exception as e:
            logger.error(f"Bulk import error: {e}")
            self.write_error_response(500, "Internal server error")
