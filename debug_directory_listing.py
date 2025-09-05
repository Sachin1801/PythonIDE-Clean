#!/usr/bin/env python3
"""
Debug script to test directory listing logic
"""
import os
import sys
from pathlib import Path

# Add server to path
sys.path.append('server')

from command.secure_file_manager import SecureFileManager

def test_directory_listing():
    print("🔍 Debug Directory Listing")
    print("=" * 40)
    
    # Initialize file manager
    file_manager = SecureFileManager()
    
    # Test parameters
    username = 'sa9082'
    role = 'professor' 
    
    print(f"Testing with user: {username} (role: {role})")
    print(f"Base path: {file_manager.base_path}")
    print()
    
    # Check if Local directory exists
    local_path = file_manager.base_path / 'Local'
    print(f"Local directory exists: {local_path.exists()}")
    print(f"Local directory path: {local_path}")
    
    if local_path.exists():
        print(f"Local directory contents:")
        try:
            items = list(local_path.iterdir())
            print(f"Total items found: {len(items)}")
            
            dirs = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]
            
            print(f"Directories: {len(dirs)}")
            print(f"Files: {len(files)}")
            print()
            
            print("First 10 directories:")
            for i, dir_item in enumerate(sorted(dirs)[:10]):
                print(f"  {i+1}. {dir_item.name}")
                
            print("...")
            print(f"Last 3 directories:")
            for dir_item in sorted(dirs)[-3:]:
                print(f"  - {dir_item.name}")
                
        except Exception as e:
            print(f"Error listing directory: {e}")
    
    print()
    print("=" * 40)
    print("Testing SecureFileManager list_directory method:")
    
    # Test the actual method
    try:
        result = file_manager.list_directory(username, role, {'path': 'Local'})
        print(f"Method result: {result}")
        
        if result.get('success'):
            directories = result.get('directories', [])
            print(f"Returned {len(directories)} directories:")
            
            for i, dir_info in enumerate(directories[:5]):
                print(f"  {i+1}. {dir_info}")
            
            if len(directories) > 5:
                print(f"  ... and {len(directories) - 5} more")
        else:
            print(f"Error: {result.get('error')}")
            
    except Exception as e:
        print(f"Exception in list_directory: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 40)
    print("Testing root directory listing:")
    
    try:
        result = file_manager.list_directory(username, role, {'path': ''})
        print(f"Root listing result: {result}")
    except Exception as e:
        print(f"Exception in root listing: {e}")

if __name__ == '__main__':
    test_directory_listing()