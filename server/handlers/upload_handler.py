#!/usr/bin/env python3

import json
import tornado.web
import sys
import os
import logging
import mimetypes
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager
from common.file_storage import file_storage
from common.config import Config
from command.resource import write_project_file

logger = logging.getLogger(__name__)


class UploadFileHandler(tornado.web.RequestHandler):
    """Handle file upload requests for admin users"""
    
    def initialize(self):
        self.user_manager = UserManager()
    
    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, session-id")
    
    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()
    
    def post(self):
        """Handle file upload POST request"""
        try:
            # Get session ID from headers
            session_id = self.request.headers.get('session-id')
            if not session_id:
                self.set_status(401)
                self.write(json.dumps({
                    'success': False,
                    'error': 'No session ID provided'
                }))
                return
            
            # Validate session and get user info
            user_info = self.user_manager.validate_session(session_id)
            if not user_info:
                self.set_status(401)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Invalid session'
                }))
                return
            
            # Check if user is admin (one of the specified admin accounts)
            admin_accounts = ['sl7927', 'sa9082', 'et2434']
            if user_info['username'] not in admin_accounts:
                self.set_status(403)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Only admin users can upload files'
                }))
                return
            
            # Get form data
            project_name = self.get_argument('projectName', default=None)
            parent_path = self.get_argument('parentPath', default='/')
            filename = self.get_argument('filename', default=None)
            
            if not project_name or not filename:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'Missing required parameters: projectName, filename'
                }))
                return
            
            # Get uploaded file
            if 'file' not in self.request.files:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'No file uploaded'
                }))
                return
            
            file_info = self.request.files['file'][0]
            file_content = file_info['body']
            
            # Validate file extension
            allowed_extensions = ['.py', '.txt', '.csv', '.pdf']
            file_extension = '.' + filename.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': f'File type not allowed. Supported: {", ".join(allowed_extensions)}'
                }))
                return
            
            # Validate file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if len(file_content) > max_size:
                self.set_status(400)
                self.write(json.dumps({
                    'success': False,
                    'error': 'File too large. Maximum size: 10MB'
                }))
                return
            
            # Clean up filename (remove any path separators)
            safe_filename = os.path.basename(filename)
            
            # Construct the full path
            if parent_path == '/':
                file_path = f"/{safe_filename}"
            else:
                file_path = f"{parent_path}/{safe_filename}"
            
            # Use the same file writing logic as the existing IDE
            try:
                # Get project path
                project_path = os.path.join(file_storage.ide_base, project_name)
                full_file_path = os.path.join(project_path, file_path.lstrip('/'))
                
                # Ensure parent directory exists
                os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
                
                # Determine if it's a binary file
                is_binary = self._is_binary_file(file_extension)
                
                if is_binary:
                    # For binary files (like PDFs), save raw content
                    with open(full_file_path, 'wb') as f:
                        f.write(file_content)
                    code = 0
                else:
                    # For text files, decode content and use write_project_file
                    try:
                        content_str = file_content.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try with other encodings
                        try:
                            content_str = file_content.decode('latin-1')
                        except UnicodeDecodeError:
                            content_str = file_content.decode('utf-8', errors='replace')
                    
                    # Use the existing write_project_file function
                    code, error = write_project_file(project_path, full_file_path, content_str)
                
                if code == 0:
                    logger.info(f"File uploaded successfully: {project_name}{file_path} by {user_info['username']}")
                    self.write(json.dumps({
                        'success': True,
                        'message': f'File {safe_filename} uploaded successfully',
                        'path': file_path,
                        'project': project_name
                    }))
                else:
                    raise Exception(f"Failed to save file: error code {code}")
                    
            except Exception as e:
                logger.error(f"Error saving uploaded file: {str(e)}")
                self.set_status(500)
                self.write(json.dumps({
                    'success': False,
                    'error': f'Failed to save file: {str(e)}'
                }))
                return
            
        except Exception as e:
            logger.error(f"Error in UploadFileHandler: {str(e)}")
            self.set_status(500)
            self.write(json.dumps({
                'success': False,
                'error': 'Internal server error'
            }))
    
    def _is_binary_file(self, extension):
        """Determine if a file should be treated as binary based on its extension"""
        binary_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.zip', '.tar', '.gz']
        return extension.lower() in binary_extensions