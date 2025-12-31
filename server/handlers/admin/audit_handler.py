"""
Admin Audit Log Handler
Provides endpoints for viewing and exporting admin audit logs.
"""

import csv
import io
import logging
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.database import db_manager
from handlers.admin.auth_handler import BaseAdminHandler

logger = logging.getLogger(__name__)


class AdminAuditListHandler(BaseAdminHandler):
    """Handler for listing audit logs with pagination and filters"""

    def get(self):
        """
        GET /api/admin/audit
        Returns paginated audit logs with optional filters.

        Query params:
        - page: Page number (default 1)
        - limit: Items per page (default 20, max 100)
        - action_type: Filter by action type
        - admin_id: Filter by admin user ID
        - from_date: Filter from date (ISO format)
        - to_date: Filter to date (ISO format)
        - search: Search in target username or path
        """
        user = self.require_admin()
        if not user:
            return

        try:
            # Parse query parameters
            page = int(self.get_argument("page", "1"))
            limit = int(self.get_argument("limit", "20"))
            limit = min(limit, 100)  # Cap at 100
            offset = (page - 1) * limit

            action_type = self.get_argument("action_type", "").strip()
            admin_id = self.get_argument("admin_id", "").strip()
            from_date = self.get_argument("from_date", "").strip()
            to_date = self.get_argument("to_date", "").strip()
            search = self.get_argument("search", "").strip()

            # Build query
            where_clauses = []
            params = []

            if action_type:
                where_clauses.append("al.action_type = %s")
                params.append(action_type)

            if admin_id:
                where_clauses.append("al.admin_user_id = %s")
                params.append(int(admin_id))

            if from_date:
                where_clauses.append("al.created_at >= %s")
                params.append(from_date)

            if to_date:
                where_clauses.append("al.created_at <= %s")
                params.append(to_date + " 23:59:59")

            if search:
                where_clauses.append(
                    "(target_user.username ILIKE %s OR al.target_path ILIKE %s)"
                )
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Get total count
            count_result = db_manager.execute_query(f"""
                SELECT COUNT(*) as total
                FROM admin_audit_log al
                LEFT JOIN users target_user ON al.target_user_id = target_user.id
                WHERE {where_sql}
            """, tuple(params))
            total = count_result[0]['total'] if count_result else 0

            # Get paginated results
            query_params = params + [limit, offset]
            logs = db_manager.execute_query(f"""
                SELECT
                    al.id,
                    al.action_type,
                    al.target_user_id,
                    al.target_path,
                    al.details,
                    al.ip_address,
                    al.created_at,
                    admin_user.username as admin_username,
                    admin_user.id as admin_user_id,
                    target_user.username as target_username
                FROM admin_audit_log al
                LEFT JOIN users admin_user ON al.admin_user_id = admin_user.id
                LEFT JOIN users target_user ON al.target_user_id = target_user.id
                WHERE {where_sql}
                ORDER BY al.created_at DESC
                LIMIT %s OFFSET %s
            """, tuple(query_params))

            # Format logs for frontend
            formatted_logs = []
            for log in logs:
                formatted_logs.append({
                    "id": log['id'],
                    "action_type": log['action_type'],
                    "admin_username": log['admin_username'] or 'System',
                    "admin_user_id": log['admin_user_id'],
                    "target_username": log['target_username'],
                    "target_path": log['target_path'],
                    "details": log['details'],
                    "ip_address": log['ip_address'],
                    "created_at": log['created_at'].isoformat() if log['created_at'] else None
                })

            self.write({
                "success": True,
                "data": {
                    "logs": formatted_logs,
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "pages": (total + limit - 1) // limit
                }
            })

        except Exception as e:
            logger.error(f"Error fetching audit logs: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to fetch audit logs"})


class AdminAuditExportHandler(BaseAdminHandler):
    """Handler for exporting audit logs to CSV"""

    def get(self):
        """
        GET /api/admin/audit/export
        Exports audit logs to CSV with optional filters.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            # Parse query parameters (same as list but no pagination)
            action_type = self.get_argument("action_type", "").strip()
            admin_id = self.get_argument("admin_id", "").strip()
            from_date = self.get_argument("from_date", "").strip()
            to_date = self.get_argument("to_date", "").strip()
            search = self.get_argument("search", "").strip()

            # Build query
            where_clauses = []
            params = []

            if action_type:
                where_clauses.append("al.action_type = %s")
                params.append(action_type)

            if admin_id:
                where_clauses.append("al.admin_user_id = %s")
                params.append(int(admin_id))

            if from_date:
                where_clauses.append("al.created_at >= %s")
                params.append(from_date)

            if to_date:
                where_clauses.append("al.created_at <= %s")
                params.append(to_date + " 23:59:59")

            if search:
                where_clauses.append(
                    "(target_user.username ILIKE %s OR al.target_path ILIKE %s)"
                )
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Get all matching logs (limit to 10000 for safety)
            logs = db_manager.execute_query(f"""
                SELECT
                    al.id,
                    al.action_type,
                    al.target_path,
                    al.ip_address,
                    al.created_at,
                    admin_user.username as admin_username,
                    target_user.username as target_username
                FROM admin_audit_log al
                LEFT JOIN users admin_user ON al.admin_user_id = admin_user.id
                LEFT JOIN users target_user ON al.target_user_id = target_user.id
                WHERE {where_sql}
                ORDER BY al.created_at DESC
                LIMIT 10000
            """, tuple(params))

            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                'ID', 'Timestamp', 'Action Type', 'Admin User',
                'Target User', 'Target Path', 'IP Address'
            ])

            # Data rows
            for log in logs:
                writer.writerow([
                    log['id'],
                    log['created_at'].isoformat() if log['created_at'] else '',
                    log['action_type'],
                    log['admin_username'] or 'System',
                    log['target_username'] or '',
                    log['target_path'] or '',
                    log['ip_address'] or ''
                ])

            # Send CSV response
            csv_content = output.getvalue()
            self.set_header('Content-Type', 'text/csv')
            self.set_header('Content-Disposition',
                f'attachment; filename="audit_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"')
            self.write(csv_content)

        except Exception as e:
            logger.error(f"Error exporting audit logs: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to export audit logs"})


class AdminAuditActionTypesHandler(BaseAdminHandler):
    """Handler for getting distinct action types"""

    def get(self):
        """
        GET /api/admin/audit/action-types
        Returns list of distinct action types for filter dropdown.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            result = db_manager.execute_query("""
                SELECT DISTINCT action_type
                FROM admin_audit_log
                ORDER BY action_type
            """)

            action_types = [row['action_type'] for row in result]

            self.write({
                "success": True,
                "data": action_types
            })

        except Exception as e:
            logger.error(f"Error fetching action types: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to fetch action types"})


class AdminAuditAdminsHandler(BaseAdminHandler):
    """Handler for getting list of admins who have audit entries"""

    def get(self):
        """
        GET /api/admin/audit/admins
        Returns list of admin users who have audit log entries.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            result = db_manager.execute_query("""
                SELECT DISTINCT u.id, u.username
                FROM admin_audit_log al
                JOIN users u ON al.admin_user_id = u.id
                ORDER BY u.username
            """)

            admins = [{"id": row['id'], "username": row['username']} for row in result]

            self.write({
                "success": True,
                "data": admins
            })

        except Exception as e:
            logger.error(f"Error fetching admin users: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to fetch admin users"})
