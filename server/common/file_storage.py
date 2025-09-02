#!/usr/bin/env python3
"""
File storage management for persistent user data
Supports AWS EFS and local storage
"""
import os
import shutil
from pathlib import Path

class FileStorageManager:
    """Manages persistent file storage with AWS EFS and local fallback"""
    
    def __init__(self):
        # Determine storage path based on environment
        self.storage_root = self._get_storage_root()
        self.ide_base = os.path.join(self.storage_root, 'ide')
        
        # Ensure base directories exist
        self._ensure_base_directories()
    
    def _get_storage_root(self):
        """Get storage root - AWS EFS or local"""
        # AWS EFS - mounted at /mnt/efs in production
        if os.path.exists('/mnt/efs'):
            return '/mnt/efs/pythonide-data'
        
        # Check custom environment variable
        if 'IDE_DATA_PATH' in os.environ:
            return os.environ['IDE_DATA_PATH']
        
        # Local development - directory outside project
        return '/tmp/pythonide-data'
    
    def _ensure_base_directories(self):
        """Create base directory structure"""
        directories = [
            self.ide_base,
            os.path.join(self.ide_base, 'Local'),
            os.path.join(self.ide_base, 'Assignments'), 
            os.path.join(self.ide_base, 'Tests'),
            os.path.join(self.ide_base, 'Lecture Notes')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
        print(f"✓ File storage initialized at: {self.storage_root}")
        print(f"✓ Storage type: {'AWS EFS' if '/mnt/efs' in self.storage_root else 'Local'}")
    
    def get_user_directory(self, username):
        """Get user's local directory path"""
        return os.path.join(self.ide_base, 'Local', username)
    
    def get_assignments_directory(self):
        """Get assignments directory path"""
        return os.path.join(self.ide_base, 'Assignments')
    
    def get_tests_directory(self):
        """Get tests directory path"""  
        return os.path.join(self.ide_base, 'Tests')
    
    def get_lecture_notes_directory(self):
        """Get lecture notes directory path"""
        return os.path.join(self.ide_base, 'Lecture Notes')
    
    def create_user_directories(self, username, full_name):
        """Create directory structure for a new user"""
        user_dir = self.get_user_directory(username)
        
        # Create user subdirectories
        os.makedirs(os.path.join(user_dir, 'workspace'), exist_ok=True)
        os.makedirs(os.path.join(user_dir, 'submissions'), exist_ok=True)
        
        # Create welcome file
        welcome_path = os.path.join(user_dir, 'welcome.py')
        with open(welcome_path, 'w', encoding='utf-8') as f:
            f.write(f'# Welcome {full_name}!\nprint("Hello, {username}!")\n')
        
        return user_dir
    
    def get_storage_info(self):
        """Get information about current storage configuration"""
        is_efs = '/mnt/efs' in self.storage_root
        return {
            'storage_root': self.storage_root,
            'ide_base': self.ide_base,
            'type': 'AWS EFS' if is_efs else 'Local',
            'exists': os.path.exists(self.storage_root),
            'writable': os.access(self.storage_root, os.W_OK) if os.path.exists(self.storage_root) else False,
            'is_efs': is_efs
        }

# Global instance
file_storage = FileStorageManager()