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
        self.ide_base = os.path.join(self.storage_root, "ide")

        # Ensure base directories exist
        self._ensure_base_directories()

    def _get_storage_root(self):
        """Get storage root - prioritize environment variable, then EFS, then local"""
        # Check custom environment variable first (set in Docker)
        if "IDE_DATA_PATH" in os.environ:
            return os.environ["IDE_DATA_PATH"]

        # AWS EFS - mounted at /mnt/efs in production
        if os.path.exists("/mnt/efs/pythonide-data"):
            return "/mnt/efs/pythonide-data"

        # Local development - directory outside project
        return "/tmp/pythonide-data"

    def _ensure_base_directories(self):
        """Create base directory structure"""
        directories = [
            self.ide_base,
            os.path.join(self.ide_base, "Local"),
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

        print(f"✓ File storage initialized at: {self.storage_root}")
        print(f"✓ Storage type: {'AWS EFS' if '/mnt/efs' in self.storage_root else 'Local'}")

    def get_user_directory(self, username):
        """Get user's local directory path"""
        return os.path.join(self.ide_base, "Local", username)


    def validate_user_folder_name(self, username):
        """Validate that folder name matches username for exam environment"""
        # Check if we're in exam mode
        is_exam_mode = os.environ.get("IS_EXAM_MODE", "false").lower() == "true"

        if is_exam_mode:
            # In exam mode, ensure username starts with "exam_"
            if not username.startswith("exam_"):
                raise ValueError(f"Invalid folder name in exam environment: {username}. Expected format: exam_{{netid}}")

        return True

    def create_user_directories(self, username, full_name):
        """Create directory structure for a new user"""
        # Validate folder naming (exam mode check)
        self.validate_user_folder_name(username)

        user_dir = self.get_user_directory(username)
        is_exam_mode = os.environ.get("IS_EXAM_MODE", "false").lower() == "true"

        # Skip workspace/ and welcome.py in exam mode
        if not is_exam_mode:
            os.makedirs(os.path.join(user_dir, "workspace"), exist_ok=True)
            welcome_path = os.path.join(user_dir, "welcome.py")
            with open(welcome_path, "w", encoding="utf-8") as f:
                f.write(f'# Welcome {full_name}!\nprint("Hello, {username}!")\n')

        # Always create these subdirectories
        os.makedirs(os.path.join(user_dir, "Lecture_Examples"), exist_ok=True)
        os.makedirs(os.path.join(user_dir, "submissions"), exist_ok=True)

        return user_dir

    def get_storage_info(self):
        """Get information about current storage configuration"""
        is_efs = "/mnt/efs" in self.storage_root
        return {
            "storage_root": self.storage_root,
            "ide_base": self.ide_base,
            "type": "AWS EFS" if is_efs else "Local",
            "exists": os.path.exists(self.storage_root),
            "writable": os.access(self.storage_root, os.W_OK) if os.path.exists(self.storage_root) else False,
            "is_efs": is_efs,
        }


# Global instance
file_storage = FileStorageManager()
