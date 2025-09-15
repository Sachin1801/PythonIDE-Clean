#!/usr/bin/env python3
"""
Temporary migration handler to run user creation from web interface
REMOVE THIS FILE AFTER MIGRATION IS COMPLETE FOR SECURITY
"""
import json
import subprocess
import os
import sys
from tornado.web import RequestHandler

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager
from common.database import db_manager

class MigrationHandler(RequestHandler):
    """Run migration from web interface"""
    
    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    
    def options(self):
        self.set_status(204)
        self.finish()
    
    async def get(self):
        """Check migration status"""
        try:
            # Check how many users exist
            users = db_manager.execute_query(
                "SELECT username, role FROM users ORDER BY role DESC, username ASC"
            )
            
            result = {
                'success': True,
                'total_users': len(users),
                'users': [
                    {'username': u['username'], 'role': u['role']} 
                    for u in users[:10]  # First 10 users
                ],
                'migration_needed': len(users) < 42,
                'message': f"Found {len(users)} users. {'Migration needed.' if len(users) < 42 else 'Migration complete.'}"
            }
            
            self.write(result)
            
        except Exception as e:
            self.set_status(500)
            self.write({'success': False, 'error': str(e)})
    
    async def post(self):
        """Run the migration"""
        try:
            # Parse request body
            data = json.loads(self.request.body.decode()) if self.request.body else {}
            secret = data.get('secret', '')
            action = data.get('action', 'migrate')  # Default to migrate, but allow 'fix_directories'
            
            # Simple security check
            if secret != 'PythonIDE2025Migration':
                self.set_status(403)
                self.write({'success': False, 'error': 'Invalid secret'})
                return
            
            # Check which action to perform
            if action == 'fix_directories':
                # Run directory fix script
                result = subprocess.run(
                    ['python3', '/app/server/migrations/fix_efs_directories.py'],
                    capture_output=True,
                    text=True,
                    cwd='/app/server'
                )
            else:
                # Run migration script
                result = subprocess.run(
                    ['python3', '/app/server/migrations/create_full_class_with_consistent_passwords.py', '--environment', 'production'],
                    capture_output=True,
                    text=True,
                    cwd='/app/server'
                )
            
            # Check result
            if result.returncode == 0:
                # Get user count after migration
                users = db_manager.execute_query("SELECT COUNT(*) as count FROM users")
                user_count = users[0]['count'] if users else 0
                
                # Get admin users
                admins = db_manager.execute_query(
                    "SELECT username FROM users WHERE role = 'professor' ORDER BY username"
                )
                
                response = {
                    'success': True,
                    'message': 'Migration completed successfully',
                    'total_users': user_count,
                    'admin_users': [a['username'] for a in admins],
                    'output': result.stdout[-1000:],  # Last 1000 chars of output
                    'admin_passwords': {
                        'admin_editor': 'XuR0ibQqhw6#',
                        'sa9082': 'pXzwjLIYE20*',
                        'sl7927': '4qPg1cmJkUa!',
                        'et2434': 'evaTQRwfyhC*'
                    }
                }
            else:
                response = {
                    'success': False,
                    'error': result.stderr[-1000:],
                    'output': result.stdout[-1000:]
                }
            
            self.write(response)
            
        except Exception as e:
            self.set_status(500)
            self.write({'success': False, 'error': str(e)})

# Handler registration
def get_migration_handler():
    return (r"/api/admin/migrate", MigrationHandler)