#!/usr/bin/env python3
"""
Create 10 test student accounts for pre-provisioning new students
These accounts can later be renamed/reassigned to actual students
"""

import os
import secrets
import csv
from datetime import datetime

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

def create_test_directories(base_path="server/projects/ide/Local"):
    """Create directory structure for test accounts"""
    success_count = 0
    
    for i in range(1, 11):
        username = f"test_{i}"
        try:
            user_dir = os.path.join(base_path, username)
            os.makedirs(user_dir, exist_ok=True)
            
            # Create Workspace subdirectory
            workspace_dir = os.path.join(user_dir, 'Workspace')
            os.makedirs(workspace_dir, exist_ok=True)
            
            # Create welcome.py
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
            
            success_count += 1
            print(f"✅ Created directory and files for {username}")
            
        except Exception as e:
            print(f"❌ Error creating directory for {username}: {e}")
    
    return success_count

def generate_test_accounts():
    """Generate test accounts with credentials"""
    
    print("=== Generating 10 Test Student Accounts ===")
    
    # Generate test accounts
    test_accounts = []
    for i in range(1, 11):
        username = f"test_{i}"
        full_name = f"Test Student {i}"
        email = f"{username}@nyu.edu"
        password = generate_password()
        
        test_accounts.append({
            'username': username,
            'full_name': full_name,
            'email': email,
            'password': password,
            'role': 'student'
        })
    
    # Create directories
    print("\nCreating directories...")
    dir_count = create_test_directories()
    
    # Create credentials file
    creds_file = "TEST_ACCOUNTS_CREDENTIALS.txt"
    print(f"\nCreating credentials file: {creds_file}")
    
    with open(creds_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("TEST STUDENT ACCOUNTS - PRE-PROVISIONED\n")
        f.write("=" * 60 + "\n\n")
        f.write("Purpose: These accounts are pre-created for quick student onboarding.\n")
        f.write("When a new student joins:\n")
        f.write("1. Update username, full_name, email in database\n")
        f.write("2. Rename directory from Local/test_X/ to Local/{new_username}/\n")
        f.write("3. Update welcome.py with new username\n")
        f.write("4. Password and files remain unchanged\n\n")
        f.write("=" * 60 + "\n")
        f.write("TEST ACCOUNTS\n")
        f.write("=" * 60 + "\n")
        
        for account in test_accounts:
            f.write(f"{account['username']:<12} : {account['password']:<15} ({account['full_name']})\n")
        
        f.write(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total accounts: {len(test_accounts)}\n")
    
    # Update CSV file
    csv_file = "adminData/consistent_class_credentials_local_20250909_164112.csv"
    print(f"Adding test accounts to CSV: {csv_file}")
    
    # Read existing CSV
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    
    # Find insertion point (before admin accounts)
    admin_start = -1
    for i, line in enumerate(lines):
        if 'admin_editor' in line:
            admin_start = i
            break
    
    if admin_start == -1:
        # Append to end if no admin section found
        admin_start = len(lines)
    
    # Insert test accounts
    new_lines = lines[:admin_start]
    
    for account in test_accounts:
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        csv_line = f"{account['username']},{account['full_name']},{account['password']},{account['role']},{account['email']},{timestamp}\n"
        new_lines.append(csv_line)
    
    new_lines.extend(lines[admin_start:])
    
    # Write updated CSV
    with open(csv_file, 'w') as f:
        f.writelines(new_lines)
    
    print(f"\n=== Summary ===")
    print(f"Test accounts generated: {len(test_accounts)}")
    print(f"Directories created: {dir_count}")
    print(f"Credentials saved to: {creds_file}")
    print(f"CSV file updated: {csv_file}")
    
    print(f"\n=== Test Account Credentials ===")
    for account in test_accounts:
        print(f"{account['username']:<12} : {account['password']:<15} ({account['full_name']})")
    
    return test_accounts

if __name__ == "__main__":
    test_accounts = generate_test_accounts()