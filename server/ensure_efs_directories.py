#!/usr/bin/env python3
"""
Ensure all student directories exist on EFS and persist across deployments
This script is idempotent - safe to run multiple times
"""
import os
import sys
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.file_storage import file_storage

def copy_local_to_efs():
    """
    Copy local directory structure to EFS if needed
    This ensures all student folders exist on EFS
    """
    # Get the EFS base path
    efs_base = Path(file_storage.ide_base)
    local_base = Path('server/projects/ide')
    
    logger.info(f"=== EFS Directory Initialization ===")
    logger.info(f"EFS Path: {efs_base}")
    logger.info(f"Storage Type: {file_storage.get_storage_info()['type']}")
    
    # Create only the directories we want to keep
    main_dirs = ['Local', 'Lecture Notes']
    for dir_name in main_dirs:
        dir_path = efs_base / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Ensured directory: {dir_path}")
    
    # Remove unwanted directories if they exist
    unwanted_dirs = ['Assignments', 'Tests', 'Testing']
    for dir_name in unwanted_dirs:
        dir_path = efs_base / dir_name
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(dir_path)
            logger.info(f"✓ Removed unwanted directory: {dir_path}")
        elif dir_path.exists():
            logger.info(f"- Found file (not directory): {dir_path}")
        else:
            logger.info(f"- Directory not found: {dir_path}")
    
    # ONLY student usernames get directories (professors have full access, no personal folders)
    student_usernames = [
        'sa8820', 'na3649', 'ntb5594', 'hrb9324', 'nd2560', 'ag11389', 'arg9667',
        'lh4052', 'jh9963', 'ch5315', 'wh2717', 'bsj5539', 'fk2248', 'nvk9963',
        'sil9056', 'hl6459', 'zl3894', 'jom2045', 'arm9283', 'zm2525', 'im2420',
        'jn3143', 'jn9106', 'djp10030', 'ap10062', 'bap9618', 'fp2331', 'srp8204',
        'agr8457', 'shs9941', 'as19217', 'mat9481', 'cw4715', 'jw9248', 'sz4766'
    ]
    
    # Admins DO NOT get personal folders - they have full system access
    # admin_usernames = ['sl7927', 'sa9082', 'et2434'] - NOT NEEDED
    
    logger.info(f"\nCreating user directories for {len(student_usernames)} students...")
    
    created_count = 0
    existing_count = 0
    
    for username in student_usernames:
        user_dir = efs_base / 'Local' / username
        workspace_dir = user_dir / 'workspace'
        
        # Check if directory exists
        if user_dir.exists():
            existing_count += 1
        else:
            user_dir.mkdir(parents=True, exist_ok=True)
            created_count += 1
            logger.info(f"  Created: {username}/")
        
        # Ensure workspace exists
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Create welcome.py if it doesn't exist
        welcome_file = user_dir / 'welcome.py'
        if not welcome_file.exists():
            with open(welcome_file, 'w') as f:
                f.write(f'''# Welcome to Python IDE, {username}!
# This is your personal workspace.

print("Hello, {username}!")
print("Welcome to Python Programming!")
print()
print("Your files are automatically saved.")
print("Only you can see files in your Local/{username}/ folder.")

# Try writing your first Python program below:
''')
            logger.info(f"  Created welcome.py for {username}")
        
        # Copy existing files from local if they exist (but don't overwrite)
        local_user_dir = local_base / 'Local' / username
        if local_user_dir.exists() and local_user_dir.is_dir():
            for item in local_user_dir.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(local_user_dir)
                    target_file = user_dir / relative_path
                    if not target_file.exists():
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_file)
                        logger.info(f"  Copied: {username}/{relative_path}")
    
    logger.info(f"\n✓ Directory check complete:")
    logger.info(f"  - {existing_count} directories already existed")
    logger.info(f"  - {created_count} directories created")
    logger.info(f"  - Total: {len(student_usernames)} user directories")
    
    # Copy content directories (Assignments, Tests, Lecture Notes)
    content_dirs = ['Assignments', 'Tests', 'Lecture Notes', 'Testing']
    for dir_name in content_dirs:
        local_dir = local_base / dir_name
        efs_dir = efs_base / dir_name
        
        if local_dir.exists() and local_dir.is_dir():
            # Copy files that don't exist on EFS
            file_count = 0
            for item in local_dir.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(local_dir)
                    target_file = efs_dir / relative_path
                    if not target_file.exists():
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_file)
                        file_count += 1
            if file_count > 0:
                logger.info(f"✓ Copied {file_count} files to {dir_name}/")
    
    # Verify persistence marker
    marker_file = efs_base / '.efs_initialized'
    if marker_file.exists():
        with open(marker_file, 'r') as f:
            last_init = f.read().strip()
        logger.info(f"\n✓ EFS was previously initialized: {last_init}")
        logger.info("✓ Data persists across deployments!")
    else:
        from datetime import datetime
        with open(marker_file, 'w') as f:
            f.write(f"Initialized: {datetime.now().isoformat()}\n")
        logger.info(f"\n✓ First time initialization complete")
    
    return True

def verify_efs_structure():
    """Verify that all expected directories exist on EFS"""
    efs_base = Path(file_storage.ide_base)
    
    issues = []
    
    # Check main directories
    for dir_name in ['Local', 'Assignments', 'Tests', 'Lecture Notes']:
        dir_path = efs_base / dir_name
        if not dir_path.exists():
            issues.append(f"Missing directory: {dir_name}")
    
    # Check user directories (students only - admins don't have personal folders)
    expected_users = [
        'sa8820', 'na3649', 'ntb5594', 'hrb9324', 'nd2560', 'ag11389', 'arg9667',
        'lh4052', 'jh9963', 'ch5315', 'wh2717', 'bsj5539', 'fk2248', 'nvk9963',
        'sil9056', 'hl6459', 'zl3894', 'jom2045', 'arm9283', 'zm2525', 'im2420',
        'jn3143', 'jn9106', 'djp10030', 'ap10062', 'bap9618', 'fp2331', 'srp8204',
        'agr8457', 'shs9941', 'as19217', 'mat9481', 'cw4715', 'jw9248', 'sz4766'
    ]
    
    missing_users = []
    for username in expected_users:
        user_dir = efs_base / 'Local' / username
        if not user_dir.exists():
            missing_users.append(username)
    
    if missing_users:
        issues.append(f"Missing user directories: {', '.join(missing_users)}")
    
    if issues:
        logger.warning("Issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False
    else:
        logger.info("✓ All expected directories exist!")
        return True

if __name__ == "__main__":
    try:
        # Run initialization
        success = copy_local_to_efs()
        
        # Verify structure
        if success:
            verify_efs_structure()
        
        logger.info("\n=== EFS Initialization Complete ===")
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)