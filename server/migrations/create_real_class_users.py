#!/usr/bin/env python3
"""
Create REAL user accounts from the CSV file
- Remove all existing test accounts
- Create admin accounts: sl7927, sa9082, et2434
- Create student accounts for all others
"""
import sys
import os
import csv
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager
from common.database import db_manager

def remove_all_existing_users():
    """Remove ALL existing users from the database"""
    try:
        print("\n" + "="*60)
        print("REMOVING ALL EXISTING USERS")
        print("="*60)
        
        # Get all existing users
        users = db_manager.execute_query("SELECT username FROM users")
        
        if not users:
            print("No existing users found.")
            return
        
        print(f"Found {len(users)} existing users. Removing them...")
        
        for user in users:
            username = user['username']
            try:
                # Delete sessions first (foreign key constraint)
                db_manager.execute_query(
                    "DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE username = %s)",
                    (username,)
                )
                
                # Delete password reset tokens
                db_manager.execute_query(
                    "DELETE FROM password_reset_tokens WHERE user_id IN (SELECT id FROM users WHERE username = %s)",
                    (username,)
                )
                
                # Delete files metadata
                db_manager.execute_query(
                    "DELETE FROM files WHERE user_id IN (SELECT id FROM users WHERE username = %s)",
                    (username,)
                )
                
                # Delete submissions
                db_manager.execute_query(
                    "DELETE FROM submissions WHERE user_id IN (SELECT id FROM users WHERE username = %s)",
                    (username,)
                )
                
                # Finally delete the user
                db_manager.execute_query("DELETE FROM users WHERE username = %s", (username,))
                print(f"  ✓ Removed user: {username}")
                
            except Exception as e:
                print(f"  ✗ Failed to remove {username}: {e}")
        
        print("\nAll existing users have been removed.")
        
    except Exception as e:
        print(f"Error removing users: {e}")

def create_users_from_csv():
    """Create users from the CSV file"""
    manager = UserManager()
    
    # Path to CSV file
    csv_path = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 
        'adminData', 
        'class_credentials_20250901_192739.csv'
    )
    
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return 0, 0
    
    created_users = []
    failed_users = []
    
    print("\n" + "="*60)
    print("CREATING USERS FROM CSV")
    print("="*60)
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            username = row['Username'].strip()
            full_name = row['Full Name'].strip()
            password = row['Password'].strip()
            notes = row['Notes'].strip()
            
            # Skip empty rows
            if not username:
                continue
            
            # Determine role based on notes
            if "Admin Rights" in notes:
                role = 'professor'
                role_label = "ADMIN"
            else:
                role = 'student'
                role_label = "STUDENT"
            
            # Create email (assuming NYU email format)
            email = f"{username}@nyu.edu"
            
            # Create the user
            success, msg = manager.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                role=role
            )
            
            if success:
                created_users.append({
                    'username': username,
                    'full_name': full_name,
                    'password': password,
                    'role': role
                })
                print(f"  ✓ Created {role_label}: {username} ({full_name})")
            else:
                failed_users.append({
                    'username': username,
                    'full_name': full_name,
                    'error': msg
                })
                print(f"  ✗ Failed to create {username}: {msg}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Successfully created: {len(created_users)} accounts")
    print(f"Failed: {len(failed_users)} accounts")
    
    if created_users:
        print("\nCreated accounts:")
        admins = [u for u in created_users if u['role'] == 'professor']
        students = [u for u in created_users if u['role'] == 'student']
        
        if admins:
            print(f"\n  Admins ({len(admins)}):")
            for user in admins:
                print(f"    - {user['username']}: {user['full_name']}")
        
        if students:
            print(f"\n  Students ({len(students)}):")
            for user in students:
                print(f"    - {user['username']}: {user['full_name']}")
    
    if failed_users:
        print("\nFailed accounts:")
        for user in failed_users:
            print(f"  - {user['username']} ({user['full_name']}): {user['error']}")
    
    # Save summary to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_path = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 
        'adminData', 
        f'user_creation_summary_{timestamp}.txt'
    )
    
    with open(summary_path, 'w') as f:
        f.write(f"User Creation Summary - {datetime.now()}\n")
        f.write("="*60 + "\n\n")
        f.write(f"Total Created: {len(created_users)}\n")
        f.write(f"Total Failed: {len(failed_users)}\n\n")
        
        if admins:
            f.write(f"ADMINS ({len(admins)}):\n")
            for user in admins:
                f.write(f"  {user['username']}: {user['full_name']} - Password: {user['password']}\n")
        
        if students:
            f.write(f"\nSTUDENTS ({len(students)}):\n")
            for user in students:
                f.write(f"  {user['username']}: {user['full_name']} - Password: {user['password']}\n")
        
        if failed_users:
            f.write(f"\nFAILED:\n")
            for user in failed_users:
                f.write(f"  {user['username']}: {user['error']}\n")
    
    print(f"\n✓ Summary saved to: {summary_path}")
    
    return len(created_users), len(failed_users)

def verify_user_directories():
    """Verify that user directories have been created"""
    print("\n" + "="*60)
    print("VERIFYING USER DIRECTORIES")
    print("="*60)
    
    # Get the correct base path from file storage configuration
    if os.path.exists('/mnt/efs'):
        base_path = '/mnt/efs/pythonide-data/ide/Local'
    elif 'IDE_DATA_PATH' in os.environ:
        base_path = os.path.join(os.environ['IDE_DATA_PATH'], 'ide', 'Local')
    else:
        base_path = '/tmp/pythonide-data/ide/Local'
    
    if not os.path.exists(base_path):
        print(f"Base directory does not exist: {base_path}")
        print("Creating base directory structure...")
        os.makedirs(base_path, exist_ok=True)
    
    # Get all users from database
    users = db_manager.execute_query("SELECT username, role FROM users ORDER BY role, username")
    
    for user in users:
        username = user['username']
        role = user['role']
        user_dir = os.path.join(base_path, username)
        
        if os.path.exists(user_dir):
            print(f"  ✓ Directory exists: {user_dir} ({role})")
        else:
            print(f"  ✗ Directory missing: {user_dir} ({role})")
            # Create the directory
            os.makedirs(user_dir, exist_ok=True)
            print(f"    → Created directory: {user_dir}")

def explain_password_system():
    """Explain how the password system works"""
    print("\n" + "="*60)
    print("PASSWORD SYSTEM EXPLANATION")
    print("="*60)
    
    print("""
1. PASSWORD STORAGE:
   - Passwords are hashed using bcrypt (never stored in plain text)
   - Hash is stored in the 'password_hash' column in users table
   - Original passwords cannot be recovered from the hash

2. PASSWORD FORMAT (from CSV):
   - Admin accounts: Admin@{username} (e.g., Admin@sl7927)
   - Student accounts: student@{username} (e.g., student@na3649)

3. CHANGE PASSWORD:
   - Users can change their password after login
   - Requires: username, old password, new password
   - API endpoint: POST /api/auth/change-password
   - Process:
     a) Verify old password matches current hash
     b) Generate new bcrypt hash for new password
     c) Update password_hash in database

4. FORGOT PASSWORD:
   - Step 1: Request reset token
     - API: POST /api/auth/forgot-password
     - Input: username or email
     - Creates a reset token valid for 1 hour
     - Token stored in password_reset_tokens table
   
   - Step 2: Reset password with token
     - API: POST /api/auth/reset-password
     - Input: reset token + new password
     - Validates token hasn't expired
     - Updates password and marks token as used

5. SESSION MANAGEMENT:
   - Login creates a session token (24 hours validity)
   - Token stored in sessions table
   - Each request validates the session token
   - Logout invalidates the session token

6. SECURITY FEATURES:
   - Bcrypt with salt for password hashing
   - Reset tokens expire after 1 hour
   - Used tokens cannot be reused
   - Sessions expire after 24 hours
   - All tokens are cryptographically secure random strings
""")
    
    print("="*60)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Create real class user accounts from CSV')
    parser.add_argument('--no-remove', action='store_true', 
                        help='Do not remove existing users first')
    parser.add_argument('--verify-only', action='store_true',
                        help='Only verify directories, do not create users')
    parser.add_argument('--explain', action='store_true',
                        help='Explain the password system')
    
    args = parser.parse_args()
    
    if args.explain:
        explain_password_system()
        sys.exit(0)
    
    if args.verify_only:
        verify_user_directories()
        sys.exit(0)
    
    # Remove existing users unless --no-remove is specified
    if not args.no_remove:
        remove_all_existing_users()
    
    # Create new users from CSV
    created, failed = create_users_from_csv()
    
    # Verify directories
    verify_user_directories()
    
    # Explain the password system
    explain_password_system()
    
    if failed > 0:
        print(f"\n⚠️  {failed} accounts failed to create. Check the output above.")
        sys.exit(1)
    else:
        print(f"\n✅ All {created} accounts created successfully!")
        print("\n📋 NEXT STEPS:")
        print("1. Share the CSV file with users securely")
        print("2. Test login with admin account (e.g., sa9082 / Admin@sa9082)")
        print("3. Test change password functionality")
        print("4. Test forgot password functionality")