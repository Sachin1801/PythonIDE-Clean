#!/usr/bin/env python3
"""
Initialize LOCAL test accounts for Docker development
Creates simple test accounts for local testing that won't interfere with production
"""
import os
import sys
import psycopg2
import bcrypt
from datetime import datetime


def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def init_local_test_accounts():
    """Initialize local test accounts for Docker testing"""
    print("=" * 60)
    print("LOCAL TEST ACCOUNT INITIALIZATION")
    print("=" * 60)

    try:
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            print("❌ DATABASE_URL not set!")
            return

        print(f"Connecting to database...")

        # Parse the database URL
        import re
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^/:]+)(?::(\d+))?/(.+)", db_url)
        if not match:
            print("❌ Invalid DATABASE_URL format")
            return

        user, password, host, port, database = match.groups()
        port = port or "5432"

        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()

        # Define LOCAL test accounts (simple passwords for easy testing)
        local_test_accounts = [
            # Local test students (easy to remember)
            ("local_student1", "test123", "Local Test Student 1", "student", "local_student1@test.local"),
            ("local_student2", "test123", "Local Test Student 2", "student", "local_student2@test.local"),
            ("local_student3", "test123", "Local Test Student 3", "student", "local_student3@test.local"),

            # Local test professor
            ("local_prof", "prof123", "Local Test Professor", "professor", "local_prof@test.local"),
        ]

        print(f"\n{'=' * 60}")
        print("CREATING/UPDATING LOCAL TEST ACCOUNTS")
        print(f"{'=' * 60}\n")

        # Create or update test accounts
        created_count = 0
        updated_count = 0

        for username, plain_password, full_name, role, email in local_test_accounts:
            password_hash = hash_password(plain_password)

            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing = cursor.fetchone()

            try:
                if existing:
                    # Update existing user
                    cursor.execute("""
                        UPDATE users
                        SET password_hash = %s, full_name = %s, role = %s, email = %s, is_active = true
                        WHERE username = %s
                    """, (password_hash, full_name, role, email, username))
                    print(f"✓ Updated {role:10} | {username:20} | {plain_password}")
                    updated_count += 1
                else:
                    # Create new user
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, full_name, role)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (username, email, password_hash, full_name, role))
                    print(f"✓ Created {role:10} | {username:20} | {plain_password}")
                    created_count += 1

            except Exception as e:
                print(f"❌ Error with {username}: {e}")

        conn.commit()

        # Create directories for test users
        print(f"\n{'=' * 60}")
        print("CREATING USER DIRECTORIES")
        print(f"{'=' * 60}\n")

        create_test_directories(local_test_accounts)

        # Summary
        print(f"\n{'=' * 60}")
        print("✅ LOCAL TEST ACCOUNT INITIALIZATION COMPLETE")
        print(f"{'=' * 60}")
        print(f"Created: {created_count} | Updated: {updated_count}")

        # Verify total count
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'local_%'")
        local_count = cursor.fetchone()[0]
        print(f"Total local test accounts in database: {local_count}")

        print(f"\n{'=' * 60}")
        print("📋 LOCAL TEST CREDENTIALS (localhost:10086)")
        print(f"{'=' * 60}")
        print(f"{'ROLE':<12} | {'USERNAME':<20} | {'PASSWORD':<10}")
        print("-" * 60)
        for username, password, _, role, _ in local_test_accounts:
            print(f"{role.upper():<12} | {username:<20} | {password:<10}")
        print(f"{'=' * 60}\n")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ ERROR during test account initialization: {e}")
        import traceback
        traceback.print_exc()


def create_test_directories(test_users):
    """Create directories for test users"""
    try:
        # Determine the base path
        if "IDE_DATA_PATH" in os.environ:
            base_path = os.path.join(os.environ["IDE_DATA_PATH"], "ide", "Local")
        else:
            base_path = "/app/server/projects/ide/Local"

        print(f"Creating directories at: {base_path}\n")

        # Create base directory
        os.makedirs(base_path, exist_ok=True)

        # Create directories for each test user
        for username, _, full_name, _, _ in test_users:
            user_dir = os.path.join(base_path, username)
            os.makedirs(user_dir, exist_ok=True)

            # Create welcome file
            welcome_file = os.path.join(user_dir, "welcome.py")
            if not os.path.exists(welcome_file):
                with open(welcome_file, "w") as f:
                    f.write(f'''# Welcome to PythonIDE - Local Test Environment
# User: {full_name} ({username})

print("=" * 50)
print("Welcome to the Local Test IDE!")
print("User: {username}")
print("=" * 50)

# Test the hybrid REPL system
message = "Hello from {username}!"
number = 42

print(f"Message: {{message}}")
print(f"Number: {{number}}")
print("\\nThese variables will be available in REPL after execution.")
''')

            print(f"✓ Created directory: {username}/")

        print("\n✅ All test directories created")

    except Exception as e:
        print(f"❌ Error creating test directories: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    init_local_test_accounts()
