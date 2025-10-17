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
    """Generate a random 5-character password"""
    # Use letters and digits (avoid ambiguous characters like 0,O,1,l)
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(length))


def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def init_exam_users(reset_existing=False):
    """Initialize exam users for mid-term"""
    print("=== EXAM USER INITIALIZATION STARTED ===")

    try:
        # Get exam database URL from environment
        db_url = os.environ.get("EXAM_DATABASE_URL", "")
        if not db_url:
            print("EXAM_DATABASE_URL not set!")
            print("Please set: export EXAM_DATABASE_URL='postgresql://user:pass@host:port/pythonide_exam'")
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
            print("Clearing existing exam users...")
            cursor.execute("DELETE FROM users WHERE username LIKE 'exam_%'")
            conn.commit()

        # List of student NetIDs (from your main student list)
        student_netids = [
            "sa8820", "na3649", "ntb5594", "hrb9324", "nd2560",
            "ag11389", "arg9667", "lh4052", "jh9963", "ch5315",
            "wh2717", "bsj5539", "fk2248", "nvk9963", "sil9056",
            "hl6459", "zl3894", "jom2045", "arm9283", "zm2525",
            "im2420", "jn3143", "jn9106", "djp10030", "ap10062",
            "bap9618", "fp2331", "srp8204", "agr8457", "shs9941",
            "as19217", "mat9481", "cw4715", "jw9248", "sz4766",
            "sz3991", "eif2018", "ql2499", "gs4387", "cw4973", "jy4383"
        ]

        # Also get full names from main database if available
        student_names = {
            "sa8820": "Syed Ahnaf Ul Ahsan",
            "na3649": "Nicole Akmetov",
            "ntb5594": "Nabi Burns-Min",
            "hrb9324": "Harry Byala",
            "nd2560": "Nikita Drovin-skiy",
            "ag11389": "Adrian Garcia",
            "arg9667": "Aarav Gupta",
            "lh4052": "Liisa Hambazaza",
            "jh9963": "Justin Hu",
            "ch5315": "Rami Hu",
            "wh2717": "Weijie Huang",
            "bsj5539": "Maybelina J",
            "fk2248": "Falisha Khan",
            "nvk9963": "Neil Khandelwal",
            "sil9056": "Simon Levine",
            "hl6459": "Haoru Li",
            "zl3894": "Jenny Li",
            "jom2045": "Janell Magante",
            "arm9283": "Amelia Mappus",
            "zm2525": "Zhou Meng",
            "im2420": "Ishaan Mukherjee",
            "jn3143": "Janvi Nagpal",
            "jn9106": "Jacob Nathan",
            "djp10030": "Darius Partovi",
            "ap10062": "Alexandar Pelletier",
            "bap9618": "Benjamin Piquet",
            "fp2331": "Federico Pirelli",
            "srp8204": "Shaina Pollak",
            "agr8457": "Alex Reber",
            "shs9941": "Suzie Sanford",
            "as19217": "Albert Sun",
            "mat9481": "Mario Toscano",
            "cw4715": "Chun-Hsiang Wang",
            "jw9248": "Jingyuan Wang",
            "sz4766": "Shengbo Zhang",
            "sz3991": "Shiwen Zhu",
            "eif2018": "Ethan Flores",
            "ql2499": "Nick Li",
            "gs4387": "Gursehaj Singh",
            "cw4973": "Caden Wang",
            "jy4383": "Jessica Yuan"
        }

        # Create CSV file with credentials
        csv_filename = f"exam_credentials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(csv_filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Username', 'Password', 'Full Name', 'NetID'])

            # Create exam users
            created_count = 0
            for netid in student_netids:
                exam_username = f"exam_{netid}"
                exam_password = generate_random_password()
                full_name = student_names.get(netid, f"Student {netid}")
                email = f"{exam_username}@college.edu"
                password_hash = hash_password(exam_password)

                try:
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, full_name, role)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (username) DO NOTHING
                    """, (exam_username, email, password_hash, full_name, "student"))

                    # Write to CSV
                    csvwriter.writerow([exam_username, exam_password, full_name, netid])

                    print(f"Created: {exam_username} - Password: {exam_password}")
                    created_count += 1

                except Exception as e:
                    print(f"Error creating {exam_username}: {e}")

        # Create exam professor accounts (for monitoring)
        print("\nCreating exam professor accounts...")
        exam_professors = [
            ("exam_sl7927", "Susan Liao", "ExamAdmin@sl7927"),
            ("exam_sa9082", "Sachin Adlakha", "ExamAdmin@sa9082"),
            ("exam_et2434", "Ethan Tan", "ExamAdmin@et2434"),
        ]

        for username, full_name, password in exam_professors:
            email = f"{username}@college.edu"
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, (username, email, password_hash, full_name, "professor"))
            print(f"Created professor: {username}")

        conn.commit()

        # Verify
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'exam_%' AND role='student'")
        student_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'exam_%' AND role='professor'")
        prof_count = cursor.fetchone()[0]

        print(f"\n✅ Exam user initialization complete!")
        print(f"Created {student_count} exam student accounts")
        print(f"Created {prof_count} exam professor accounts")
        print(f"Credentials saved to: {csv_filename}")
        print("\n⚠️  IMPORTANT: Keep this CSV file secure! Share passwords individually with students.")

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
        if os.path.exists("/mnt/efs"):
            base_path = "/mnt/efs/pythonide-data-exam/ide/Local"
            example_path = "/mnt/efs/pythonide-data-exam/ide/Example"
        elif "EXAM_IDE_DATA_PATH" in os.environ:
            base_path = os.path.join(os.environ["EXAM_IDE_DATA_PATH"], "ide", "Local")
            example_path = os.path.join(os.environ["EXAM_IDE_DATA_PATH"], "ide", "Example")
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

        # List of exam student usernames
        exam_usernames = [f"exam_{netid}" for netid in [
            "sa8820", "na3649", "ntb5594", "hrb9324", "nd2560",
            "ag11389", "arg9667", "lh4052", "jh9963", "ch5315",
            "wh2717", "bsj5539", "fk2248", "nvk9963", "sil9056",
            "hl6459", "zl3894", "jom2045", "arm9283", "zm2525",
            "im2420", "jn3143", "jn9106", "djp10030", "ap10062",
            "bap9618", "fp2331", "srp8204", "agr8457", "shs9941",
            "as19217", "mat9481", "cw4715", "jw9248", "sz4766",
            "sz3991", "eif2018", "ql2499", "gs4387", "cw4973", "jy4383"
        ]]

        # Create directories for each exam student
        for username in exam_usernames:
            user_dir = os.path.join(base_path, username)
            os.makedirs(user_dir, exist_ok=True)

            # Create initial exam file (will be replaced before actual exam)
            exam_file = os.path.join(user_dir, "midterm_exam.py")
            with open(exam_file, "w") as f:
                f.write(f"""# Mid-Term Exam - {username}
# This is a practice file. The actual exam questions will appear here.

print("Welcome to the exam environment, {username}!")
print("This is where your exam questions will appear.")
print("You can practice using this environment before the exam.")

# Practice: Write a function that returns the square of a number
def square(n):
    pass  # Your code here

# Test your function
# print(square(5))  # Should print 25
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