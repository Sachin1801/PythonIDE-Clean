#!/usr/bin/env python3
"""
Fix EFS directories for correct usernames
This runs on the AWS container to fix user directories
"""
import os
import sys
import shutil

# List of ALL correct users
CORRECT_USERS = [
    # Instructors
    'sa9082', 'et2434', 'sl7927',
    # Students
    'sa8820', 'na3649', 'ntb5594', 'hrb9324', 'nd2560', 'ag11389', 
    'arg9667', 'lh4052', 'jh9963', 'ch5315', 'wh2717', 'bsj5539', 
    'fk2248', 'nvk9963', 'sil9056', 'hl6459', 'zl3894', 'jom2045',
    'arm9283', 'zm2525', 'im2420', 'jn3143', 'jan9106', 'djp10030',
    'ap10062', 'bap9618', 'fp2331', 'srp8204', 'agr8457', 'shs9941',
    'as19217', 'mat9481', 'cw4715', 'jw9248', 'sz4766',
    # Test accounts
    'admin_editor', 'admin_viewer', 'test_admin', 'test_student'
]

# Directories to remove (incorrect usernames)
INCORRECT_DIRS = [
    'dl8926', 'dl9362', 'ecs8863', 'ee7513', 'hr6456', 'jd7852',
    'lp7436', 'mm17329', 'nyk5356', 'pm7841', 'pp8019', 'ps10497',
    'pvd5683', 'rm11092', 'rmm9894', 'sg12493', 'sr10641', 'ss18846',
    'ss19618', 'sw10013', 'vn5684', 'vt5675', 'xl6213', 'xs7043'
]

def main():
    """Fix user directories in Local/ folder"""
    
    # Determine the base path - prioritize EFS if available
    ide_data_path = '/tmp/pythonide-data'
    if os.path.exists('/mnt/efs/pythonide-data'):
        ide_data_path = '/mnt/efs/pythonide-data'
        print(f"✓ Using AWS EFS storage at: {ide_data_path}")
    else:
        print(f"⚠ Using local storage at: {ide_data_path}")
    
    local_dir = os.path.join(ide_data_path, 'projects', 'ide', 'Local')
    
    print(f"Working with directory: {local_dir}")
    print("=" * 60)
    
    # Create Local directory if it doesn't exist
    os.makedirs(local_dir, exist_ok=True)
    
    # Step 1: Remove incorrect directories
    print("Step 1: Removing incorrect directories...")
    print("-" * 40)
    removed_count = 0
    for dirname in INCORRECT_DIRS:
        dir_path = os.path.join(local_dir, dirname)
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"✓ Removed incorrect directory: {dirname}")
                removed_count += 1
            except Exception as e:
                print(f"✗ Error removing {dirname}: {e}")
    print(f"Removed {removed_count} incorrect directories")
    
    # Step 2: Create correct directories
    print("\nStep 2: Creating correct user directories...")
    print("-" * 40)
    created_count = 0
    existing_count = 0
    
    for username in CORRECT_USERS:
        user_dir = os.path.join(local_dir, username)
        if not os.path.exists(user_dir):
            try:
                os.makedirs(user_dir, exist_ok=True)
                # Create a README file in each new directory
                readme_path = os.path.join(user_dir, 'README.txt')
                with open(readme_path, 'w') as f:
                    f.write(f"Personal workspace for {username}\n")
                    f.write("=" * 40 + "\n")
                    f.write("This is your personal directory for Python IDE.\n")
                    f.write("All your files will be saved here.\n")
                    f.write(f"Created: {os.environ.get('TZ', 'UTC')} time\n")
                print(f"✓ Created directory: {username}")
                created_count += 1
            except Exception as e:
                print(f"✗ Error creating directory for {username}: {e}")
        else:
            print(f"• Directory exists: {username}")
            existing_count += 1
    
    print(f"\nCreated {created_count} new directories")
    print(f"Found {existing_count} existing directories")
    
    # Step 3: List all directories in Local/
    print("\nStep 3: Final directory listing...")
    print("-" * 40)
    
    if os.path.exists(local_dir):
        all_dirs = sorted([d for d in os.listdir(local_dir) 
                          if os.path.isdir(os.path.join(local_dir, d))])
        
        print(f"Total directories in Local/: {len(all_dirs)}")
        
        # Check for any unexpected directories
        unexpected = set(all_dirs) - set(CORRECT_USERS)
        if unexpected:
            print(f"\n⚠️  WARNING: Found unexpected directories: {sorted(unexpected)}")
        
        # Check for missing directories
        missing = set(CORRECT_USERS) - set(all_dirs)
        if missing:
            print(f"\n⚠️  WARNING: Missing directories: {sorted(missing)}")
        
        if not unexpected and not missing:
            print("\n✅ All directories are correct!")
            print(f"✅ Total: {len(all_dirs)} directories match expected {len(CORRECT_USERS)} users")
    
    print("\n" + "=" * 60)
    print("DIRECTORY FIX COMPLETE!")
    print("=" * 60)
    
    return {
        'removed': removed_count,
        'created': created_count,
        'existing': existing_count,
        'total': len(all_dirs) if os.path.exists(local_dir) else 0
    }

if __name__ == "__main__":
    result = main()
    print(f"\nSummary: Removed {result['removed']}, Created {result['created']}, Total {result['total']} directories")