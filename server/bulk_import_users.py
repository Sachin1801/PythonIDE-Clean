#!/usr/bin/env python3
"""
Bulk import users from CSV file
Usage:
    python server/bulk_import_users.py <csv_file>
    python server/bulk_import_users.py adminData/consistent_class_credentials_local_20250909_164112.csv
"""

import os
import sys
import csv
import bcrypt
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import db_manager
from common.file_storage import file_storage


def bulk_create_users(csv_path):
    """
    Create all users from CSV file

    Args:
        csv_path (str): Path to CSV file with user data

    Returns:
        dict: Statistics about the import
    """
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return None

    print("\n" + "=" * 80)
    print(f"Bulk User Import from: {csv_path}")
    print("=" * 80 + "\n")

    users_to_create = []

    # Read CSV file
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users_to_create.append({
                'username': row['Username'].strip(),
                'full_name': row['Full Name'].strip(),
                'password': row['Password'].strip(),
                'role': row['Role'].strip(),
                'email': row['Email'].strip()
            })

    print(f"Found {len(users_to_create)} users to import\n")

    # Statistics
    stats = {
        'total': len(users_to_create),
        'created': 0,
        'skipped': 0,
        'errors': 0,
        'students': 0,
        'professors': 0
    }

    # Create each user
    for i, user_data in enumerate(users_to_create, 1):
        username = user_data['username']
        full_name = user_data['full_name']
        password = user_data['password']
        role = user_data['role']
        email = user_data['email']

        try:
            # Check if user already exists
            check_query = "SELECT id FROM users WHERE username = %s" if db_manager.is_postgres else "SELECT id FROM users WHERE username = ?"
            existing = db_manager.execute_query(check_query, (username,))

            if existing:
                print(f"[{i}/{stats['total']}] ⚠️  {username:<20} (Already exists)")
                stats['skipped'] += 1
                continue

            # Hash password
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")

            # Insert user
            insert_query = """
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
            """ if db_manager.is_postgres else """
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """

            db_manager.execute_query(insert_query, (username, email, password_hash, full_name, role))

            # Create user directory
            try:
                file_storage.create_user_directories(username, full_name)
            except Exception as dir_error:
                print(f"    ⚠️  Directory creation warning: {dir_error}")

            # Update stats
            stats['created'] += 1
            if role == 'student':
                stats['students'] += 1
            else:
                stats['professors'] += 1

            print(f"[{i}/{stats['total']}] ✅ {username:<20} ({role:<10}) - {full_name}")

        except Exception as e:
            print(f"[{i}/{stats['total']}] ❌ {username:<20} - Error: {e}")
            stats['errors'] += 1

    # Print summary
    print("\n" + "=" * 80)
    print("Import Summary")
    print("=" * 80)
    print(f"Total users in CSV:     {stats['total']}")
    print(f"✅ Successfully created: {stats['created']}")
    print(f"   - Students:          {stats['students']}")
    print(f"   - Professors:        {stats['professors']}")
    print(f"⚠️  Skipped (existing):  {stats['skipped']}")
    print(f"❌ Errors:              {stats['errors']}")
    print("=" * 80 + "\n")

    return stats


def verify_import(csv_path):
    """
    Verify all users from CSV exist in database

    Args:
        csv_path (str): Path to CSV file
    """
    print("\n" + "=" * 80)
    print("Verifying Import")
    print("=" * 80 + "\n")

    # Read usernames from CSV
    csv_usernames = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_usernames.add(row['Username'].strip())

    # Query all users from database
    query = "SELECT username, role FROM users ORDER BY role DESC, username ASC"
    db_users = db_manager.execute_query(query)
    db_usernames = {user['username'] for user in db_users}

    # Compare
    missing = csv_usernames - db_usernames
    extra = db_usernames - csv_usernames

    print(f"✅ Users in CSV:      {len(csv_usernames)}")
    print(f"✅ Users in Database: {len(db_usernames)}")
    print(f"✅ Matched:           {len(csv_usernames & db_usernames)}")

    if missing:
        print(f"\n⚠️  Missing from database ({len(missing)}):")
        for username in sorted(missing):
            print(f"    - {username}")

    if extra:
        print(f"\n⚠️  Extra in database (not in CSV) ({len(extra)}):")
        for username in sorted(extra):
            print(f"    - {username}")

    if not missing and len(csv_usernames) == len(db_usernames):
        print("\n✅ All users from CSV exist in database!")

    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Bulk import users from CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s adminData/consistent_class_credentials_local_20250909_164112.csv
  %(prog)s --verify adminData/consistent_class_credentials_local_20250909_164112.csv
        """
    )

    parser.add_argument('csv_file', help='Path to CSV file with user data')
    parser.add_argument('--verify', action='store_true', help='Verify import after creation')
    parser.add_argument('--verify-only', action='store_true', help='Only verify, do not import')

    args = parser.parse_args()

    # Validate database connection
    try:
        db_manager.execute_query("SELECT 1")
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    # Import users
    if not args.verify_only:
        stats = bulk_create_users(args.csv_file)
        if stats is None:
            sys.exit(1)

    # Verify import
    if args.verify or args.verify_only:
        verify_import(args.csv_file)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
