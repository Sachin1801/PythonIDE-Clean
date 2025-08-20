#!/usr/bin/env python3
"""
Setup PostgreSQL database with initial users
Works for both local and production environments
"""

import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager
from common.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_users():
    """Create initial users and directories"""
    
    user_manager = UserManager()
    
    # Test users to create
    users = [
        {
            'username': 'professor',
            'email': 'professor@university.edu',
            'password': 'ChangeMeASAP2024!',
            'full_name': 'Prof. Smith',
            'role': 'professor'
        },
        {
            'username': 'sa9082',
            'email': 'sa9082@nyu.edu',
            'password': 'sa90822024',
            'full_name': 'Sachin Adlakha',
            'role': 'student'
        },
        {
            'username': 'student1',
            'email': 'student1@university.edu',
            'password': 'student123',
            'full_name': 'John Doe',
            'role': 'student'
        },
        {
            'username': 'student2',
            'email': 'student2@university.edu',
            'password': 'student123',
            'full_name': 'Jane Smith',
            'role': 'student'
        }
    ]
    
    print("\n" + "="*50)
    print("Setting up PythonIDE Users")
    print("="*50 + "\n")
    
    for user_data in users:
        success, message = user_manager.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            full_name=user_data['full_name'],
            role=user_data['role']
        )
        
        if success:
            print(f"✅ {message}")
            print(f"   Username: {user_data['username']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Role: {user_data['role']}")
            print()
        else:
            if "already exists" in message.lower():
                print(f"⚠️  User {user_data['username']} already exists")
            else:
                print(f"❌ {message}")
    
    # Create shared directories
    print("\nCreating shared directories...")
    shared_dirs = [
        "server/projects/ide/Lecture Notes",
        "server/projects/ide/Assignments",
        "server/projects/ide/Tests"
    ]
    
    for dir_path in shared_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created/verified: {dir_path}")
    
    # Create sample lecture notes
    lecture_notes_path = "server/projects/ide/Lecture Notes/week1_introduction.py"
    if not os.path.exists(lecture_notes_path):
        with open(lecture_notes_path, 'w') as f:
            f.write('''# Week 1: Introduction to Python
# Professor Smith

# Variables and Data Types
name = "Python"
version = 3.9
is_awesome = True

# Lists
fruits = ["apple", "banana", "orange"]

# Dictionaries
student = {
    "name": "John Doe",
    "age": 20,
    "grade": "A"
}

# Functions
def greet(name):
    """A simple greeting function"""
    return f"Hello, {name}!"

# Loops
for fruit in fruits:
    print(f"I like {fruit}")

# Conditional statements
if is_awesome:
    print(f"{name} is awesome!")

# Example usage
print(greet("Students"))
print(f"Welcome to {name} {version}")
''')
        print("✅ Created sample lecture notes")
    
    print("\n" + "="*50)
    print("✅ Setup Complete!")
    print("="*50)
    print("\nTest Accounts:")
    print("  Professor: professor / ChangeMeASAP2024!")
    print("  Student 1: sa9082 / sa90822024")
    print("  Student 2: student1 / student123")
    print("  Student 3: student2 / student123")
    print("\nYou can now run: ./run_local.sh")
    print("Or access at: http://localhost:8080")

if __name__ == "__main__":
    try:
        setup_users()
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  sudo service postgresql start")
        print("\nAnd database exists:")
        print("  sudo -u postgres createdb pythonide")
        sys.exit(1)