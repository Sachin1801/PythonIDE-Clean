"""
Admin Panel API Handlers
All handlers for the admin panel (admin.pythonide-classroom.tech)
"""

from .auth_handler import AdminAuthHandler, AdminSessionHandler
from .users_handler import AdminUsersHandler, AdminUserDetailHandler, AdminBulkImportHandler

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
    ]
