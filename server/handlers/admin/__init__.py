"""
Admin Panel API Handlers
All handlers for the admin panel (admin.pythonide-classroom.tech)
"""

from .auth_handler import AdminAuthHandler, AdminSessionHandler
from .users_handler import AdminUsersHandler, AdminUserDetailHandler, AdminBulkImportHandler
from .analytics_handler import (
    AdminDashboardHandler,
    AdminRecentActivityHandler,
    AdminLoginTrendsHandler,
    AdminExecutionTrendsHandler,
    AdminTopUsersHandler,
    AdminAnalyticsSummaryHandler
)
from .audit_handler import (
    AdminAuditListHandler,
    AdminAuditExportHandler,
    AdminAuditActionTypesHandler,
    AdminAuditAdminsHandler
)
from .files_handler import (
    AdminStudentsListHandler,
    AdminBrowseFilesHandler,
    AdminFileContentHandler,
    AdminFileDownloadHandler,
    AdminFileSearchHandler
)

# Collect all admin handlers for registration
def get_admin_handlers():
    """Return list of admin handler routes for registration in server.py"""
    return [
        # Authentication
        (r"/api/admin/auth/login", AdminAuthHandler),
        (r"/api/admin/auth/logout", AdminAuthHandler),
        (r"/api/admin/auth/session", AdminSessionHandler),

        # User Management
        (r"/api/admin/users", AdminUsersHandler),
        (r"/api/admin/users/([0-9]+)", AdminUserDetailHandler),
        (r"/api/admin/users/([0-9]+)/reset-password", AdminUserDetailHandler),
        (r"/api/admin/users/bulk-import", AdminBulkImportHandler),
        (r"/api/admin/users/export", AdminUsersHandler),

        # Analytics & Dashboard
        (r"/api/admin/analytics/dashboard", AdminDashboardHandler),
        (r"/api/admin/analytics/activity", AdminRecentActivityHandler),
        (r"/api/admin/analytics/login-trends", AdminLoginTrendsHandler),
        (r"/api/admin/analytics/execution-trends", AdminExecutionTrendsHandler),
        (r"/api/admin/analytics/top-users", AdminTopUsersHandler),
        (r"/api/admin/analytics/summary", AdminAnalyticsSummaryHandler),

        # Audit Log
        (r"/api/admin/audit", AdminAuditListHandler),
        (r"/api/admin/audit/export", AdminAuditExportHandler),
        (r"/api/admin/audit/action-types", AdminAuditActionTypesHandler),
        (r"/api/admin/audit/admins", AdminAuditAdminsHandler),

        # File Browser
        (r"/api/admin/files/students", AdminStudentsListHandler),
        (r"/api/admin/files/browse", AdminBrowseFilesHandler),
        (r"/api/admin/files/content", AdminFileContentHandler),
        (r"/api/admin/files/download", AdminFileDownloadHandler),
        (r"/api/admin/files/search", AdminFileSearchHandler),
    ]
