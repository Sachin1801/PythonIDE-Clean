#!/usr/bin/env python3
"""
Create new student accounts for PythonIDE
Adds 5 new students with generated passwords
"""

import os
import sys
import secrets
import string
import psycopg2
import bcrypt
from datetime import datetime

def generate_password():
    """Generate a secure random password"""
    # Password pattern similar to existing ones: X##R###Q###[special char]
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    special = '@#$%&*!'
    
    password = (
        secrets.choice(letters) +          # X
        ''.join(secrets.choice(digits) for _ in range(2)) +  # ##
        'R' +                              # R
        ''.join(secrets.choice(digits) for _ in range(3)) +  # ###
        'Q' +                              # Q  
        ''.join(secrets.choice(digits) for _ in range(3)) +  # ###
        secrets.choice(special)            # special char
    )
    return password

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_student_user(username, full_name, password, cursor):
    """Create a student user in the database"""
    try:
        email = f"{username}@college.edu" 
        password_hash = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        ''', (username, email, password_hash, full_name, 'student'))
        
        return True
    except Exception as e:
        print(f"Error creating user {username}: {e}")
        return False

def create_student_directory(username, base_path="server/projects/ide/Local"):
    """Create directory structure for a student"""
    try:
        user_dir = os.path.join(base_path, username)
        os.makedirs(user_dir, exist_ok=True)
        
        # Create workspace subdirectory (like existing students)
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
        
        print(f"✅ Created directory and files for {username}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating directory for {username}: {e}")
        return False

def main():
    """Main function to create new students"""
    
    # New students data
    new_students = [
        ('eif2018', 'Ethan Flores'),
        ('ql2499', 'Nick Li'), 
        ('gs4387', 'Gursehaj Singh'),
        ('cw4973', 'Caden Wang'),
        ('jy4383', 'Jessica Yuan')
    ]
    
    print("=== Creating New Student Accounts ===")
    
    # Generate passwords for each student
    student_credentials = []
    for username, full_name in new_students:
        password = generate_password()
        student_credentials.append((username, full_name, password))
    
    # Connect to local database (assuming same setup as existing)
    try:
        # Try to connect to local PostgreSQL first
        conn = psycopg2.connect(
            host="localhost",
            database="pythonide", 
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()
        print("Connected to local PostgreSQL database")
        
    except Exception as e:
        print(f"Could not connect to local database: {e}")
        print("Make sure PostgreSQL is running and database 'pythonide' exists")
        sys.exit(1)
    
    # Create users in database
    success_count = 0
    for username, full_name, password in student_credentials:
        if create_student_user(username, full_name, password, cursor):
            success_count += 1
            print(f"✅ Created database user: {username}")
        else:
            print(f"❌ Failed to create database user: {username}")
    
    # Commit database changes
    conn.commit()
    cursor.close()
    conn.close()
    
    # Create directories
    dir_success_count = 0
    for username, full_name, password in student_credentials:
        if create_student_directory(username):
            dir_success_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Database users created: {success_count}/5")
    print(f"Directories created: {dir_success_count}/5")
    
    print(f"\n=== Generated Credentials ===")
    for username, full_name, password in student_credentials:
        print(f"{username:<12} : {password:<15} ({full_name})")
    
    return student_credentials

if __name__ == "__main__":
    credentials = main()