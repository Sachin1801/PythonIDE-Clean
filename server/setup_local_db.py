#!/usr/bin/env python3
"""
Setup local SQLite database for development
"""

import sqlite3
import bcrypt
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_database():
    """Initialize SQLite database with test users"""

    # Remove existing database if it exists
    db_path = "ide.db"
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)

    # Connect to database (creates it)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    print("Creating tables...")

    # Users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """
    )

    # Sessions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """
    )

    # Files table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            path TEXT NOT NULL,
            size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, path)
        )
    """
    )

    # Submissions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            assignment_name TEXT,
            file_path TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            grade REAL,
            feedback TEXT
        )
    """
    )

    print("Tables created successfully!")

    # Create test users
    print("\nCreating test users...")

    users = [
        {
            "username": "professor",
            "email": "professor@university.edu",
            "password": "ChangeMeASAP2024!",
            "full_name": "Prof. Smith",
            "role": "professor",
        },
        {
            "username": "sa9082",
            "email": "sa9082@nyu.edu",
            "password": "sa90822024",
            "full_name": "Sachin Adlakha",
            "role": "student",
        },
        {
            "username": "student1",
            "email": "student1@university.edu",
            "password": "student123",
            "full_name": "John Doe",
            "role": "student",
        },
        {
            "username": "student2",
            "email": "student2@university.edu",
            "password": "student123",
            "full_name": "Jane Smith",
            "role": "student",
        },
    ]

    for user in users:
        # Hash password
        password_hash = bcrypt.hashpw(user["password"].encode(), bcrypt.gensalt()).decode("utf-8")

        try:
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """,
                (user["username"], user["email"], password_hash, user["full_name"], user["role"]),
            )

            print(f"✅ Created user: {user['username']} ({user['role']}) - Password: {user['password']}")

            # Create user directory
            if user["role"] == "student":
                user_dir = f"projects/ide/Local/{user['username']}"
                os.makedirs(f"{user_dir}/workspace", exist_ok=True)
                os.makedirs(f"{user_dir}/submissions", exist_ok=True)

                # Create welcome file
                welcome_path = f"{user_dir}/welcome.py"
                with open(welcome_path, "w") as f:
                    f.write(
                        f"""# Welcome {user['full_name']}!
# This is your personal workspace

def hello():
    print("Hello, {user['username']}!")
    print("Welcome to PythonIDE")
    
if __name__ == "__main__":
    hello()
"""
                    )
                print(f"   Created workspace: {user_dir}")

        except sqlite3.IntegrityError as e:
            print(f"⚠️  User {user['username']} already exists")

    # Create shared directories
    print("\nCreating shared directories...")
    shared_dirs = ["projects/ide/Lecture Notes", "projects/ide/Assignments", "projects/ide/Tests"]

    for dir_path in shared_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

    # Create sample lecture notes
    lecture_notes_path = "projects/ide/Lecture Notes/week1_introduction.py"
    if not os.path.exists(lecture_notes_path):
        with open(lecture_notes_path, "w") as f:
            f.write(
                """# Week 1: Introduction to Python
# Professor Smith

# Variables and Data Types
name = "Python"
version = 3.9
is_awesome = True

# Lists
fruits = ["apple", "banana", "orange"]

# Functions
def greet(name):
    return f"Hello, {name}!"

# Example usage
print(greet("Students"))
print(f"Welcome to {name} {version}")
"""
            )
        print(f"✅ Created sample lecture notes")

    # Commit changes
    conn.commit()
    conn.close()

    print("\n" + "=" * 50)
    print("✅ Local database setup complete!")
    print("=" * 50)
    print("\nTest accounts:")
    print("  Professor: professor / ChangeMeASAP2024!")
    print("  Student 1: sa9082 / sa90822024")
    print("  Student 2: student1 / student123")
    print("  Student 3: student2 / student123")
    print("\nYou can now run: ./run_local.sh")


if __name__ == "__main__":
    setup_database()
