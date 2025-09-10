#!/usr/bin/env python3
"""
Fix user accounts - remove incorrect ones and add correct ones
"""
import os
import sys
import bcrypt
import hashlib

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server'))

from common.database import db_manager
from utils.password_generator import PasswordGenerator

# Correct user list based on requirements
CORRECT_USERS = {
    'instructors': [
        ('sa9082', 'Sachin Adlakha', 'professor'),
        ('et2434', 'Ethan Tan', 'professor'),
        ('sl7927', 'Susan Liao', 'professor'),
    ],
    'students': [
        ('sa8820', 'Syed Ahnaf Ul Ahsan', 'student'),
        ('na3649', 'Nicole Akmetov', 'student'),
        ('ntb5594', 'Nabi Burns-Min', 'student'),
        ('hrb9324', 'Harry Byala', 'student'),
        ('nd2560', 'Nikita Drovinskiy', 'student'),
        ('ag11389', 'Adrian Garcia', 'student'),
        ('arg9667', 'Aarav Gupta', 'student'),
        ('lh4052', 'Liisa Hambazaza', 'student'),
        ('jh9963', 'Justin Hu', 'student'),
        ('ch5315', 'Rami Hu', 'student'),
        ('wh2717', 'Weijie Huang', 'student'),
        ('bsj5539', 'Maybelina J', 'student'),
        ('fk2248', 'Falisha Khan', 'student'),
        ('nvk9963', 'Neil Khandelwal', 'student'),
        ('sil9056', 'Simon Levine', 'student'),
        ('hl6459', 'Haoru Li', 'student'),
        ('zl3894', 'Jenny Li', 'student'),
        ('jom2045', 'Janell Magante', 'student'),
        ('arm9283', 'Amelia Mappus', 'student'),
        ('zm2525', 'Zhou Meng', 'student'),
        ('im2420', 'Ishaan Mukherjee', 'student'),
        ('jn3143', 'Janvi Nagpal', 'student'),
        ('jan9106', 'Jacob Nathan', 'student'),
        ('djp10030', 'Darius Partovi', 'student'),
        ('ap10062', 'Alexandar Pelletier', 'student'),
        ('bap9618', 'Benjamin Piquet', 'student'),
        ('fp2331', 'Federico Pirelli', 'student'),
        ('srp8204', 'Shaina Pollak', 'student'),
        ('agr8457', 'Alex Reber', 'student'),
        ('shs9941', 'Suzie Sanford', 'student'),
        ('as19217', 'Albert Sun', 'student'),
        ('mat9481', 'Mario Toscano', 'student'),
        ('cw4715', 'Chun-Hsiang Wang', 'student'),
        ('jw9248', 'Jingyuan Wang', 'student'),
        ('sz4766', 'Shengbo Zhang', 'student'),
    ],
    'test_accounts': [
        ('admin_editor', 'Admin Editor', 'professor'),
        ('admin_viewer', 'Admin Viewer', 'student'),
        ('test_admin', 'Test Admin', 'professor'),
        ('test_student', 'Test Student', 'student'),
    ]
}

# Users to remove (incorrect interpretations)
USERS_TO_REMOVE = [
    'dl8926', 'dl9362', 'ecs8863', 'ee7513', 'hr6456', 'jd7852', 
    'lp7436', 'mm17329', 'nyk5356', 'pm7841', 'pp8019', 'ps10497', 
    'pvd5683', 'rm11092', 'rmm9894', 'sg12493', 'sr10641', 'ss18846', 
    'ss19618', 'sw10013', 'vn5684', 'vt5675', 'xl6213', 'xs7043'
]

def generate_consistent_password(username, environment="production"):
    """Generate deterministic password based on username and environment"""
    secret_seed = "PythonIDE2025SecureClassroom"
    hash_input = f"{username}_{secret_seed}_{environment}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()
    
    # Convert hash to readable password format
    chars = []
    chars.append(hash_digest[0].upper() if hash_digest[0].isalpha() else 'X')
    chars.append(hash_digest[1:3])
    chars.append(hash_digest[3].upper() if hash_digest[3].isalpha() else 'R')
    chars.append(str(sum(ord(c) for c in hash_digest[:4]) % 10))
    chars.append(hash_digest[4:6])
    chars.append(hash_digest[6].upper() if hash_digest[6].isalpha() else 'Q')
    chars.append(hash_digest[7:9])
    chars.append(str(sum(ord(c) for c in hash_digest[6:10]) % 10))
    
    symbols = ['!', '@', '#', '$', '%', '&', '*']
    symbol_index = sum(ord(c) for c in hash_digest[:8]) % len(symbols)
    chars.append(symbols[symbol_index])
    
    return ''.join(str(c) for c in chars)

def create_or_update_user(username, full_name, role, password=None):
    """Create or update a user with the given details"""
    try:
        # Generate password if not provided
        if not password:
            # Keep existing passwords for test accounts
            if username == 'admin_editor':
                password = 'XuR0ibQqhw6#'
            elif username == 'admin_viewer':
                password = 'AdminView2025!'
            elif username == 'test_admin':
                password = 'TestAdmin2025!'
            elif username == 'test_student':
                password = 'TestStudent2025!'
            else:
                password = generate_consistent_password(username)
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Generate email
        email = f"{username}@college.edu"
        
        # Check if user exists
        existing = db_manager.execute_query(
            "SELECT id FROM users WHERE username = %s",
            (username,)
        )
        
        if existing:
            # Update existing user
            query = """
            UPDATE users 
            SET email = %s, password_hash = %s, role = %s, full_name = %s
            WHERE username = %s
            """
            db_manager.execute_query(query, (email, password_hash.decode('utf-8'), role, full_name, username))
            print(f"✓ Updated {role}: {username} ({full_name})")
        else:
            # Insert new user
            query = """
            INSERT INTO users (username, email, password_hash, role, full_name) 
            VALUES (%s, %s, %s, %s, %s)
            """
            db_manager.execute_query(query, (username, email, password_hash.decode('utf-8'), role, full_name))
            print(f"✓ Created {role}: {username} ({full_name})")
        
        return password
    except Exception as e:
        print(f"✗ Error with user {username}: {e}")
        return None

def remove_incorrect_users():
    """Remove users that were incorrectly created"""
    removed_count = 0
    for username in USERS_TO_REMOVE:
        try:
            # Check if user exists
            existing = db_manager.execute_query(
                "SELECT id FROM users WHERE username = %s",
                (username,)
            )
            
            if existing:
                # Delete user
                db_manager.execute_query(
                    "DELETE FROM users WHERE username = %s",
                    (username,)
                )
                print(f"✓ Removed incorrect user: {username}")
                removed_count += 1
        except Exception as e:
            print(f"✗ Error removing {username}: {e}")
    
    return removed_count

def main():
    print("=" * 60)
    print("FIXING USER ACCOUNTS")
    print("=" * 60)
    
    # Step 1: Remove incorrect users
    print("\nStep 1: Removing incorrect users...")
    print("-" * 40)
    removed = remove_incorrect_users()
    print(f"Removed {removed} incorrect users")
    
    # Step 2: Create/update correct users
    print("\nStep 2: Creating/updating correct users...")
    print("-" * 40)
    
    credentials = []
    
    # Process instructors
    print("\nInstructors:")
    for username, full_name, role in CORRECT_USERS['instructors']:
        password = create_or_update_user(username, full_name, role)
        if password:
            credentials.append((username, password, role, full_name))
    
    # Process students
    print("\nStudents:")
    for username, full_name, role in CORRECT_USERS['students']:
        password = create_or_update_user(username, full_name, role)
        if password:
            credentials.append((username, password, role, full_name))
    
    # Process test accounts
    print("\nTest Accounts:")
    for username, full_name, role in CORRECT_USERS['test_accounts']:
        password = create_or_update_user(username, full_name, role)
        if password:
            credentials.append((username, password, role, full_name))
    
    # Step 3: Save credentials to file
    print("\nStep 3: Saving credentials...")
    print("-" * 40)
    
    with open('FINAL_CREDENTIALS.txt', 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("PYTHONIDE FINAL CREDENTIALS\n")
        f.write("=" * 60 + "\n\n")
        
        # URL information
        if 'pythonide-classroom.tech' in os.environ.get('CUSTOM_DOMAIN', ''):
            f.write("URL: http://pythonide-classroom.tech\n")
            f.write("Admin Panel: http://pythonide-classroom.tech/admin/users\n")
        else:
            f.write("URL: http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com\n")
            f.write("Admin Panel: http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com/admin/users\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("INSTRUCTORS\n")
        f.write("=" * 60 + "\n")
        for username, password, role, full_name in credentials:
            if role == 'professor' and username not in ['admin_editor', 'test_admin']:
                f.write(f"{username:15} : {password:20} ({full_name})\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("STUDENTS\n")
        f.write("=" * 60 + "\n")
        for username, password, role, full_name in credentials:
            if role == 'student' and username not in ['admin_viewer', 'test_student']:
                f.write(f"{username:15} : {password:20} ({full_name})\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("TEST/ADMIN ACCOUNTS\n")
        f.write("=" * 60 + "\n")
        for username, password, role, full_name in credentials:
            if username in ['admin_editor', 'admin_viewer', 'test_admin', 'test_student']:
                f.write(f"{username:15} : {password:20} ({full_name})\n")
    
    # Also save as CSV
    with open('final_credentials.csv', 'w') as f:
        f.write("username,password,role,full_name,email\n")
        for username, password, role, full_name in credentials:
            f.write(f"{username},{password},{role},{full_name},{username}@college.edu\n")
    
    print("✓ Credentials saved to FINAL_CREDENTIALS.txt and final_credentials.csv")
    
    # Step 4: Verify counts
    print("\nStep 4: Verification...")
    print("-" * 40)
    
    users = db_manager.execute_query("SELECT COUNT(*) as count FROM users")
    user_count = users[0]['count'] if users else 0
    
    professors = db_manager.execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'professor'")
    prof_count = professors[0]['count'] if professors else 0
    
    students = db_manager.execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
    student_count = students[0]['count'] if students else 0
    
    print(f"Total users: {user_count}")
    print(f"Professors: {prof_count}")
    print(f"Students: {student_count}")
    
    print("\n" + "=" * 60)
    print("✅ USER ACCOUNT FIX COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()