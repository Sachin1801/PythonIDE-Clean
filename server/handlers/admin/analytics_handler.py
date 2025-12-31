"""
Admin Analytics Handler
Provides dashboard statistics and analytics data.
"""

import logging
import os
import sys

import psutil

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.database import db_manager
from handlers.admin.auth_handler import BaseAdminHandler

logger = logging.getLogger(__name__)


class AdminDashboardHandler(BaseAdminHandler):
    """Handler for dashboard statistics"""

    def get(self):
        """
        GET /api/admin/analytics/dashboard
        Returns dashboard statistics including user counts, active sessions, and system stats.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            # Get user counts
            user_stats_result = db_manager.execute_query("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE role = 'student') as students,
                    COUNT(*) FILTER (WHERE role = 'professor') as professors
                FROM users
                WHERE is_active = true
            """)
            user_stats = user_stats_result[0] if user_stats_result else {}

            # Get active sessions count (sessions created in last 24 hours)
            session_stats_result = db_manager.execute_query("""
                SELECT COUNT(*) as active_sessions
                FROM admin_sessions
                WHERE expires_at > NOW()
            """)
            session_stats = session_stats_result[0] if session_stats_result else {}

            # Get main IDE active sessions from user sessions if table exists
            try:
                ide_sessions_result = db_manager.execute_query("""
                    SELECT COUNT(DISTINCT username) as active_ide_sessions
                    FROM users
                    WHERE last_login > NOW() - INTERVAL '1 hour'
                """)
                ide_sessions = ide_sessions_result[0] if ide_sessions_result else {}
                active_ide_sessions = ide_sessions.get('active_ide_sessions', 0) if ide_sessions else 0
            except Exception:
                active_ide_sessions = 0

            # Get system stats
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Get recent activity count (last 24 hours)
            activity_stats_result = db_manager.execute_query("""
                SELECT COUNT(*) as recent_actions
                FROM admin_audit_log
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
            activity_stats = activity_stats_result[0] if activity_stats_result else {}

            response = {
                "success": True,
                "data": {
                    "totalUsers": user_stats.get('total_users', 0) if user_stats else 0,
                    "students": user_stats.get('students', 0) if user_stats else 0,
                    "professors": user_stats.get('professors', 0) if user_stats else 0,
                    "activeSessions": (session_stats.get('active_sessions', 0) if session_stats else 0) + active_ide_sessions,
                    "memoryPercent": round(memory.percent),
                    "cpuPercent": round(cpu_percent),
                    "recentActions": activity_stats.get('recent_actions', 0) if activity_stats else 0
                }
            }

            self.write(response)

        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to fetch dashboard statistics"})


class AdminLoginTrendsHandler(BaseAdminHandler):
    """Handler for login trends data"""

    def get(self):
        """
        GET /api/admin/analytics/login-trends?days=30
        Returns daily login counts for the specified number of days.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            days = int(self.get_argument("days", "30"))
            days = min(days, 90)  # Cap at 90 days

            result = db_manager.execute_query("""
                SELECT
                    DATE(login_time) as date,
                    COUNT(*) as total_logins,
                    COUNT(*) FILTER (WHERE success = true) as successful,
                    COUNT(*) FILTER (WHERE success = false) as failed
                FROM login_history
                WHERE login_time > NOW() - INTERVAL '%s days'
                GROUP BY DATE(login_time)
                ORDER BY date
            """, (days,))

            trends = []
            for row in result:
                trends.append({
                    "date": row['date'].isoformat() if row['date'] else None,
                    "total": row['total_logins'],
                    "successful": row['successful'],
                    "failed": row['failed']
                })

            self.write({
                "success": True,
                "data": trends
            })

        except Exception as e:
            logger.error(f"Error fetching login trends: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to fetch login trends"})


class AdminExecutionTrendsHandler(BaseAdminHandler):
    """Handler for code execution trends data"""

    def get(self):
        """
        GET /api/admin/analytics/execution-trends?days=30
        Returns daily execution counts for the specified number of days.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            days = int(self.get_argument("days", "30"))
            days = min(days, 90)

            result = db_manager.execute_query("""
                SELECT
                    DATE(execution_time) as date,
                    COUNT(*) as total_executions,
                    COUNT(*) FILTER (WHERE exit_code = 0) as successful,
                    COUNT(*) FILTER (WHERE exit_code != 0) as failed,
                    AVG(duration_ms) as avg_duration
                FROM execution_log
                WHERE execution_time > NOW() - INTERVAL '%s days'
                GROUP BY DATE(execution_time)
                ORDER BY date
            """, (days,))

            trends = []
            for row in result:
                trends.append({
                    "date": row['date'].isoformat() if row['date'] else None,
                    "total": row['total_executions'],
                    "successful": row['successful'],
                    "failed": row['failed'],
                    "avg_duration": round(row['avg_duration']) if row['avg_duration'] else 0
                })

            self.write({
                "success": True,
                "data": trends
            })

        except Exception as e:
            logger.error(f"Error fetching execution trends: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to fetch execution trends"})


class AdminTopUsersHandler(BaseAdminHandler):
    """Handler for top active users"""

    def get(self):
        """
        GET /api/admin/analytics/top-users?limit=10&metric=logins
        Returns top users by specified metric (logins or executions).
        """
        user = self.require_admin()
        if not user:
            return

        try:
            limit = int(self.get_argument("limit", "10"))
            limit = min(limit, 50)
            metric = self.get_argument("metric", "logins")
            days = int(self.get_argument("days", "30"))

            if metric == "executions":
                result = db_manager.execute_query("""
                    SELECT
                        u.username,
                        u.full_name,
                        COUNT(e.id) as count,
                        COUNT(*) FILTER (WHERE e.exit_code = 0) as successful,
                        MAX(e.execution_time) as last_activity
                    FROM users u
                    LEFT JOIN execution_log e ON u.id = e.user_id
                        AND e.execution_time > NOW() - INTERVAL '%s days'
                    WHERE u.role = 'student'
                    GROUP BY u.id, u.username, u.full_name
                    HAVING COUNT(e.id) > 0
                    ORDER BY count DESC
                    LIMIT %s
                """, (days, limit))
            else:
                result = db_manager.execute_query("""
                    SELECT
                        u.username,
                        u.full_name,
                        COUNT(l.id) as count,
                        COUNT(*) FILTER (WHERE l.success = true) as successful,
                        MAX(l.login_time) as last_activity
                    FROM users u
                    LEFT JOIN login_history l ON u.id = l.user_id
                        AND l.login_time > NOW() - INTERVAL '%s days'
                    WHERE u.role = 'student'
                    GROUP BY u.id, u.username, u.full_name
                    HAVING COUNT(l.id) > 0
                    ORDER BY count DESC
                    LIMIT %s
                """, (days, limit))

            users = []
            for row in result:
                users.append({
                    "username": row['username'],
                    "full_name": row['full_name'],
                    "count": row['count'],
                    "successful": row['successful'],
                    "last_activity": row['last_activity'].isoformat() if row['last_activity'] else None
                })

            self.write({
                "success": True,
                "data": users
            })

        except Exception as e:
            logger.error(f"Error fetching top users: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to fetch top users"})


class AdminAnalyticsSummaryHandler(BaseAdminHandler):
    """Handler for analytics summary stats"""

    def get(self):
        """
        GET /api/admin/analytics/summary?days=30
        Returns summary statistics for the dashboard.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            days = int(self.get_argument("days", "30"))

            # Login stats
            login_stats = db_manager.execute_query("""
                SELECT
                    COUNT(*) as total_logins,
                    COUNT(*) FILTER (WHERE success = true) as successful_logins,
                    COUNT(DISTINCT user_id) as unique_users
                FROM login_history
                WHERE login_time > NOW() - INTERVAL '%s days'
            """, (days,))

            # Execution stats
            exec_stats = db_manager.execute_query("""
                SELECT
                    COUNT(*) as total_executions,
                    COUNT(*) FILTER (WHERE exit_code = 0) as successful_executions,
                    COUNT(DISTINCT user_id) as active_coders,
                    AVG(duration_ms) as avg_duration
                FROM execution_log
                WHERE execution_time > NOW() - INTERVAL '%s days'
            """, (days,))

            login_data = login_stats[0] if login_stats else {}
            exec_data = exec_stats[0] if exec_stats else {}

            self.write({
                "success": True,
                "data": {
                    "logins": {
                        "total": login_data.get('total_logins', 0),
                        "successful": login_data.get('successful_logins', 0),
                        "unique_users": login_data.get('unique_users', 0)
                    },
                    "executions": {
                        "total": exec_data.get('total_executions', 0),
                        "successful": exec_data.get('successful_executions', 0),
                        "active_coders": exec_data.get('active_coders', 0),
                        "avg_duration": round(exec_data.get('avg_duration', 0) or 0)
                    }
                }
            })

        except Exception as e:
            logger.error(f"Error fetching analytics summary: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to fetch analytics summary"})


class AdminRecentActivityHandler(BaseAdminHandler):
    """Handler for recent activity feed"""

    def get(self):
        """
        GET /api/admin/analytics/activity
        Returns recent admin actions for the activity feed.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            limit = int(self.get_argument("limit", "10"))
            limit = min(limit, 50)  # Cap at 50

            activities = db_manager.execute_query("""
                SELECT
                    al.id,
                    al.action_type,
                    al.target_user_id,
                    al.target_path,
                    al.details,
                    al.created_at,
                    admin_user.username as admin_username,
                    target_user.username as target_username
                FROM admin_audit_log al
                LEFT JOIN users admin_user ON al.admin_user_id = admin_user.id
                LEFT JOIN users target_user ON al.target_user_id = target_user.id
                ORDER BY al.created_at DESC
                LIMIT %s
            """, (limit,))

            # Format activities for frontend
            formatted_activities = []
            for activity in activities:
                formatted_activities.append({
                    "id": activity['id'],
                    "action_type": activity['action_type'],
                    "admin_username": activity['admin_username'] or 'System',
                    "target_username": activity['target_username'],
                    "target_path": activity['target_path'],
                    "details": activity['details'],
                    "created_at": activity['created_at'].isoformat() if activity['created_at'] else None
                })

            self.write({
                "success": True,
                "data": formatted_activities
            })

        except Exception as e:
            logger.error(f"Error fetching recent activity: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to fetch recent activity"})
