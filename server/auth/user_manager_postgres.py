import bcrypt
import secrets
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database import db_manager

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
            
            # Create user directory
            user_dir = f"server/projects/ide/Local/{username}"
            os.makedirs(f"{user_dir}/workspace", exist_ok=True)
            os.makedirs(f"{user_dir}/submissions", exist_ok=True)
            
            # Create welcome file
            with open(f"{user_dir}/welcome.py", 'w') as f:
                f.write(f'# Welcome {full_name}!\nprint("Hello, {username}!")\n')
            
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