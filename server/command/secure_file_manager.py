import os
import sqlite3
import uuid
import json
import base64
import mimetypes
from pathlib import Path
from datetime import datetime
import shutil
import traceback

class SecureFileManager:
    def __init__(self):
        # Adjust path based on where we're running from
        if os.path.exists('ide.db'):
            db_path = 'ide.db'
        elif os.path.exists('server/ide.db'):
            db_path = 'server/ide.db'
        else:
            db_path = 'ide.db'
            
        self.db_path = db_path
        self.base_path = Path('server/projects/ide')
        if not self.base_path.exists():
            self.base_path = Path('projects/ide')
        
        # Ensure base directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def validate_path(self, username, role, requested_path):
        """Validate user has access to requested path"""
        
        # Prevent directory traversal
        if '..' in str(requested_path) or str(requested_path).startswith('/'):
            raise ValueError("Invalid path: directory traversal detected")
        
        # Normalize the path
        requested_path = str(requested_path).replace('\\', '/')
        
        # Check permissions based on role and path
        if role == 'professor':
            return True  # Professors can access everything
        
        # Students can only access specific paths
        if requested_path.startswith(f'Local/{username}/'):
            return True
        
        # Read-only access to lecture notes
        if requested_path.startswith('Lecture Notes/'):
            return 'read_only'
        
        # Students can read assignment descriptions but only write in their own submission folders
        if requested_path.startswith('Assignments/'):
            if f'/{username}/' in requested_path or requested_path.endswith(f'/{username}'):
                return True
            return 'read_only'
        
        # Similar for tests
        if requested_path.startswith('Tests/'):
            if f'/{username}/' in requested_path or requested_path.endswith(f'/{username}'):
                return True
            return 'read_only'
        
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
            # Handle binary files
            if data.get('binary'):
                content_bytes = base64.b64decode(content)
                full_path.write_bytes(content_bytes)
            else:
                full_path.write_text(content, encoding='utf-8')
            
            # Update database
            conn = self.get_connection()
            conn.execute('''
                INSERT OR REPLACE INTO file_metadata 
                (username, file_path, last_modified)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (username, file_path))
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'File saved'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_file(self, username, role, data):
        """Get file with permission checking"""
        file_path = data.get('path')
        
        permission = self.validate_path(username, role, file_path)
        if not permission:
            return {'success': False, 'error': 'Permission denied'}
        
        full_path = self.base_path / file_path
        
        if not full_path.exists():
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
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
            
            # Remove from database
            conn = self.get_connection()
            conn.execute(
                'DELETE FROM file_metadata WHERE username = ? AND file_path = ?',
                (username, file_path)
            )
            conn.commit()
            conn.close()
            
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
        
        old_full_path = self.base_path / old_path
        new_full_path = self.base_path / new_path
        
        if not old_full_path.exists():
            return {'success': False, 'error': 'Source file not found'}
        
        if new_full_path.exists():
            return {'success': False, 'error': 'Destination already exists'}
        
        try:
            old_full_path.rename(new_full_path)
            
            # Update database
            conn = self.get_connection()
            conn.execute('''
                UPDATE file_metadata 
                SET file_path = ? 
                WHERE username = ? AND file_path = ?
            ''', (new_path, username, old_path))
            conn.commit()
            conn.close()
            
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