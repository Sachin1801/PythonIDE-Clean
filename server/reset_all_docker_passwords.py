#!/usr/bin/env python3
"""
Reset all passwords in Docker database and export to CSV
This will generate new secure passwords for all users
"""
import sys
import os
import csv
import bcrypt
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import db_manager
from utils.password_generator import PasswordGenerator


def reset_all_passwords_and_export():
    """Reset all user passwords and export to CSV"""

    print("\n" + "=" * 80)
    print("Resetting All Docker Database Passwords")
    print("=" * 80 + "\n")

    # Get all users
    query = "SELECT id, username, email, full_name, role FROM users ORDER BY role DESC, username ASC"
    users = db_manager.execute_query(query)

    if not users:
        print("❌ No users found in database")
        return

    print(f"Found {len(users)} users to reset\n")

    generator = PasswordGenerator()
    updated_users = []

    for i, user in enumerate(users, 1):
        user_id = user['id']
        username = user['username']
        full_name = user['full_name']
        email = user['email']
        role = user['role']

        # Generate new password
        new_password = generator.generate_password(length=12)

        # Hash the password
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode('utf-8')

        # Update database
        update_query = "UPDATE users SET password_hash = %s WHERE id = %s" if db_manager.is_postgres else "UPDATE users SET password_hash = ? WHERE id = ?"
        db_manager.execute_query(update_query, (password_hash, user_id))

        # Invalidate all sessions (force re-login)
        invalidate_query = "UPDATE sessions SET is_active = false WHERE user_id = %s" if db_manager.is_postgres else "UPDATE sessions SET is_active = 0 WHERE user_id = ?"
        db_manager.execute_query(invalidate_query, (user_id,))

        updated_users.append({
            'username': username,
            'full_name': full_name,
            'password': new_password,
            'role': role,
            'email': email,
            'password_generated_at': datetime.now().isoformat()
        })

        print(f"[{i}/{len(users)}] ✅ {username:<20} {role:<10} - Password reset")

    # Export to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"docker_local_credentials_{timestamp}.csv"

    # Create adminData directory if it doesn't exist
    admin_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "adminData")
    os.makedirs(admin_data_dir, exist_ok=True)

    csv_path = os.path.join(admin_data_dir, csv_filename)

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Username', 'Full Name', 'Password', 'Role', 'Email', 'Generated At']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for user in updated_users:
            writer.writerow({
                'Username': user['username'],
                'Full Name': user['full_name'],
                'Password': user['password'],
                'Role': user['role'],
                'Email': user['email'],
                'Generated At': user['password_generated_at']
            })

    print("\n" + "=" * 80)
    print("✅ Password Reset Complete!")
    print("=" * 80)
    print(f"\nTotal users reset: {len(updated_users)}")
    print(f"CSV exported to: {csv_path}")
    print(f"\n📄 File: {csv_filename}")

    # Show first 5 users as example
    print("\n🔑 Sample Credentials (first 5 users):")
    print("-" * 60)
    for user in updated_users[:5]:
        print(f"{user['username']:<15} : {user['password']:<20} ({user['role']})")
    print("-" * 60)
    print(f"... and {len(updated_users) - 5} more users")

    print("\n⚠️  All sessions have been invalidated (users logged out)")
    print("✅ Users can now login with new passwords from the CSV file")

    return csv_path


if __name__ == "__main__":
    try:
        # Validate database connection
        db_manager.execute_query("SELECT 1")
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    try:
        csv_path = reset_all_passwords_and_export()
        print(f"\n✅ Done! Open the CSV file to get login credentials:")
        print(f"   {csv_path}\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
