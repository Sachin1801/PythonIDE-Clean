#!/usr/bin/env python3
"""
Sync user directories to the correct location that the server uses
"""
import sys
import os
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import db_manager

def sync_user_directories():
    """Create user directories in the server's actual location"""
    
    # The server uses this path
    server_base_path = "/home/sachinadlakha/on-campus/PythonIDE-Clean/server/projects/ide/Local"
    
    # Get all users from database
    users = db_manager.execute_query("SELECT username, role FROM users ORDER BY role, username")
    
    print("="*60)
    print("SYNCING USER DIRECTORIES TO SERVER LOCATION")
    print("="*60)
    print(f"Server directory: {server_base_path}\n")
    
    created_dirs = []
    existing_dirs = []
    
    for user in users:
        username = user['username']
        role = user['role']
        
        # IMPORTANT: Only create Local directories for students
        # Admins (professors) should NEVER have Local/{username} folders
        # They have full access to everything without needing their own folder
        if role == 'student':
            user_dir = os.path.join(server_base_path, username)
            
            if not os.path.exists(user_dir):
                os.makedirs(user_dir, exist_ok=True)
                created_dirs.append((username, role))
                print(f"  ✓ Created directory for {role}: {username}")
                
                # Create a welcome file for the student
                welcome_file = os.path.join(user_dir, "welcome.py")
                with open(welcome_file, 'w') as f:
                    f.write(f'''# Welcome {username}!
# This is your personal workspace directory.
# Only you and the professors can access files here.

print("Hello {username}!")
print("This is your personal Python IDE workspace.")
print("Start coding and have fun learning Python!")

# Try running this file by clicking the Run button!
''')
                
            else:
                existing_dirs.append((username, role))
                print(f"  • Directory exists for {role}: {username}")
    
    # Remove any folders that shouldn't be there (old test users)
    print("\nChecking for old test user folders to remove...")
    
    # List of old test usernames to remove
    old_test_users = [
        'professor', 'jd1234', 'ab5678', 'mk9012', 'rs3456',
        'lj7890', 'tm2345', 'sw6789', 'dg0123', 'jm4567'
    ]
    
    # Also check for any admin folders that shouldn't exist
    admin_users = [u['username'] for u in users if u['role'] == 'professor']
    
    for item in os.listdir(server_base_path):
        item_path = os.path.join(server_base_path, item)
        
        # Skip files and special directories
        if not os.path.isdir(item_path) or item.startswith('.') or item == '_migrated_files':
            continue
        
        # Remove old test users
        if item in old_test_users:
            shutil.rmtree(item_path)
            print(f"  ✗ Removed old test user folder: {item}")
        
        # Remove admin folders if they exist (admins shouldn't have Local folders)
        elif item in admin_users:
            # Always remove admin folders - they should NEVER exist in Local/
            shutil.rmtree(item_path)
            print(f"  ✗ Removed admin folder (admins don't need Local folders): {item}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Created: {len(created_dirs)} new directories")
    print(f"Existing: {len(existing_dirs)} directories already present")
    
    if created_dirs:
        print("\nNew directories created for:")
        for username, role in created_dirs:
            print(f"  - {username} ({role})")
    
    # Ensure other required directories exist
    other_dirs = [
        "/home/sachinadlakha/on-campus/PythonIDE-Clean/server/projects/ide/Lecture Notes"
    ]
    
    print("\nEnsuring other directories exist:")
    for dir_path in other_dirs:
        os.makedirs(dir_path, exist_ok=True)
        dir_name = os.path.basename(dir_path)
        print(f"  ✓ {dir_name}")
    
    print("\n✅ Directory sync complete!")
    print("\nDirectory Structure:")
    print("  • Admins (sl7927, sa9082, et2434): Full access to all directories")
    print("  • Students: Access only to Local/{username}/")
    print("  • All users: Read-only access to Lecture Notes")

if __name__ == '__main__':
    sync_user_directories()