#!/usr/bin/env python3

import os
import sys


class Config:
    PYTHON = sys.executable

    # Use EFS mount in production, local projects directory in development
    @staticmethod
    def get_projects_path():
        """Get the correct projects path based on environment"""
        # AWS EFS - mounted at /mnt/efs in production
        if os.path.exists("/mnt/efs/pythonide-data"):
            return "/mnt/efs/pythonide-data"

        # Check custom environment variable
        if "IDE_DATA_PATH" in os.environ:
            return os.environ["IDE_DATA_PATH"]

        # Local development - use server/projects directory
        return os.path.join(os.path.dirname(__file__), "..", "projects")

    # Maintain backward compatibility
    PROJECTS = get_projects_path.__func__()
