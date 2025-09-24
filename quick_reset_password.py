#!/usr/bin/env python
"""
Quick password reset for local development.
Resets passwords for common accounts.
"""

import psycopg2
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def reset_passwords():
    """Reset passwords for common accounts."""

    # Get database connection from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/pythonide')

    # Define accounts to reset with their new passwords
    accounts_to_reset = [
        ('sa9082', 'password'),  # Admin account
        ('sl7927', 'password'),  # Another admin
        ('test_1', 'password'),  # Test student
        ('test_2', 'password'),  # Test student
    ]

    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        for username, new_password in accounts_to_reset:
            # Hash the new password
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Update the password
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE username = %s",
                (password_hash, username)
            )

            if cur.rowcount > 0:
                print(f"✅ Reset password for {username} -> '{new_password}'")
            else:
                print(f"⚠️  User {username} not found")

        conn.commit()
        print("\n🎉 Password reset complete!")
        print("\n📝 You can now login with:")
        for username, password in accounts_to_reset:
            role = "Admin" if username in ['sa9082', 'sl7927'] else "Student"
            print(f"   {role}: {username} / {password}")

    except Exception as e:
        print(f"❌ Error resetting passwords: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    print("🔐 Quick Password Reset for Local Development")
    print("=" * 50)
    print("This will reset passwords for common test accounts.")
    print("=" * 50)

    response = input("\nDo you want to proceed? (yes/no): ").strip().lower()

    if response == 'yes' or response == 'y':
        reset_passwords()
    else:
        print("Cancelled.")