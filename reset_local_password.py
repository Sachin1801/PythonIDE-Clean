#!/usr/bin/env python
"""
Reset password for specific users in the local PostgreSQL database.
This is for LOCAL DEVELOPMENT ONLY - do not use in production!
"""

import psycopg2
import bcrypt
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def reset_password(username, new_password):
    """Reset password for a specific user."""

    # Get database connection from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/pythonide')

    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Hash the new password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Update the password
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE username = %s",
            (password_hash, username)
        )

        if cur.rowcount == 0:
            print(f"❌ User '{username}' not found")
            return False

        conn.commit()
        print(f"✅ Password reset successfully for user: {username}")
        return True

    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def list_users():
    """List all users in the database."""

    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/pythonide')

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute("SELECT username, role FROM users ORDER BY role, username")
        users = cur.fetchall()

        print("\n📋 Current users in database:")
        print("-" * 40)

        current_role = None
        for username, role in users:
            if role != current_role:
                current_role = role
                print(f"\n{role.upper()}S:")
            print(f"  - {username}")

        print("-" * 40)

    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def main():
    print("🔐 Local Password Reset Tool")
    print("=" * 40)
    print("⚠️  This is for LOCAL DEVELOPMENT ONLY!")
    print("=" * 40)

    # List current users
    list_users()

    while True:
        print("\nOptions:")
        print("1. Reset password for a user")
        print("2. Reset password for admin (sa9082)")
        print("3. Reset password for test student")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == '1':
            username = input("Enter username to reset: ").strip()
            password = input("Enter new password: ").strip()

            if not password:
                print("❌ Password cannot be empty")
                continue

            reset_password(username, password)

        elif choice == '2':
            # Quick reset for your admin account
            password = input("Enter new password for sa9082 (or press Enter for 'password'): ").strip()
            if not password:
                password = 'password'
            reset_password('sa9082', password)
            print(f"📝 You can now login with: sa9082 / {password}")

        elif choice == '3':
            # Reset a test student account
            password = input("Enter new password for test_1 (or press Enter for 'password'): ").strip()
            if not password:
                password = 'password'
            reset_password('test_1', password)
            print(f"📝 You can now login with: test_1 / {password}")

        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()