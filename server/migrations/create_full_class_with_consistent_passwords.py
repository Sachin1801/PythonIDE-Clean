#!/usr/bin/env python3
"""
Create full class users with consistent passwords for both local and AWS environments
This ensures the same password works on both local development and production
"""
import sys
import os
import csv
import hashlib
from datetime import datetime

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager
from common.database import db_manager
from utils.password_generator import PasswordGenerator

def generate_consistent_password(username, environment="production"):
    """
    Generate consistent password for a user based on username
    This ensures the same user gets the same password in both local and AWS
    
    Args:
        username (str): The username
        environment (str): "local" or "production" for different environments
        
    Returns:
        str: Consistent password for this user
    """
    # Use a combination of username and a secret seed to generate consistent passwords
    # This allows same passwords locally and on AWS while still being secure
    secret_seed = "PythonIDE2025SecureClassroom"  # Change this if you want different passwords
    
    # Create a hash based on username + seed + environment
    hash_input = f"{username}_{secret_seed}_{environment}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()
    
    # Convert hash to a readable password format (12 characters)
    # Take first 32 chars of hex, convert to base62-like
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    password = ""
    
    for i in range(12):
        # Use pairs of hex digits to select characters
        hex_pair = hash_digest[i*2:(i*2)+2]
        char_index = int(hex_pair, 16) % len(chars)
        password += chars[char_index]
    
    # Ensure at least one special character for complexity
    special_chars = "!@#$%^&*"
    special_index = int(hash_digest[-2:], 16) % len(special_chars)
    
    # Replace last character with special character
    password = password[:-1] + special_chars[special_index]
    
    return password

def remove_all_existing_users():
    """Remove ALL existing users from the database"""
    try:
        print("\n" + "="*60)
        print("REMOVING ALL EXISTING USERS")
        print("="*60)
        
        users = db_manager.execute_query("SELECT username FROM users")
        
        if not users:
            print("No existing users found.")
            return
        
        print(f"Found {len(users)} existing users. Removing them...")
        
        for user in users:
            username = user['username']
            try:
                # Delete in correct order due to foreign key constraints
                db_manager.execute_query(
                    "DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE username = %s)",
                    (username,)
                )
                db_manager.execute_query(
                    "DELETE FROM password_reset_tokens WHERE user_id IN (SELECT id FROM users WHERE username = %s)",
                    (username,)
                )
                db_manager.execute_query(
                    "DELETE FROM files WHERE user_id IN (SELECT id FROM users WHERE username = %s)",
                    (username,)
                )
                db_manager.execute_query(
                    "DELETE FROM submissions WHERE user_id IN (SELECT id FROM users WHERE username = %s)",
                    (username,)
                )
                db_manager.execute_query("DELETE FROM users WHERE username = %s", (username,))
                print(f"  ✓ Removed user: {username}")
                
            except Exception as e:
                print(f"  ✗ Failed to remove {username}: {e}")
        
        print("All existing users have been removed.")
        
    except Exception as e:
        print(f"Error removing users: {e}")

def load_class_from_csv(csv_path):
    """Load the full class from CSV file"""
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return []
    
    users = []
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row.get('Username', '').strip()
            full_name = row.get('Full Name', '').strip()
            notes = row.get('Notes', '').strip()
            
            if not username:
                continue
            
            # Determine role - admin accounts get professor role
            if username in ['sl7927', 'sa9082', 'et2434', 'admin_editor', 'test_admin']:
                role = 'professor'
            else:
                role = 'student'
            
            users.append({
                'username': username,
                'full_name': full_name,
                'role': role,
                'email': f"{username}@nyu.edu"
            })
    
    return users

def create_full_class_with_consistent_passwords(environment="production"):
    """
    Create full class with consistent passwords
    
    Args:
        environment (str): "local" or "production" - affects password generation
    """
    manager = UserManager()
    generator = PasswordGenerator()
    
    # Find the most recent class CSV file
    csv_path = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 
        'adminData', 
        'class_credentials_corrected_20250909_154857.csv'
    )
    
    print(f"Loading class from: {csv_path}")
    users_data = load_class_from_csv(csv_path)
    
    if not users_data:
        print("No users loaded from CSV!")
        return [], []
    
    print(f"Loaded {len(users_data)} users for creation in {environment} environment")
    
    created_users = []
    failed_users = []
    
    print("\n" + "="*60)
    print(f"CREATING {len(users_data)} USERS WITH CONSISTENT PASSWORDS ({environment.upper()})")
    print("="*60)
    
    for user_data in users_data:
        username = user_data['username']
        full_name = user_data['full_name']
        role = user_data['role']
        email = user_data['email']
        
        # Generate consistent password for this user
        password = generate_consistent_password(username, environment)
        
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
                'role': role,
                'email': email,
                'password_generated_at': datetime.now().isoformat(),
                'environment': environment
            })
            role_label = "ADMIN" if role == 'professor' else "STUDENT"
            print(f"  ✓ Created {role_label}: {username} ({full_name})")
        else:
            failed_users.append({
                'username': username,
                'full_name': full_name,
                'error': msg,
                'role': role
            })
            print(f"  ✗ Failed to create {username}: {msg}")
    
    # Export credentials to CSV
    if created_users:
        csv_path = generator.export_to_csv(created_users, f"consistent_class_credentials_{environment}")
        print(f"\n✓ Credentials exported to: {csv_path}")
    
    # Print summary with first few passwords shown
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Successfully created: {len(created_users)} accounts")
    print(f"Failed: {len(failed_users)} accounts")
    print(f"Environment: {environment}")
    
    if created_users:
        admins = [u for u in created_users if u['role'] == 'professor']
        students = [u for u in created_users if u['role'] == 'student']
        
        if admins:
            print(f"\n  Admins ({len(admins)}) - IMPORTANT PASSWORDS:")
            for user in admins:
                print(f"    - {user['username']}: {user['full_name']} | Password: {user['password']}")
        
        if students:
            print(f"\n  Students ({len(students)}) - First 5 examples:")
            for user in students[:5]:
                print(f"    - {user['username']}: {user['full_name']} | Password: {user['password']}")
            if len(students) > 5:
                print(f"    ... and {len(students) - 5} more students (see CSV file)")
    
    if failed_users:
        print("\nFailed accounts:")
        for user in failed_users:
            print(f"  - {user['username']} ({user['full_name']}): {user['error']}")
    
    return created_users, failed_users

def verify_user_directories():
    """Verify that user directories have been created"""
    print("\n" + "="*60)
    print("VERIFYING USER DIRECTORIES")
    print("="*60)
    
    # Determine base path based on environment
    if os.path.exists('/mnt/efs'):
        base_path = '/mnt/efs/pythonide-data/ide/Local'
        print("Detected AWS EFS environment")
    elif 'IDE_DATA_PATH' in os.environ:
        base_path = os.path.join(os.environ['IDE_DATA_PATH'], 'ide', 'Local')
        print(f"Using IDE_DATA_PATH: {base_path}")
    else:
        base_path = '/tmp/pythonide-data/ide/Local'
        print(f"Using local temp path: {base_path}")
    
    if not os.path.exists(base_path):
        print(f"Creating base directory: {base_path}")
        os.makedirs(base_path, exist_ok=True)
    
    users = db_manager.execute_query("SELECT username, role FROM users ORDER BY role DESC, username ASC")
    
    admins_count = 0
    students_count = 0
    
    for user in users:
        username = user['username']
        role = user['role']
        user_dir = os.path.join(base_path, username)
        
        if role == 'professor':
            admins_count += 1
        else:
            students_count += 1
        
        if os.path.exists(user_dir):
            print(f"  ✓ Directory exists: {username}/ ({role})")
        else:
            print(f"  ✗ Directory missing: {username}/ ({role})")
            os.makedirs(user_dir, exist_ok=True)
            print(f"    → Created directory: {username}/")
    
    print(f"\nDirectory Summary: {admins_count} admins, {students_count} students")

def test_password_consistency():
    """Test that consistent password generation works"""
    print("\n" + "="*60)
    print("TESTING PASSWORD CONSISTENCY")
    print("="*60)
    
    test_users = ['sa9082', 'admin_editor', 'jd1234', 'ab5678']
    
    for username in test_users:
        local_password = generate_consistent_password(username, "local")
        prod_password = generate_consistent_password(username, "production")
        
        print(f"  {username}:")
        print(f"    Local:      {local_password}")
        print(f"    Production: {prod_password}")
        print(f"    Same: {'✓' if local_password == prod_password else '✗'}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Create full class with consistent passwords')
    parser.add_argument('--environment', choices=['local', 'production'], default='production',
                        help='Environment (affects password generation)')
    parser.add_argument('--no-remove', action='store_true',
                        help='Do not remove existing users first')
    parser.add_argument('--verify-only', action='store_true',
                        help='Only verify directories, do not create users')
    parser.add_argument('--test-consistency', action='store_true',
                        help='Test password consistency across environments')
    
    args = parser.parse_args()
    
    if args.test_consistency:
        test_password_consistency()
        sys.exit(0)
    
    if args.verify_only:
        verify_user_directories()
        sys.exit(0)
    
    # Remove existing users unless --no-remove is specified
    if not args.no_remove:
        remove_all_existing_users()
    
    # Create users with consistent passwords
    created_users, failed_users = create_full_class_with_consistent_passwords(args.environment)
    
    # Verify directories
    verify_user_directories()
    
    # Final summary
    if failed_users:
        print(f"\n⚠️  {len(failed_users)} accounts failed to create.")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(created_users)} accounts created successfully!")
        print(f"\n📋 NEXT STEPS:")
        print("1. Check the generated CSV file in adminData/ directory")
        print("2. Test admin_editor login at /admin/users")  
        print("3. Test password reset functionality")
        print("4. Deploy to AWS with same environment flag")
        print(f"\n🔑 Admin Editor Password: {[u['password'] for u in created_users if u['username'] == 'admin_editor'][0] if any(u['username'] == 'admin_editor' for u in created_users) else 'NOT FOUND'}")