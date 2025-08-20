"""
File synchronization between filesystem and database
Keeps the files table in sync with actual filesystem
"""

import os
import sys
from pathlib import Path
import mimetypes
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database import db_manager

class FileSync:
    def __init__(self):
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
        
        print(f"FileSync initialized with base_path: {self.base_path}")
    
    def sync_user_files(self, user_id, username):
        """Sync all files for a specific user"""
        user_dir = self.base_path / 'Local' / username
        
        # Create user directory if it doesn't exist
        if not user_dir.exists():
            user_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory for user {username}: {user_dir}")
        
        # Get all files from filesystem
        filesystem_files = set()
        for file_path in user_dir.rglob('*'):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(self.base_path))
                filesystem_files.add(relative_path)
                self._update_file_record(user_id, relative_path, file_path)
        
        # Get all files from database for this user
        query = "SELECT path FROM files WHERE user_id = %s"
        db_files = self.db.execute_query(query, (user_id,))
        db_paths = {f['path'] for f in db_files} if db_files else set()
        
        # Remove deleted files from database
        deleted_files = db_paths - filesystem_files
        for path in deleted_files:
            self._remove_file_record(user_id, path)
        
        return len(filesystem_files)
    
    def _update_file_record(self, user_id, relative_path, full_path):
        """Update or create a file record in the database"""
        try:
            # Get file stats
            stats = full_path.stat()
            size = stats.st_size
            
            # Check if record exists
            query = "SELECT id FROM files WHERE user_id = %s AND path = %s"
            existing = self.db.execute_query(query, (user_id, relative_path))
            
            if existing:
                # Update existing record
                update_query = """
                    UPDATE files 
                    SET size = %s, modified_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND path = %s
                """
                self.db.execute_query(update_query, 
                    (size, user_id, relative_path))
            else:
                # Create new record
                insert_query = """
                    INSERT INTO files (user_id, path, size, created_at, modified_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                self.db.execute_query(insert_query,
                    (user_id, relative_path, size))
        except Exception as e:
            print(f"Error updating file record for {relative_path}: {e}")
    
    def _remove_file_record(self, user_id, path):
        """Remove a file record from the database"""
        query = "DELETE FROM files WHERE user_id = %s AND path = %s"
        self.db.execute_query(query, (user_id, path))
    
    def _mark_file_deleted(self, user_id, path):
        """Remove a file record from the database (backward compatibility)"""
        self._remove_file_record(user_id, path)
    
    def sync_all_users(self):
        """Sync files for all users"""
        query = "SELECT id, username FROM users WHERE is_active = true"
        users = self.db.execute_query(query)
        
        if users:
            for user in users:
                count = self.sync_user_files(user['id'], user['username'])
                print(f"Synced {count} files for user {user['username']}")
    
    def create_initial_files(self, user_id, username, role):
        """Create initial files for a new user"""
        user_dir = self.base_path / 'Local' / username
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a welcome file
        welcome_file = user_dir / 'welcome.py'
        welcome_content = f"""# Welcome to Python IDE, {username}!

# This is your personal workspace at Local/{username}/
# You can create, edit, and run Python files here.

print("Hello, {username}!")
print("Your role: {role}")

# Try running this file by clicking the Run button!

def greet(name):
    return f"Hello, {{name}}! Welcome to Python IDE."

# Test the function
print(greet("{username}"))
"""
        
        welcome_file.write_text(welcome_content)
        
        # Create a README
        readme_file = user_dir / 'README.md'
        readme_content = f"""# {username}'s Workspace

Welcome to your personal Python IDE workspace!

## Directory Structure
- `Local/{username}/` - Your personal files (full access)
- `Lecture Notes/` - Course materials (read-only for students)
- `Assignments/` - Assignment submissions
- `Tests/` - Test submissions

## Getting Started
1. Create new Python files using the file menu
2. Edit files in the code editor
3. Run Python code using the Run button
4. View output in the console below

## Tips
- Use Ctrl+S to save your work
- The console supports interactive Python (REPL)
- You can upload files using the upload button
"""
        
        readme_file.write_text(readme_content)
        
        # Sync these files to database
        self.sync_user_files(user_id, username)
        
        print(f"Created initial files for {username}")

# Global file sync instance
file_sync = FileSync()