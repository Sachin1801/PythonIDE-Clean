#!/usr/bin/env python3
"""
Script to create sz3991 directory on AWS EFS
Run this on AWS environment after RDS user has been created
"""
import os
import sys

def create_efs_directory():
    """Create sz3991 directory on AWS EFS"""
    
    username = 'sz3991'
    full_name = 'Shiwen Zhu'
    
    print("="*60)
    print("CREATING SZ3991 DIRECTORY ON AWS EFS")
    print("="*60)
    print(f"Username: {username}")
    print(f"Full Name: {full_name}")
    
    # Determine the correct path based on environment
    possible_paths = [
        '/mnt/efs/pythonide-data/ide/Local',  # AWS EFS mount
        os.environ.get('IDE_DATA_PATH', '') + '/ide/Local' if os.environ.get('IDE_DATA_PATH') else '',
        '/tmp/pythonide-data/ide/Local'  # Local fallback
    ]
    
    base_path = None
    for path in possible_paths:
        if path and os.path.exists(path):
            base_path = path
            break
    
    if not base_path:
        print("✗ Could not find Local directory base path")
        print("Tried:")
        for path in possible_paths:
            if path:
                print(f"  - {path}")
        return False
    
    print(f"📁 Base path: {base_path}")
    
    # Check if running on AWS EFS
    if '/mnt/efs' in base_path:
        print("✓ Detected AWS EFS environment")
    elif 'IDE_DATA_PATH' in base_path:
        print("✓ Detected IDE_DATA_PATH environment")
    else:
        print("⚠️  Detected local environment")
    
    user_dir = os.path.join(base_path, username)
    
    try:
        # Check if directory already exists
        if os.path.exists(user_dir):
            print(f"✓ Directory already exists: {user_dir}")
            
            # List contents
            contents = os.listdir(user_dir)
            if contents:
                print(f"  Contents: {contents}")
            else:
                print("  Directory is empty")
                
            return True
        
        # Create the directory
        print(f"📝 Creating directory: {user_dir}")
        os.makedirs(user_dir, mode=0o755, exist_ok=True)
        
        # Verify creation
        if os.path.exists(user_dir):
            print(f"✓ Successfully created directory: {user_dir}")
            
            # Set proper permissions
            os.chmod(user_dir, 0o755)
            print("✓ Set permissions to 755")
            
            # Create a welcome file
            welcome_file = os.path.join(user_dir, 'welcome.py')
            welcome_content = f'''# Welcome to your Python IDE workspace!
# This is {full_name}'s ({username}) personal directory
# 
# You can:
# - Create Python files (.py)
# - Upload files via the interface
# - Run Python scripts with the Run button
# - Use the hybrid REPL system
# 
# Happy coding! 🐍

print("Hello, {full_name}!")
print("Welcome to your Python workspace")
'''
            
            with open(welcome_file, 'w') as f:
                f.write(welcome_content)
            
            print(f"✓ Created welcome file: welcome.py")
            
            return True
        else:
            print(f"✗ Directory creation failed: {user_dir}")
            return False
            
    except Exception as e:
        print(f"✗ Error creating directory: {e}")
        return False

def verify_all_student_directories():
    """Verify all student directories exist and show summary"""
    print("\n" + "="*60)
    print("VERIFYING ALL STUDENT DIRECTORIES")
    print("="*60)
    
    # Determine base path
    possible_paths = [
        '/mnt/efs/pythonide-data/ide/Local',
        os.environ.get('IDE_DATA_PATH', '') + '/ide/Local' if os.environ.get('IDE_DATA_PATH') else '',
        '/tmp/pythonide-data/ide/Local'
    ]
    
    base_path = None
    for path in possible_paths:
        if path and os.path.exists(path):
            base_path = path
            break
    
    if not base_path:
        print("✗ Could not find Local directory")
        return False
    
    print(f"📁 Checking directories in: {base_path}")
    
    try:
        # Get all directories
        directories = [d for d in os.listdir(base_path) 
                      if os.path.isdir(os.path.join(base_path, d))]
        directories.sort()
        
        print(f"📊 Found {len(directories)} directories:")
        
        # Count by type
        admin_dirs = []
        student_dirs = []
        other_dirs = []
        
        # Known admin usernames
        admin_usernames = {'admin_editor', 'admin_viewer', 'et2434', 'sa9082', 'sl7927', 'test_admin'}
        
        for dir_name in directories:
            if dir_name in admin_usernames:
                admin_dirs.append(dir_name)
            elif dir_name.startswith('_') or dir_name in ['README.md', '.config']:
                other_dirs.append(dir_name)
            else:
                student_dirs.append(dir_name)
        
        print(f"  - Admin directories: {len(admin_dirs)}")
        print(f"  - Student directories: {len(student_dirs)}")
        print(f"  - Other directories: {len(other_dirs)}")
        
        # Check for sz3991
        if 'sz3991' in directories:
            print(f"\n✓ sz3991 directory confirmed present")
        else:
            print(f"\n✗ sz3991 directory NOT FOUND")
        
        # Show some examples
        print(f"\nStudent directories (sample):")
        for student in student_dirs[:10]:
            print(f"  - {student}")
        if len(student_dirs) > 10:
            print(f"  ... and {len(student_dirs) - 10} more")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking directories: {e}")
        return False

if __name__ == '__main__':
    print("AWS EFS Directory Creation Script")
    print("Creating directory for: sz3991 (Shiwen Zhu)")
    
    # Create the directory
    success = create_efs_directory()
    
    if success:
        print(f"\n✅ SUCCESS: sz3991 directory created on EFS")
        
        # Verify all directories
        verify_all_student_directories()
        
        print(f"\n📋 NEXT STEPS:")
        print("1. Test login with sz3991 credentials")
        print("2. Verify file operations work in the directory")
        print("3. Test Python script execution")
        
        print(f"\n🔑 LOGIN CREDENTIALS for sz3991:")
        print(f"Username: sz3991")
        print(f"Password: EaS08VX%fcp8")
        
    else:
        print(f"\n❌ FAILED: Could not create sz3991 directory")
        sys.exit(1)