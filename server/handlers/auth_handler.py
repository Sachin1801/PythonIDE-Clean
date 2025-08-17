#!/usr/bin/env python3

import json
import tornado.web
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager import UserManager


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
            result = self.user_manager.authenticate(username, password)
            
            if result['success']:
                self.set_status(200)
                self.write(json.dumps(result))
            else:
                self.set_status(401)
                self.write(json.dumps(result))
                
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
            session_id = data.get('session_id')
            
            if not session_id:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Session ID required'
                }))
                return
            
            # Validate session
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