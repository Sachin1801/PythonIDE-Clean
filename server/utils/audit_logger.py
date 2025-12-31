"""
Audit Logger Utility
Centralized logging for all admin actions to provide complete audit trail.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database import db_manager

logger = logging.getLogger(__name__)


class AuditActionType:
    """Constants for audit action types"""
    # User management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    RESET_PASSWORD = "reset_password"
    BULK_IMPORT_USERS = "bulk_import_users"
    BULK_RESET_PASSWORDS = "bulk_reset_passwords"
    ACTIVATE_USER = "activate_user"
    DEACTIVATE_USER = "deactivate_user"

    # Session management
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGOUT = "admin_logout"

    # File operations
    VIEW_FILE = "view_file"
    DOWNLOAD_FILE = "download_file"
    EDIT_FILE = "edit_file"
    DELETE_FILE = "delete_file"
    SEARCH_FILES = "search_files"

    # Grading
    GRADE_SUBMISSION = "grade_submission"
    BULK_GRADE = "bulk_grade"
    EXPORT_GRADES = "export_grades"

    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_AUDIT_LOG = "export_audit_log"


class AuditLogger:
    """Centralized audit logging for admin actions"""

    def __init__(self):
        self.db = db_manager

    def log_action(
        self,
        admin_user_id: int,
        action_type: str,
        target_user_id: Optional[int] = None,
        target_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Log an admin action to the audit log.

        Args:
            admin_user_id: ID of the admin performing the action
            action_type: Type of action (use AuditActionType constants)
            target_user_id: ID of the user being affected (if applicable)
            target_path: File path being affected (if applicable)
            details: Additional details as JSON
            ip_address: IP address of the admin

        Returns:
            bool: True if logged successfully
        """
        try:
            query = """
                INSERT INTO admin_audit_log
                (admin_user_id, action_type, target_user_id, target_path, details, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.db.execute_query(
                query,
                (
                    admin_user_id,
                    action_type,
                    target_user_id,
                    target_path,
                    json.dumps(details) if details else None,
                    ip_address
                )
            )
            logger.debug(f"Audit logged: {action_type} by user {admin_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
            return False

    def get_audit_logs(
        self,
        page: int = 1,
        limit: int = 50,
        action_type: Optional[str] = None,
        admin_user_id: Optional[int] = None,
        target_user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit logs with filtering and pagination.

        Args:
            page: Page number (1-based)
            limit: Number of records per page
            action_type: Filter by action type
            admin_user_id: Filter by admin who performed action
            target_user_id: Filter by target user
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            dict: Paginated audit logs with metadata
        """
        try:
            # Build WHERE clause
            conditions = []
            params = []

            if action_type:
                conditions.append("a.action_type = %s")
                params.append(action_type)

            if admin_user_id:
                conditions.append("a.admin_user_id = %s")
                params.append(admin_user_id)

            if target_user_id:
                conditions.append("a.target_user_id = %s")
                params.append(target_user_id)

            if start_date:
                conditions.append("a.created_at >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("a.created_at <= %s")
                params.append(end_date)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Get total count
            count_query = f"""
                SELECT COUNT(*) as total
                FROM admin_audit_log a
                WHERE {where_clause}
            """
            count_result = self.db.execute_query(count_query, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            # Get paginated results
            offset = (page - 1) * limit
            query = f"""
                SELECT
                    a.id,
                    a.action_type,
                    a.target_path,
                    a.details,
                    a.ip_address,
                    a.created_at,
                    admin_u.id as admin_user_id,
                    admin_u.username as admin_username,
                    admin_u.full_name as admin_full_name,
                    target_u.id as target_user_id,
                    target_u.username as target_username,
                    target_u.full_name as target_full_name
                FROM admin_audit_log a
                LEFT JOIN users admin_u ON a.admin_user_id = admin_u.id
                LEFT JOIN users target_u ON a.target_user_id = target_u.id
                WHERE {where_clause}
                ORDER BY a.created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            logs = self.db.execute_query(query, tuple(params))

            # Format results
            formatted_logs = []
            for log in logs:
                formatted_logs.append({
                    "id": log["id"],
                    "action_type": log["action_type"],
                    "admin_user": {
                        "id": log["admin_user_id"],
                        "username": log["admin_username"],
                        "full_name": log["admin_full_name"]
                    } if log["admin_user_id"] else None,
                    "target_user": {
                        "id": log["target_user_id"],
                        "username": log["target_username"],
                        "full_name": log["target_full_name"]
                    } if log["target_user_id"] else None,
                    "target_path": log["target_path"],
                    "details": json.loads(log["details"]) if log["details"] else None,
                    "ip_address": log["ip_address"],
                    "created_at": log["created_at"].isoformat() if log["created_at"] else None
                })

            return {
                "success": True,
                "logs": formatted_logs,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }

        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return {"success": False, "error": str(e)}

    def get_user_activity(self, user_id: int, limit: int = 100) -> Dict[str, Any]:
        """
        Get all audit log entries related to a specific user
        (as admin or as target).

        Args:
            user_id: User ID to get activity for
            limit: Maximum number of records

        Returns:
            dict: User activity logs
        """
        try:
            query = """
                SELECT
                    a.id,
                    a.action_type,
                    a.target_path,
                    a.details,
                    a.ip_address,
                    a.created_at,
                    CASE
                        WHEN a.admin_user_id = %s THEN 'performer'
                        ELSE 'target'
                    END as user_role,
                    admin_u.username as admin_username,
                    target_u.username as target_username
                FROM admin_audit_log a
                LEFT JOIN users admin_u ON a.admin_user_id = admin_u.id
                LEFT JOIN users target_u ON a.target_user_id = target_u.id
                WHERE a.admin_user_id = %s OR a.target_user_id = %s
                ORDER BY a.created_at DESC
                LIMIT %s
            """
            logs = self.db.execute_query(query, (user_id, user_id, user_id, limit))

            formatted_logs = []
            for log in logs:
                formatted_logs.append({
                    "id": log["id"],
                    "action_type": log["action_type"],
                    "user_role": log["user_role"],
                    "admin_username": log["admin_username"],
                    "target_username": log["target_username"],
                    "target_path": log["target_path"],
                    "details": json.loads(log["details"]) if log["details"] else None,
                    "ip_address": log["ip_address"],
                    "created_at": log["created_at"].isoformat() if log["created_at"] else None
                })

            return {"success": True, "activity": formatted_logs}

        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return {"success": False, "error": str(e)}

    def export_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export audit logs as CSV content.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            str: CSV content
        """
        try:
            conditions = []
            params = []

            if start_date:
                conditions.append("a.created_at >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("a.created_at <= %s")
                params.append(end_date)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT
                    a.created_at,
                    admin_u.username as admin_username,
                    a.action_type,
                    target_u.username as target_username,
                    a.target_path,
                    a.details,
                    a.ip_address
                FROM admin_audit_log a
                LEFT JOIN users admin_u ON a.admin_user_id = admin_u.id
                LEFT JOIN users target_u ON a.target_user_id = target_u.id
                WHERE {where_clause}
                ORDER BY a.created_at DESC
            """
            logs = self.db.execute_query(query, tuple(params)) if params else self.db.execute_query(query)

            # Build CSV
            csv_lines = ["timestamp,admin_username,action_type,target_username,target_path,details,ip_address"]

            for log in logs:
                details_str = json.dumps(log["details"]).replace('"', '""') if log["details"] else ""
                csv_lines.append(
                    f'"{log["created_at"]}","{log["admin_username"] or ""}","{log["action_type"]}",'
                    f'"{log["target_username"] or ""}","{log["target_path"] or ""}",'
                    f'"{details_str}","{log["ip_address"] or ""}"'
                )

            return "\n".join(csv_lines)

        except Exception as e:
            logger.error(f"Failed to export audit logs: {e}")
            return ""


# Global instance
audit_logger = AuditLogger()


# Convenience function for quick logging
def log_admin_action(
    admin_user_id: int,
    action_type: str,
    target_user_id: Optional[int] = None,
    target_path: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> bool:
    """Quick function to log an admin action"""
    return audit_logger.log_action(
        admin_user_id=admin_user_id,
        action_type=action_type,
        target_user_id=target_user_id,
        target_path=target_path,
        details=details,
        ip_address=ip_address
    )
