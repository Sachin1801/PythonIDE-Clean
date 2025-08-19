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
from command.file_sync import file_sync

class SecureFileManager:
    def __init__(self):
        # Use the global database manager
        self.db = db_manager
        
        # Determine the correct base path based on current working directory
        # Check multiple possible paths in order of preference
        possible_paths = [
            Path('projects/ide'),          # When running from server/
            Path('server/projects/ide'),  # When running from root
            Path('../server/projects/ide'), # Alternative path
        ]
        
        self.base_path = None
        for path in possible_paths:
            if path.exists():
                self.base_path = path.resolve()  # Use absolute path
                break
        
        # If no existing path found, create it based on where we are
        if self.base_path is None:
            # Check if we're in server directory
            if Path('projects/ide').parent.exists():
                self.base_path = Path('projects/ide').resolve()
            else:
                self.base_path = Path('server/projects/ide').resolve()
            self.base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SecureFileManager initialized with base_path: {self.base_path}")
    
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
            return True  # Professors can access everything
        
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
        
        # 3. Students can read assignment descriptions but only write in their own submission folders
        if requested_path.startswith('Assignments/'):
            if f'/{username}/' in requested_path or requested_path.endswith(f'/{username}'):
                logger.info(f"Write access granted for assignment: {requested_path}")
                return True
            logger.info(f"Read-only access granted for assignment: {requested_path}")
            return 'read_only'
        
        # 4. Similar for tests
        if requested_path.startswith('Tests/'):
            if f'/{username}/' in requested_path or requested_path.endswith(f'/{username}'):
                logger.info(f"Write access granted for test: {requested_path}")
                return True
            logger.info(f"Read-only access granted for test: {requested_path}")
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
        
        # Root directory is always accessible (to see top-level folders)
        if dir_path == '' or dir_path == '/':
            # Show top-level directories based on role
            if role == 'professor':
                dirs = ['Local', 'Lecture Notes', 'Assignments', 'Tests']
            else:
                dirs = [f'Local/{username}', 'Lecture Notes', 'Assignments', 'Tests']
            
            return {
                'success': True,
                'directories': dirs,
                'files': []
            }
        
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
    
    def submit_assignment(self, username, role, data):
        """Create submission with unique ID"""
        if role != 'student':
            return {'success': False, 'error': 'Only students can submit'}
        
        file_path = data.get('path')
        assignment_name = data.get('assignment_name')
        
        # Validate the file exists and user has access
        permission = self.validate_path(username, role, file_path)
        if not permission:
            return {'success': False, 'error': 'Permission denied'}
        
        full_path = self.base_path / file_path
        if not full_path.exists():
            return {'success': False, 'error': 'File not found'}
        
        # Generate unique submission ID
        submission_id = f"{username}_{assignment_name}_{uuid.uuid4().hex[:8]}"
        
        # Copy file to submissions folder
        submission_dir = self.base_path / 'Assignments' / assignment_name / username
        submission_dir.mkdir(parents=True, exist_ok=True)
        
        submission_file = submission_dir / f"submission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2(full_path, submission_file)
        
        # Update database
        conn = self.get_connection()
        conn.execute('''
            INSERT INTO file_metadata 
            (username, file_path, is_submitted, submission_id, last_modified)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
        ''', (username, str(submission_file.relative_to(self.base_path)), submission_id))
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'submission_id': submission_id,
            'message': f'Submitted successfully! ID: {submission_id}'
        }
    
    def get_submissions(self, username, role, data):
        """Get submissions for grading (professor only)"""
        if role != 'professor':
            return {'success': False, 'error': 'Only professors can view submissions'}
        
        assignment_name = data.get('assignment_name', '')
        
        conn = self.get_connection()
        
        if assignment_name:
            cursor = conn.execute('''
                SELECT * FROM file_metadata 
                WHERE is_submitted = 1 AND file_path LIKE ?
                ORDER BY last_modified DESC
            ''', (f'%Assignments/{assignment_name}/%',))
        else:
            cursor = conn.execute('''
                SELECT * FROM file_metadata 
                WHERE is_submitted = 1
                ORDER BY last_modified DESC
            ''')
        
        submissions = []
        for row in cursor:
            submissions.append({
                'id': row['id'],
                'username': row['username'],
                'file_path': row['file_path'],
                'submission_id': row['submission_id'],
                'submitted_at': row['last_modified'],
                'grade': row['grade'],
                'feedback': row['feedback'],
                'graded_by': row['graded_by'],
                'graded_at': row['graded_at']
            })
        
        conn.close()
        return {'success': True, 'submissions': submissions}
    
    def grade_submission(self, username, role, data):
        """Grade a submission (professor only)"""
        if role != 'professor':
            return {'success': False, 'error': 'Only professors can grade'}
        
        submission_id = data.get('submission_id')
        grade = data.get('grade')
        feedback = data.get('feedback', '')
        
        conn = self.get_connection()
        conn.execute('''
            UPDATE file_metadata 
            SET grade = ?, feedback = ?, graded_by = ?, graded_at = CURRENT_TIMESTAMP
            WHERE submission_id = ?
        ''', (grade, feedback, username, submission_id))
        
        affected = conn.total_changes
        conn.commit()
        conn.close()
        
        if affected > 0:
            return {'success': True, 'message': 'Submission graded'}
        else:
            return {'success': False, 'error': 'Submission not found'}