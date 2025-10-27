#!/usr/bin/env python3
"""
Initialize test users for Docker exam environment
Creates test accounts for REPL testing
"""
import os
import sys
import psycopg2
import bcrypt
from datetime import datetime


def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def init_docker_test_users():
    """Initialize test users for Docker testing"""
    print("=== DOCKER TEST USER INITIALIZATION ===")

    try:
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            print("DATABASE_URL not set!")
            return

        print(f"Connecting to database...")

        # Parse the database URL
        import re
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^/:]+)(?::(\d+))?/(.+)", db_url)
        if not match:
            print("Invalid DATABASE_URL format")
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

        # Define test users
        test_users = [
            # Test students
            ("test_student", "password123", "Test Student", "student", "test_student@college.edu"),
            ("demo_student", "demo123", "Demo Student", "student", "demo_student@college.edu"),
            ("alice_test", "alice123", "Alice Testing", "student", "alice_test@college.edu"),

            # Test professors/admins
            ("admin_editor", "admin123", "Admin Editor", "professor", "admin_editor@college.edu"),
            ("test_professor", "prof123", "Test Professor", "professor", "test_professor@college.edu"),
            ("admin_viewer", "viewer123", "Admin Viewer", "professor", "admin_viewer@college.edu"),
        ]

        # Clear existing test users
        print("Clearing existing test users...")
        for username, _, _, _, _ in test_users:
            cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()

        # Create test users
        created_count = 0
        for username, plain_password, full_name, role, email in test_users:
            password_hash = hash_password(plain_password)

            try:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, email, password_hash, full_name, role))

                print(f"✓ Created {role}: {username} / {plain_password}")
                created_count += 1

            except Exception as e:
                print(f"Error creating {username}: {e}")

        conn.commit()

        # Verify creation
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'test_%' OR username LIKE 'admin_%' OR username LIKE 'demo_%' OR username LIKE 'alice_%'")
        test_count = cursor.fetchone()[0]

        print(f"\n✅ Docker test user initialization complete!")
        print(f"Created {created_count} test accounts")
        print(f"Total test accounts in database: {test_count}")
        print("\n📋 Test Credentials:")
        print("─" * 40)
        for username, password, _, role, _ in test_users:
            print(f"{role.upper():12} | {username:15} | {password}")
        print("─" * 40)

        cursor.close()
        conn.close()

        # Create directories for test users
        create_test_directories(test_users)

    except Exception as e:
        print(f"ERROR during test user initialization: {e}")
        import traceback
        traceback.print_exc()


def create_test_directories(test_users):
    """Create directories for test users"""
    try:
        # Determine the base path
        if "IDE_DATA_PATH" in os.environ:
            base_path = os.path.join(os.environ["IDE_DATA_PATH"], "ide", "Local")
        elif os.path.exists("/mnt/efs/pythonide-data-exam"):
            base_path = "/mnt/efs/pythonide-data-exam/ide/Local"
        else:
            base_path = "/tmp/pythonide-data-exam/ide/Local"

        print(f"\nCreating test directories at: {base_path}")

        # Create base directory
        os.makedirs(base_path, exist_ok=True)

        # Create directories for each test user
        for username, _, _, _, _ in test_users:
            user_dir = os.path.join(base_path, username)
            os.makedirs(user_dir, exist_ok=True)

            # Create welcome file
            welcome_file = os.path.join(user_dir, "welcome.py")
            with open(welcome_file, "w") as f:
                f.write(f'''# Welcome {username}!
# This is your test environment for the new REPL system.

print("Welcome to the Docker Test IDE!")
print("User: {username}")
print("You can test the new REPL implementation here.")

# Test variables for REPL persistence
test_var = "Hello from script!"
test_number = 42

print(f"Variables defined: test_var='{{test_var}}', test_number={{test_number}}")
print("These should be available in the REPL after the script runs.")
''')

            print(f"✓ Created directory and welcome.py for: {username}")

        # Also copy the test scripts to a shared location
        test_scripts_src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_scripts")
        if os.path.exists(test_scripts_src):
            import shutil
            # Copy test scripts to each user's directory
            for username, _, _, _, _ in test_users:
                user_dir = os.path.join(base_path, username)
                for test_file in ["test_basic.py", "test_input.py", "test_error.py", "test_loop_input.py"]:
                    src_file = os.path.join(test_scripts_src, test_file)
                    if os.path.exists(src_file):
                        shutil.copy2(src_file, os.path.join(user_dir, test_file))
            print("✓ Copied test scripts to user directories")

        print("✅ All test directories created")

    except Exception as e:
        print(f"Error creating test directories: {e}")


if __name__ == "__main__":
    init_docker_test_users()