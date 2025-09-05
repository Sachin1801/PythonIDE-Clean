#!/usr/bin/env python3
"""
Simple debug script to check directory structure
"""
import os
from pathlib import Path

def debug_local_directories():
    print("🔍 Simple Directory Debug")
    print("=" * 40)
    
    base_path = Path("server/projects/ide")
    local_path = base_path / "Local"
    
    print(f"Base path: {base_path}")
    print(f"Local path: {local_path}")
    print(f"Local exists: {local_path.exists()}")
    print()
    
    if local_path.exists():
        items = list(local_path.iterdir())
        
        # Separate directories and files
        directories = [item for item in items if item.is_dir()]
        files = [item for item in items if item.is_file()]
        
        print(f"Total items: {len(items)}")
        print(f"Directories: {len(directories)}")
        print(f"Files: {len(files)}")
        print()
        
        # Check for admin directories specifically
        admin_accounts = ['sl7927', 'sa9082', 'et2434']
        print("Admin directory check:")
        for admin in admin_accounts:
            admin_path = local_path / admin
            exists = admin_path.exists()
            is_dir = admin_path.is_dir() if exists else False
            print(f"  {admin}: exists={exists}, is_dir={is_dir}")
        
        print()
        
        # List all directories (not files)
        print("All directories in Local/:")
        dir_names = sorted([d.name for d in directories])
        
        for i, name in enumerate(dir_names, 1):
            marker = " 👨‍🏫" if name in admin_accounts else " 👨‍🎓"
            print(f"  {i:2d}. {name}{marker}")
        
        print()
        print("Files in Local/:")
        for f in files:
            print(f"  - {f.name}")
    
    print()
    print("=" * 40)
    print("Check if directories are properly accessible:")
    
    # Test reading a few directories
    test_dirs = ['sa9082', 'sa8820', 'na3649']  # Mix of admin and students
    
    for dirname in test_dirs:
        dir_path = local_path / dirname
        if dir_path.exists():
            try:
                contents = list(dir_path.iterdir())
                print(f"  {dirname}/: {len(contents)} items")
                for item in contents:
                    print(f"    - {item.name}")
            except Exception as e:
                print(f"  {dirname}/: ERROR - {e}")
        else:
            print(f"  {dirname}/: NOT FOUND")

if __name__ == '__main__':
    debug_local_directories()