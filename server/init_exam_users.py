#!/usr/bin/env python3
"""
Initialize exam users with random passwords
Creates exam_{netid} accounts for mid-term examination
"""
import os
import sys
import psycopg2
import bcrypt
import random
import string
from datetime import datetime
import csv


def generate_random_password(length=5):
    """Generate a random 5-character password (lowercase alphanumeric)"""
    # Use lowercase letters and digits (avoid ambiguous characters like 0,o,1,l)
    chars = 'abcdefghjklmnpqrstuvwxyz23456789'
    return ''.join(random.choice(chars) for _ in range(length))


def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def init_exam_users(reset_existing=False):
    """Initialize exam users from CSV file"""
    print("=== EXAM USER INITIALIZATION STARTED ===")

    try:
        # Get database URL from environment (same var as main server)
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            print("DATABASE_URL not set!")
            print("Please set: export DATABASE_URL='postgresql://user:pass@host:port/pythonide_exam'")
            return

        print(f"Connecting to exam database...")

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

        # Reset existing users if requested
        if reset_existing:
            print("Clearing existing users...")
            cursor.execute("DELETE FROM users")
            conn.commit()

        # Read credentials from CSV file
        admin_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "adminData")
        csv_path = os.path.join(admin_data_dir, "exam_credentials_LATEST.csv")

        if not os.path.exists(csv_path):
            print(f"ERROR: Credentials file not found at {csv_path}")
            return

        print(f"Reading credentials from: {csv_path}")

        # Create exam users from CSV
        created_students = 0
        created_admins = 0

        with open(csv_path, 'r', newline='') as csvfile:
            csvreader = csv.DictReader(csvfile)

            for row in csvreader:
                username = row['Username'].strip()
                password = row['Password'].strip()
                full_name = row['Full Name'].strip()
                netid = row['NetID'].strip()

                # Skip empty rows
                if not username or not password:
                    continue

                email = f"{username}@college.edu"
                password_hash = hash_password(password)

                # Determine role: professors/admins vs students
                # Admin accounts: sa9082, et2434, sl7927, admin_editor, dpp9951
                admin_netids = ['sa9082', 'et2434', 'sl7927', 'admin_editor', 'dpp9951']
                role = "professor" if netid in admin_netids else "student"

                try:
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, full_name, role)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (username) DO UPDATE SET
                            email = EXCLUDED.email,
                            password_hash = EXCLUDED.password_hash,
                            full_name = EXCLUDED.full_name,
                            role = EXCLUDED.role
                    """, (username, email, password_hash, full_name, role))

                    print(f"Created {role}: {username} ({full_name}) - Password: {password}")

                    if role == "professor":
                        created_admins += 1
                    else:
                        created_students += 1

                except Exception as e:
                    print(f"Error creating {username}: {e}")

        conn.commit()

        # Verify - count all students and professors
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'")
        student_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='professor'")
        prof_count = cursor.fetchone()[0]

        print(f"\n✅ Exam user initialization complete!")
        print(f"Total student accounts: {student_count} ({created_students} processed)")
        print(f"Total professor/admin accounts: {prof_count} ({created_admins} processed)")
        print(f"Credentials source: {csv_path}")
        print("\n⚠️  IMPORTANT: All passwords are from exam_credentials_LATEST.csv")

        cursor.close()
        conn.close()

        # Create directories on EFS
        create_exam_directories()

    except Exception as e:
        print(f"ERROR during exam user initialization: {e}")
        import traceback
        traceback.print_exc()


def create_exam_directories():
    """Create directories on EFS for exam users"""
    try:
        # Determine the base path for EXAM environment
        # Prioritize IDE_DATA_PATH (set in Docker), then check for EFS, then fallback to /tmp
        if "IDE_DATA_PATH" in os.environ:
            base_path = os.path.join(os.environ["IDE_DATA_PATH"], "ide", "Local")
            example_path = os.path.join(os.environ["IDE_DATA_PATH"], "ide", "Example")
        elif os.path.exists("/mnt/efs/pythonide-data-exam"):
            base_path = "/mnt/efs/pythonide-data-exam/ide/Local"
            example_path = "/mnt/efs/pythonide-data-exam/ide/Example"
        else:
            base_path = "/tmp/pythonide-data-exam/ide/Local"
            example_path = "/tmp/pythonide-data-exam/ide/Example"

        print(f"\nCreating exam directories at: {base_path}")

        # Create base directories
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(example_path, exist_ok=True)

        # Create Example folder with read-only sample files
        example_file = os.path.join(example_path, "example_functions.py")
        with open(example_file, "w") as f:
            f.write("""# Example Functions for Mid-Term Exam
# This is a read-only reference file

def calculate_average(numbers):
    '''Calculate the average of a list of numbers'''
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def is_palindrome(text):
    '''Check if a string is a palindrome'''
    clean_text = ''.join(c.lower() for c in text if c.isalnum())
    return clean_text == clean_text[::-1]

def fibonacci(n):
    '''Generate first n Fibonacci numbers'''
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    else:
        fib = [0, 1]
        for i in range(2, n):
            fib.append(fib[-1] + fib[-2])
        return fib

# You can reference these examples but cannot modify this file
""")

        # Read usernames from CSV file
        admin_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "adminData")
        csv_path = os.path.join(admin_data_dir, "exam_credentials_LATEST.csv")

        exam_usernames = []
        if os.path.exists(csv_path):
            with open(csv_path, 'r', newline='') as csvfile:
                csvreader = csv.DictReader(csvfile)
                for row in csvreader:
                    username = row['Username'].strip()
                    if username:
                        exam_usernames.append(username)
            print(f"Found {len(exam_usernames)} exam accounts from CSV")
        else:
            print(f"WARNING: CSV file not found at {csv_path}, skipping directory creation")
            return

        # Create directories for each exam user
        for username in exam_usernames:
            user_dir = os.path.join(base_path, username)
            os.makedirs(user_dir, exist_ok=True)

            # Create welcome file for exam environment
            welcome_file = os.path.join(user_dir, "welcome.py")
            with open(welcome_file, "w") as f:
                f.write("""# Welcome to the Exam IDE Environment
# This is your isolated workspace for examinations.
# Only you and the instructors can access files in this directory.

print("Welcome to the Exam IDE!")
print("This environment is isolated and secure.")
print("You can write and test your Python code here.")
print("Good luck on your exam!")
""")

            print(f"Created exam directory for: {username}")

        print("✅ All exam directories created")

    except Exception as e:
        print(f"Error creating exam directories: {e}")


def reset_exam_files():
    """Reset exam files before the actual exam (run this right before exam)"""
    print("=== RESETTING EXAM FILES FOR ACTUAL EXAM ===")

    try:
        if os.path.exists("/mnt/efs"):
            base_path = "/mnt/efs/pythonide-data-exam/ide/Local"
        elif "EXAM_IDE_DATA_PATH" in os.environ:
            base_path = os.path.join(os.environ["EXAM_IDE_DATA_PATH"], "ide", "Local")
        else:
            base_path = "/tmp/pythonide-data-exam/ide/Local"

        # Get actual exam questions from a file (you'll create this)
        exam_content = """# Mid-Term Exam - ACTUAL QUESTIONS
# Name: {username}
# Date: {date}
# Time Limit: 75 minutes

# INSTRUCTIONS:
# - Complete all functions below
# - You may NOT use external resources
# - Test your code before submission
# - Save your work frequently (Ctrl+S)

# Question 1 (20 points): String Manipulation
def reverse_words(sentence):
    '''
    Given a sentence, reverse each word individually.
    Example: "Hello World" -> "olleH dlroW"
    '''
    pass

# Question 2 (25 points): List Processing
def find_duplicates(lst):
    '''
    Find all duplicate elements in a list.
    Return a list of duplicates (no repetition).
    Example: [1,2,3,2,4,3] -> [2,3]
    '''
    pass

# Question 3 (25 points): Dictionary Operations
def merge_inventories(inv1, inv2):
    '''
    Merge two inventory dictionaries by adding quantities.
    Example: {'apple': 5}, {'apple': 3, 'banana': 2} -> {'apple': 8, 'banana': 2}
    '''
    pass

# Question 4 (30 points): File Handling
def process_scores(filename):
    '''
    Read a file with student scores (name,score per line).
    Return the average score and the highest scorer's name.
    '''
    pass

# TEST YOUR FUNCTIONS HERE:
# print(reverse_words("Hello World"))
# print(find_duplicates([1,2,3,2,4,3]))
# print(merge_inventories({'apple': 5}, {'apple': 3, 'banana': 2}))
"""

        # Reset each student's exam file
        import glob
        from datetime import datetime

        for user_dir in glob.glob(os.path.join(base_path, "exam_*")):
            username = os.path.basename(user_dir)
            exam_file = os.path.join(user_dir, "midterm_exam.py")

            # Clear any other files (keep directory clean)
            for file in glob.glob(os.path.join(user_dir, "*")):
                if file != exam_file:
                    os.remove(file)

            # Write the actual exam content
            with open(exam_file, "w") as f:
                f.write(exam_content.format(
                    username=username,
                    date=datetime.now().strftime("%Y-%m-%d")
                ))

            print(f"Reset exam file for: {username}")

        print("✅ All exam files reset for actual exam")

    except Exception as e:
        print(f"Error resetting exam files: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Manage exam users')
    parser.add_argument('--reset', action='store_true', help='Reset existing exam users')
    parser.add_argument('--reset-files', action='store_true', help='Reset exam files for actual exam')

    args = parser.parse_args()

    if args.reset_files:
        reset_exam_files()
    else:
        init_exam_users(reset_existing=args.reset)