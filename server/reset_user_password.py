#!/usr/bin/env python3
"""
Command-line utility to reset user passwords
Usage:
    python server/reset_user_password.py <username> <new_password>
    python server/reset_user_password.py --help
    python server/reset_user_password.py --list-users
    python server/reset_user_password.py --generate-password <username>

Examples:
    # Reset password manually
    python server/reset_user_password.py sa9082 newpassword123

    # Generate random password and reset
    python server/reset_user_password.py --generate-password sa9082

    # List all users
    python server/reset_user_password.py --list-users
"""

import os
import sys
import argparse
import bcrypt
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import db_manager
from utils.password_generator import PasswordGenerator


def reset_password(username, new_password):
    """
    Reset a user's password directly in the database

    Args:
        username (str): Username to reset password for
        new_password (str): New password (plaintext, will be hashed)

    Returns:
        tuple: (success, message)
    """
    try:
        # Check if user exists
        query = "SELECT id, username, full_name, role FROM users WHERE username = %s" if db_manager.is_postgres else "SELECT id, username, full_name, role FROM users WHERE username = ?"

        users = db_manager.execute_query(query, (username,))

        if not users:
            return False, f"❌ User '{username}' not found"

        user = users[0]
        user_id = user["id"]
        full_name = user["full_name"]
        role = user["role"]

        # Hash the new password
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode("utf-8")

        # Update password in database
        update_query = "UPDATE users SET password_hash = %s WHERE id = %s" if db_manager.is_postgres else "UPDATE users SET password_hash = ? WHERE id = ?"

        db_manager.execute_query(update_query, (password_hash, user_id))

        # Invalidate all existing sessions for this user (force re-login)
        invalidate_query = "UPDATE sessions SET is_active = false WHERE user_id = %s" if db_manager.is_postgres else "UPDATE sessions SET is_active = 0 WHERE user_id = ?"

        db_manager.execute_query(invalidate_query, (user_id,))

        return True, f"""✅ Password reset successful!

User Details:
  Username:  {username}
  Full Name: {full_name}
  Role:      {role}
  New Password: {new_password}

⚠️  All active sessions have been logged out.
User will need to log in again with the new password.
"""

    except Exception as e:
        return False, f"❌ Failed to reset password: {e}"


def list_all_users():
    """List all users in the database"""
    try:
        query = "SELECT username, email, full_name, role, created_at, last_login FROM users ORDER BY role DESC, username ASC"

        users = db_manager.execute_query(query)

        if not users:
            print("❌ No users found in database")
            return

        print("\n" + "=" * 80)
        print(f"{'Username':<15} {'Full Name':<25} {'Role':<12} {'Email':<30}")
        print("=" * 80)

        for user in users:
            username = user["username"]
            full_name = user["full_name"] or "N/A"
            role = user["role"]
            email = user["email"] or "N/A"

            print(f"{username:<15} {full_name:<25} {role:<12} {email:<30}")

        print("=" * 80)
        print(f"\nTotal users: {len(users)}\n")

    except Exception as e:
        print(f"❌ Failed to list users: {e}")


def generate_and_reset_password(username, length=12):
    """Generate a random password and reset user's password"""
    try:
        generator = PasswordGenerator()
        new_password = generator.generate_password(length=length)

        success, message = reset_password(username, new_password)

        if success:
            print(message)
            print(f"🔑 Generated Password: {new_password}")
            print(f"   (Complexity: {length} chars, mixed case, numbers, symbols)")
        else:
            print(message)

    except Exception as e:
        print(f"❌ Failed to generate password: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Reset user passwords in PythonIDE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s sa9082 newpassword123              # Reset password manually
  %(prog)s --generate-password sa9082         # Generate random password
  %(prog)s --list-users                       # List all users
  %(prog)s --generate-password sa9082 --length 16  # Custom length password
        """
    )

    parser.add_argument("username", nargs="?", help="Username to reset password for")
    parser.add_argument("new_password", nargs="?", help="New password (plaintext)")
    parser.add_argument("--list-users", action="store_true", help="List all users in database")
    parser.add_argument("--generate-password", metavar="USERNAME", help="Generate random password for user")
    parser.add_argument("--length", type=int, default=12, help="Password length for generated passwords (default: 12)")

    args = parser.parse_args()

    # Validate database connection
    try:
        db_manager.execute_query("SELECT 1")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. DATABASE_URL environment variable is set correctly")
        print("  3. You're in the correct directory")
        sys.exit(1)

    # Handle commands
    if args.list_users:
        list_all_users()

    elif args.generate_password:
        generate_and_reset_password(args.generate_password, args.length)

    elif args.username and args.new_password:
        success, message = reset_password(args.username, args.new_password)
        print(message)

    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
