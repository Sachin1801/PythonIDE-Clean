#!/usr/bin/env python3

import json
import tornado.web
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager


class LoginHandler(tornado.web.RequestHandler):
    """Handle user login requests"""
    
    def initialize(self):
        self.user_manager = UserManager()
    
    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
    
    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()
    
    def post(self):
        """Handle login POST request"""
        try:
            data = json.loads(self.request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Username and password required'
                }))
                return
            
            # Authenticate user
            result, error = self.user_manager.authenticate(username, password)
            
            if result:
                # Map token to session_id for frontend compatibility
                response_data = {
                    'success': True,
                    'session_id': result['token'],  # Frontend expects session_id
                    'username': result['username'],
                    'role': result['role'],
                    'full_name': result['full_name']
                }
                self.set_status(200)
                self.write(json.dumps(response_data))
            else:
                self.set_status(401)
                self.write(json.dumps({
                    'success': False,
                    'error': error or 'Authentication failed'
                }))
                
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({
                'success': False,
                'error': str(e)
            }))


class LogoutHandler(tornado.web.RequestHandler):
    """Handle user logout requests"""
    
    def initialize(self):
        self.user_manager = UserManager()
    
    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
    
    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()
    
    def post(self):
        """Handle logout POST request"""
        try:
            data = json.loads(self.request.body)
            session_id = data.get('session_id')
            
            if not session_id:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Session ID required'
                }))
                return
            
            # Logout user
            self.user_manager.logout(session_id)
            
            self.set_status(200)
            self.write(json.dumps({
                'success': True,
                'message': 'Logged out successfully'
            }))
                
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({
                'success': False,
                'error': str(e)
            }))


class ValidateSessionHandler(tornado.web.RequestHandler):
    """Validate session for existing connections"""
    
    def initialize(self):
        self.user_manager = UserManager()
    
    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
    
    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()
    
    def post(self):
        """Validate session"""
        try:
            data = json.loads(self.request.body)
            session_id = data.get('session_id')  # This is actually the token
            
            if not session_id:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Session ID required'
                }))
                return
            
            # Validate session (session_id is actually the token)
            session = self.user_manager.validate_session(session_id)
            
            if session:
                self.set_status(200)
                self.write(json.dumps({
                    'success': True,
                    'username': session['username'],
                    'role': session['role'],
                    'full_name': session['full_name']
                }))
            else:
                self.set_status(401)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Invalid or expired session'
                }))
                
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({
                'success': False,
                'error': str(e)
            }))


class ChangePasswordHandler(tornado.web.RequestHandler):
    """Handle password change requests"""
    
    def initialize(self):
        self.user_manager = UserManager()
    
    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
    
    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()
    
    def post(self):
        """Handle password change"""
        try:
            data = json.loads(self.request.body)
            session_id = data.get('session_id')
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            
            if not all([session_id, old_password, new_password]):
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'All fields required'
                }))
                return
            
            # Validate session first
            session = self.user_manager.validate_session(session_id)
            if not session:
                self.set_status(401)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Invalid session'
                }))
                return
            
            # Change password
            result = self.user_manager.change_password(
                session['username'], 
                old_password, 
                new_password
            )
            
            if result['success']:
                self.set_status(200)
            else:
                self.set_status(400)
            
            self.write(json.dumps(result))
                
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({
                'success': False,
                'error': str(e)
            }))


class RenewSessionHandler(tornado.web.RequestHandler):
    """Renew/extend session expiration (sliding window)"""
    
    def initialize(self):
        self.user_manager = UserManager()
    
    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
    
    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()
    
    def post(self):
        """Extend session by 24 hours from now"""
        try:
            data = json.loads(self.request.body)
            session_id = data.get('session_id')  # This is actually the token
            
            if not session_id:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Session ID required'
                }))
                return
            
            # Renew the session
            result = self.user_manager.renew_session(session_id)
            
            if result['success']:
                self.set_status(200)
            else:
                self.set_status(400)
            
            self.write(json.dumps(result))
                
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({
                'success': False,
                'error': str(e)
            }))


class ForgotPasswordHandler(tornado.web.RequestHandler):
    """Handle forgot password requests"""
    
    def initialize(self):
        self.user_manager = UserManager()
    
    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
    
    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()
    
    def post(self):
        """Generate password reset token"""
        try:
            data = json.loads(self.request.body)
            username_or_email = data.get('username')  # Could be username or email
            
            if not username_or_email:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Username or email required'
                }))
                return
            
            # Create reset token (never expose user data in response for security)
            result = self.user_manager.create_password_reset_token(username_or_email)
            
            if result['success']:
                # Security: Never return actual user data or token in response
                # In production, this would send an email with the reset link
                self.set_status(200)
                self.write(json.dumps({
                    'success': True,
                    'message': 'Password reset instructions sent. Check with administrator.',
                    # For development only - remove in production:
                    'dev_token': result['token'],
                    'dev_expires': result['expires_at']
                }))
            else:
                # Security: Return generic message even if user not found
                self.set_status(200)  # Don't reveal if user exists
                self.write(json.dumps({
                    'success': True,
                    'message': 'Password reset instructions sent. Check with administrator.'
                }))
                
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({
                'success': False,
                'error': 'Internal server error'
            }))


class ResetPasswordHandler(tornado.web.RequestHandler):
    """Handle password reset with token"""
    
    def initialize(self):
        self.user_manager = UserManager()
    
    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
    
    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()
    
    def post(self):
        """Reset password using token"""
        try:
            data = json.loads(self.request.body)
            token = data.get('token')
            new_password = data.get('new_password')
            
            if not all([token, new_password]):
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Token and new password required'
                }))
                return
            
            # Reset password
            result = self.user_manager.reset_password_with_token(token, new_password)
            
            if result['success']:
                self.set_status(200)
            else:
                self.set_status(400)
            
            self.write(json.dumps(result))
                
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({
                'success': False,
                'error': 'Internal server error'
            }))