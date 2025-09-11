#!/usr/bin/env python3
"""
Generate credentials for new students and create their directories
"""

import os
import secrets

def generate_password():
    """Generate a secure random password following the existing pattern"""
    # Pattern: Letter + 2digits + R + 3digits + Letter + 3digits + special
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    special = '@#$%&*!'
    
    password = (
        secrets.choice(letters) +          # First letter
        ''.join(secrets.choice(digits) for _ in range(2)) +  # 2 digits
        'R' +                              # R
        ''.join(secrets.choice(digits) for _ in range(3)) +  # 3 digits  
        secrets.choice(letters) +          # Middle letter
        ''.join(secrets.choice(digits) for _ in range(3)) +  # 3 digits
        secrets.choice(special)            # Special char
    )
    return password

def create_student_directory(username, full_name, base_path="server/projects/ide/Local"):
    """Create directory structure for a student"""
    try:
        user_dir = os.path.join(base_path, username)
        os.makedirs(user_dir, exist_ok=True)
        
        # Create Workspace subdirectory (consistent with existing students)
        workspace_dir = os.path.join(user_dir, 'Workspace')
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Create welcome.py with updated text
        welcome_file = os.path.join(user_dir, 'welcome.py')
        with open(welcome_file, 'w') as f:
            f.write(f'''# Welcome {username}!
# This is your personal workspace directory.
# Only you and the teaching staff can access files here.

print("Hello {username}!")
print("This is your personal Python IDE workspace.")
print("Start coding and have fun learning Python!")

# Try running this file by clicking the Run button!
''')
        
        print(f"✅ Created directory and files for {username} ({full_name})")
        return True
        
    except Exception as e:
        print(f"❌ Error creating directory for {username}: {e}")
        return False

def main():
    """Main function"""
    
    # New students data
    new_students = [
        ('eif2018', 'Ethan Flores'),
        ('ql2499', 'Nick Li'), 
        ('gs4387', 'Gursehaj Singh'),
        ('cw4973', 'Caden Wang'),
        ('jy4383', 'Jessica Yuan')
    ]
    
    print("=== Generating New Student Credentials and Directories ===\n")
    
    # Generate passwords and create directories
    student_credentials = []
    for username, full_name in new_students:
        password = generate_password()
        student_credentials.append((username, full_name, password))
        create_student_directory(username, full_name)
    
    print(f"\n=== Generated Credentials for FINAL_CREDENTIALS.txt ===")
    for username, full_name, password in student_credentials:
        print(f"{username:<12} : {password:<15} ({full_name})")
    
    return student_credentials

if __name__ == "__main__":
    credentials = main()