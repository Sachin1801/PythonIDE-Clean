import bcrypt
import secrets
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database import db_manager
from common.file_storage import file_storage

class UserManager:
    def __init__(self):
        self.db = db_manager
    
    def create_user(self, username, email, password, full_name, role='student'):
        """Create new user with hashed password"""
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
        
        try:
            query = '''
                INSERT INTO users (username, email, password_hash, full_name, role) 
                VALUES (%s, %s, %s, %s, %s)
            ''' if self.db.is_postgres else '''
                INSERT INTO users (username, email, password_hash, full_name, role) 
                VALUES (?, ?, ?, ?, ?)
            '''
            
            result = self.db.execute_query(
                query,
                (username, email, password_hash, full_name, role)
            )
            
            # Create user directory using persistent storage
            user_dir = file_storage.create_user_directories(username, full_name)
            
            return True, f"User {username} created successfully"
            
        except Exception as e:
            if 'UNIQUE' in str(e) or 'duplicate' in str(e).lower():
                return False, f"User already exists: {e}"
            return False, f"Failed to create user: {e}"
    
    def authenticate(self, username, password):
        """Authenticate user and create session"""
        try:
            query = "SELECT * FROM users WHERE username = %s" if self.db.is_postgres else \
                    "SELECT * FROM users WHERE username = ?"
            
            users = self.db.execute_query(query, (username,))
            
            if not users:
                return None, "Invalid username or password"
            
            user = users[0]
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"User type: {type(user)}")
            logger.info(f"User data: {user}")
            
            # Access as dictionary (works for both PostgreSQL RealDictCursor and SQLite Row)
            try:
                password_hash = user['password_hash']
                user_id = user['id']
                user_role = user['role']
                user_full_name = user.get('full_name', user['username'])
            except (KeyError, TypeError) as e:
                logger.error(f"Error accessing user data: {e}")
                logger.error(f"User object: {user}")
                logger.error(f"User type: {type(user)}")
                raise
            
            if not bcrypt.checkpw(password.encode(), password_hash.encode()):
                return None, "Invalid username or password"
            
            # Create session token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            session_query = '''
                INSERT INTO sessions (user_id, token, expires_at) 
                VALUES (%s, %s, %s)
            ''' if self.db.is_postgres else '''
                INSERT INTO sessions (user_id, token, expires_at) 
                VALUES (?, ?, ?)
            '''
            
            self.db.execute_query(
                session_query,
                (user_id, token, expires_at)
            )
            
            # Update last login
            update_query = "UPDATE users SET last_login = %s WHERE id = %s" if self.db.is_postgres else \
                          "UPDATE users SET last_login = ? WHERE id = ?"
            
            self.db.execute_query(update_query, (datetime.now(), user_id))
            
            return {
                'user_id': user_id,
                'username': username,
                'token': token,
                'role': user_role,
                'full_name': user_full_name,
                'expires_at': expires_at.isoformat()
            }, None
            
        except Exception as e:
            return None, f"Authentication failed: {e}"
    
    def validate_session(self, token):
        """Validate session token"""
        try:
            query = '''
                SELECT s.*, u.username, u.role, u.full_name 
                FROM sessions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.token = %s AND s.is_active = true AND s.expires_at > %s
            ''' if self.db.is_postgres else '''
                SELECT s.*, u.username, u.role, u.full_name 
                FROM sessions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.token = ? AND s.is_active = 1 AND s.expires_at > ?
            '''
            
            sessions = self.db.execute_query(query, (token, datetime.now()))
            
            if not sessions:
                return None
            
            session = sessions[0]
            
            # With RealDictCursor, this will always be a dict
            return {
                'user_id': session['user_id'],
                'username': session['username'],
                'role': session['role'],
                'full_name': session.get('full_name', session['username'])
            }
                
        except Exception as e:
            print(f"Session validation error: {e}")
            return None
    
    def logout(self, token):
        """Invalidate a session token"""
        try:
            query = "UPDATE sessions SET is_active = false WHERE token = %s" if self.db.is_postgres else \
                    "UPDATE sessions SET is_active = 0 WHERE token = ?"
            
            self.db.execute_query(query, (token,))
            return True
        except Exception as e:
            print(f"Logout error: {e}")
            return False
    
    def renew_session(self, token):
        """Extend session expiration by 24 hours (sliding window)"""
        try:
            # First validate the session is still active
            session = self.validate_session(token)
            if not session:
                return {'success': False, 'error': 'Invalid session'}
            
            # Extend expiration by 24 hours from now
            new_expires_at = datetime.now() + timedelta(hours=24)
            
            query = "UPDATE sessions SET expires_at = %s WHERE token = %s AND is_active = true" if self.db.is_postgres else \
                    "UPDATE sessions SET expires_at = ? WHERE token = ? AND is_active = 1"
            
            self.db.execute_query(query, (new_expires_at, token))
            
            return {
                'success': True,
                'expires_at': new_expires_at.isoformat(),
                'message': 'Session renewed for 24 hours'
            }
            
        except Exception as e:
            print(f"Session renewal error: {e}")
            return {'success': False, 'error': 'Failed to renew session'}
    
    def change_password(self, username, old_password, new_password):
        """Change user password"""
        try:
            # Get user and verify old password
            query = "SELECT password_hash FROM users WHERE username = %s" if self.db.is_postgres else \
                    "SELECT password_hash FROM users WHERE username = ?"
            
            users = self.db.execute_query(query, (username,))
            
            if not users:
                return {'success': False, 'error': 'User not found'}
            
            user = users[0]
            password_hash = user['password_hash']
            
            # Check old password
            if not bcrypt.checkpw(old_password.encode(), password_hash.encode()):
                return {'success': False, 'error': 'Invalid old password'}
            
            # Hash new password
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
            
            # Update password
            update_query = "UPDATE users SET password_hash = %s WHERE username = %s" if self.db.is_postgres else \
                          "UPDATE users SET password_hash = ? WHERE username = ?"
            
            self.db.execute_query(update_query, (new_hash.decode(), username))
            
            return {'success': True, 'message': 'Password changed successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_password_reset_token(self, username_or_email):
        """Create a password reset token for a user"""
        try:
            # Find user by username or email
            query = '''
                SELECT id, username, email, full_name 
                FROM users 
                WHERE username = %s OR email = %s
            ''' if self.db.is_postgres else '''
                SELECT id, username, email, full_name 
                FROM users 
                WHERE username = ? OR email = ?
            '''
            
            users = self.db.execute_query(query, (username_or_email, username_or_email))
            
            if not users:
                return {'success': False, 'error': 'User not found'}
            
            user = users[0]
            user_id = user['id']
            
            # Generate secure reset token
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
            
            # Store reset token in database
            token_query = '''
                INSERT INTO password_reset_tokens (user_id, token, expires_at) 
                VALUES (%s, %s, %s)
            ''' if self.db.is_postgres else '''
                INSERT INTO password_reset_tokens (user_id, token, expires_at) 
                VALUES (?, ?, ?)
            '''
            
            self.db.execute_query(token_query, (user_id, reset_token, expires_at))
            
            return {
                'success': True,
                'token': reset_token,
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'expires_at': expires_at.isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def reset_password_with_token(self, token, new_password):
        """Reset password using a valid reset token"""
        try:
            # Find valid reset token
            query = '''
                SELECT prt.*, u.username 
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = %s AND prt.is_used = false AND prt.expires_at > %s
            ''' if self.db.is_postgres else '''
                SELECT prt.*, u.username 
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = ? AND prt.is_used = 0 AND prt.expires_at > ?
            '''
            
            tokens = self.db.execute_query(query, (token, datetime.now()))
            
            if not tokens:
                return {'success': False, 'error': 'Invalid or expired reset token'}
            
            token_record = tokens[0]
            user_id = token_record['user_id']
            username = token_record['username']
            
            # Hash new password
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
            
            # Update password
            update_query = "UPDATE users SET password_hash = %s WHERE id = %s" if self.db.is_postgres else \
                          "UPDATE users SET password_hash = ? WHERE id = ?"
            
            self.db.execute_query(update_query, (new_hash.decode(), user_id))
            
            # Mark token as used
            mark_used_query = "UPDATE password_reset_tokens SET is_used = true WHERE token = %s" if self.db.is_postgres else \
                             "UPDATE password_reset_tokens SET is_used = 1 WHERE token = ?"
            
            self.db.execute_query(mark_used_query, (token,))
            
            return {'success': True, 'message': f'Password reset successfully for {username}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def admin_force_password_reset(self, admin_username, target_username, new_password):
        """
        Admin-only function to force reset any user's password without knowing old password
        Only admin_editor role can use this function
        
        Args:
            admin_username (str): Username of the admin performing the action
            target_username (str): Username of the user whose password to reset
            new_password (str): New password to set
            
        Returns:
            dict: Success status and message
        """
        try:
            # Verify admin has permission
            admin_query = "SELECT role FROM users WHERE username = %s" if self.db.is_postgres else \
                         "SELECT role FROM users WHERE username = ?"
            
            admin_users = self.db.execute_query(admin_query, (admin_username,))
            
            if not admin_users:
                return {'success': False, 'error': 'Admin user not found'}
            
            admin_role = admin_users[0]['role']
            
            # Only admin_editor can force reset passwords
            if admin_username != 'admin_editor':
                return {'success': False, 'error': 'Insufficient permissions. Only admin_editor can force reset passwords.'}
            
            # Check if target user exists
            target_query = "SELECT id, username, full_name FROM users WHERE username = %s" if self.db.is_postgres else \
                          "SELECT id, username, full_name FROM users WHERE username = ?"
            
            target_users = self.db.execute_query(target_query, (target_username,))
            
            if not target_users:
                return {'success': False, 'error': f'Target user {target_username} not found'}
            
            target_user = target_users[0]
            target_user_id = target_user['id']
            target_full_name = target_user['full_name']
            
            # Hash the new password
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
            
            # Update password
            update_query = "UPDATE users SET password_hash = %s WHERE id = %s" if self.db.is_postgres else \
                          "UPDATE users SET password_hash = ? WHERE id = ?"
            
            self.db.execute_query(update_query, (new_hash.decode(), target_user_id))
            
            # Invalidate all existing sessions for the target user (force re-login)
            invalidate_sessions_query = "UPDATE sessions SET is_active = false WHERE user_id = %s" if self.db.is_postgres else \
                                       "UPDATE sessions SET is_active = 0 WHERE user_id = ?"
            
            self.db.execute_query(invalidate_sessions_query, (target_user_id,))
            
            return {
                'success': True, 
                'message': f'Password reset successfully for {target_username} ({target_full_name}). User will need to log in again.',
                'target_user': target_username,
                'target_full_name': target_full_name
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to reset password: {str(e)}'}
    
    def get_all_users_for_admin(self, admin_username):
        """
        Get list of all users (admin-only function)
        Only admin_editor role can access this
        
        Args:
            admin_username (str): Username of the admin requesting data
            
        Returns:
            dict: Success status and user list
        """
        try:
            # Verify admin has permission
            admin_query = "SELECT role FROM users WHERE username = %s" if self.db.is_postgres else \
                         "SELECT role FROM users WHERE username = ?"
            
            admin_users = self.db.execute_query(admin_query, (admin_username,))
            
            if not admin_users:
                return {'success': False, 'error': 'Admin user not found'}
            
            # Only admin_editor can access user list
            if admin_username != 'admin_editor':
                return {'success': False, 'error': 'Insufficient permissions. Only admin_editor can access user management.'}
            
            # Get all users
            users_query = """
                SELECT id, username, email, full_name, role, created_at, last_login
                FROM users 
                ORDER BY role DESC, username ASC
            """
            
            users = self.db.execute_query(users_query)
            
            # Convert to list of dictionaries for JSON serialization
            users_list = []
            for user in users:
                users_list.append({
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'role': user['role'],
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'last_login': user['last_login'].isoformat() if user['last_login'] else None
                })
            
            return {
                'success': True,
                'users': users_list,
                'total_count': len(users_list)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to get users: {str(e)}'}