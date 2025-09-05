import os
import sys
import uuid
import json
import base64
import mimetypes
from pathlib import Path
from datetime import datetime
import shutil
import traceback
import logging

logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database import db_manager
from common.file_storage import file_storage
from command.file_sync import file_sync

class SecureFileManager:
    def __init__(self):
        # Use the global database manager
        self.db = db_manager
        
        # Use persistent storage (AWS EFS or local)
        self.base_path = Path(file_storage.ide_base)
        
        logger.info(f"SecureFileManager initialized with persistent storage: {self.base_path}")
        logger.info(f"Storage info: {file_storage.get_storage_info()}")
    
    def get_connection(self):
        """Get database connection"""
        # Return connection from database manager
        return self.db
    
    def validate_path(self, username, role, requested_path):
        """Validate user has access to requested path"""
        logger.info(f"validate_path called: path='{requested_path}', user='{username}', role='{role}'")
        
        if not requested_path:
            logger.warning("No path provided")
            return False
        
        # Prevent directory traversal
        if '..' in str(requested_path) or str(requested_path).startswith('/'):
            logger.error(f"Directory traversal detected in path: {requested_path}")
            raise ValueError("Invalid path: directory traversal detected")
        
        # Normalize the path
        requested_path = str(requested_path).replace('\\', '/')
        
        # Check permissions based on role and path
        if role == 'professor':
            logger.info(f"Professor access granted for: {requested_path}")
            return True  # Professors have full access to everything
        
        # For students, check different directory permissions
        # 1. Full access to their own directory
        expected_prefix = f'Local/{username}/'
        if requested_path.startswith(expected_prefix) or requested_path == f'Local/{username}':
            logger.info(f"Path validated: {requested_path} matches {expected_prefix}")
            return True
        
        # 2. Read-only access to lecture notes
        if requested_path.startswith('Lecture Notes/'):
            logger.info(f"Read-only access granted for: {requested_path}")
            return 'read_only'
        
        
        # No access to other locations
        logger.warning(f"Path rejected: '{requested_path}' - no permission for student")
        return False
    
    def save_file(self, username, role, data):
        """Save file with permission checking"""
        file_path = data.get('path')
        content = data.get('content', '')
        
        permission = self.validate_path(username, role, file_path)
        if not permission or permission == 'read_only':
            return {'success': False, 'error': 'Permission denied'}
        
        # Save to filesystem
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get user_id for database sync
            query = "SELECT id FROM users WHERE username = %s"
            users = self.db.execute_query(query, (username,))
            user_id = users[0]['id'] if users else None
            
            # Handle binary files
            if data.get('binary'):
                content_bytes = base64.b64decode(content)
                full_path.write_bytes(content_bytes)
            else:
                # Write with explicit flush to ensure it's on disk
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
            
            logger.info(f"File saved: {full_path}, size: {len(content)} bytes")
            
            # Sync with database
            if user_id:
                file_sync._update_file_record(user_id, file_path, full_path)
            
            return {'success': True, 'message': 'File saved'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_file(self, username, role, data):
        """Get file with permission checking"""
        file_path = data.get('path')
        
        logger.info(f"get_file: file_path='{file_path}', username='{username}', role='{role}'")
        
        permission = self.validate_path(username, role, file_path)
        if not permission:
            logger.warning(f"get_file: Permission denied for '{file_path}'")
            return {'success': False, 'error': 'Permission denied'}
        
        full_path = self.base_path / file_path
        logger.info(f"get_file: Looking for file at: {full_path}")
        
        if not full_path.exists():
            logger.warning(f"get_file: File not found at: {full_path}")
            # Let's check what files actually exist
            parent_dir = full_path.parent
            if parent_dir.exists():
                files_in_parent = list(parent_dir.iterdir())
                logger.info(f"get_file: Files in {parent_dir}: {[f.name for f in files_in_parent]}")
            return {'success': False, 'error': 'File not found'}
        
        try:
            # Detect file type
            mime_type, _ = mimetypes.guess_type(str(full_path))
            
            # List of extensions that should be treated as binary
            binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf', '.zip', '.tar', '.gz', '.db', '.sqlite', '.ico', '.svg'}
            file_extension = full_path.suffix.lower()
            
            # Handle binary files (check mime type or extension)
            is_binary = (mime_type and not mime_type.startswith('text')) or file_extension in binary_extensions
            
            if is_binary:
                content = base64.b64encode(full_path.read_bytes()).decode('utf-8')
                # Set mime type if not detected
                if not mime_type:
                    if file_extension == '.pdf':
                        mime_type = 'application/pdf'
                    elif file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                        mime_type = f'image/{file_extension[1:]}'
                    elif file_extension == '.svg':
                        mime_type = 'image/svg+xml'
                
                return {
                    'success': True, 
                    'content': content,
                    'binary': True,
                    'mime_type': mime_type
                }
            else:
                content = full_path.read_text(encoding='utf-8')
                return {'success': True, 'content': content}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_directory(self, username, role, data):
        """List directory contents with permission checking"""
        dir_path = data.get('path', '')
        logger.info(f"Directory listing request: user={username}, role={role}, path='{dir_path}'")
        
        # Root directory is always accessible (to see top-level folders)
        if dir_path == '' or dir_path == '/':
            # Show top-level directories based on role
            if role == 'professor':
                dirs = ['Local', 'Lecture Notes']
            else:
                dirs = [f'Local/{username}', 'Lecture Notes']
            
            return {
                'success': True,
                'directories': dirs,
                'files': []
            }
        
        # Special handling for professors accessing Local directory
        if dir_path == 'Local' and role == 'professor':
            # List all student directories for professors
            logger.info(f"Professor {username} accessing Local directory")
            local_path = self.base_path / 'Local'
            logger.info(f"Local path: {local_path}, exists: {local_path.exists()}")
            
            if local_path.exists():
                try:
                    subdirs = []
                    all_items = list(local_path.iterdir())
                    logger.info(f"Found {len(all_items)} items in Local directory")
                    
                    for item in all_items:
                        if item.is_dir():
                            subdirs.append({
                                'name': item.name,
                                'path': f'Local/{item.name}'
                            })
                    
                    logger.info(f"Returning {len(subdirs)} directories for professor")
                    return {
                        'success': True,
                        'directories': sorted(subdirs, key=lambda x: x['name']),
                        'files': []
                    }
                except Exception as e:
                    logger.error(f"Error listing Local directory for professor: {e}")
                    return {'success': False, 'error': str(e)}
            else:
                logger.error(f"Local directory not found: {local_path}")
                return {'success': False, 'error': 'Local directory not found'}
        
        permission = self.validate_path(username, role, dir_path)
        if not permission:
            return {'success': False, 'error': 'Permission denied'}
        
        full_path = self.base_path / dir_path
        
        if not full_path.exists():
            return {'success': False, 'error': 'Directory not found'}
        
        if not full_path.is_dir():
            return {'success': False, 'error': 'Not a directory'}
        
        try:
            directories = []
            files = []
            
            for item in full_path.iterdir():
                if item.is_dir():
                    directories.append({
                        'name': item.name,
                        'path': str(Path(dir_path) / item.name)
                    })
                else:
                    files.append({
                        'name': item.name,
                        'path': str(Path(dir_path) / item.name),
                        'size': item.stat().st_size,
                        'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
            
            return {
                'success': True,
                'directories': sorted(directories, key=lambda x: x['name']),
                'files': sorted(files, key=lambda x: x['name'])
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_directory(self, username, role, data):
        """Create a new directory"""
        dir_path = data.get('path')
        
        permission = self.validate_path(username, role, dir_path)
        if not permission or permission == 'read_only':
            return {'success': False, 'error': 'Permission denied'}
        
        full_path = self.base_path / dir_path
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            return {'success': True, 'message': 'Directory created'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, username, role, data):
        """Delete a file or directory"""
        file_path = data.get('path')
        
        permission = self.validate_path(username, role, file_path)
        if not permission or permission == 'read_only':
            return {'success': False, 'error': 'Permission denied'}
        
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            return {'success': False, 'error': 'File not found'}
        
        try:
            # Get user_id for database sync
            query = "SELECT id FROM users WHERE username = %s"
            users = self.db.execute_query(query, (username,))
            user_id = users[0]['id'] if users else None
            
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
            
            # Mark as deleted in database
            if user_id:
                file_sync._mark_file_deleted(user_id, file_path)
            
            return {'success': True, 'message': 'File deleted'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def rename_file(self, username, role, data):
        """Rename a file or directory"""
        old_path = data.get('old_path')
        new_path = data.get('new_path')
        
        # Check permissions for both paths
        old_permission = self.validate_path(username, role, old_path)
        new_permission = self.validate_path(username, role, new_path)
        
        if not old_permission or old_permission == 'read_only':
            return {'success': False, 'error': 'Permission denied for source'}
        
        if not new_permission or new_permission == 'read_only':
            return {'success': False, 'error': 'Permission denied for destination'}
        
        # Get user_id for database sync
        query = "SELECT id FROM users WHERE username = %s"
        users = self.db.execute_query(query, (username,))
        user_id = users[0]['id'] if users else None
        
        old_full_path = self.base_path / old_path
        new_full_path = self.base_path / new_path
        
        if not old_full_path.exists():
            return {'success': False, 'error': 'Source file not found'}
        
        if new_full_path.exists():
            return {'success': False, 'error': 'Destination already exists'}
        
        try:
            old_full_path.rename(new_full_path)
            
            # Update database
            if user_id:
                # Mark old file as deleted
                file_sync._mark_file_deleted(user_id, old_path)
                # Add new file record
                file_sync._update_file_record(user_id, new_path, new_full_path)
            
            return {'success': True, 'message': 'File renamed'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    
