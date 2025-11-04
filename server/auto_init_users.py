#!/usr/bin/env python3
"""
Auto-initialize users on container startup if they don't exist
This runs when the container starts and checks if users need to be created
"""
import os
import sys
import psycopg2
import bcrypt
from datetime import datetime


def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def init_users_if_needed():
    """Initialize users if the database is empty"""
    print("=== AUTO USER INITIALIZATION STARTED ===")
    try:
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            print("DATABASE_URL not set, skipping user initialization")
            return

        print(f"Checking if users need initialization...")
        print(f"DATABASE_URL found: {db_url[:30]}...")

        # Parse the database URL (port is optional, defaults to 5432)
        import re

        match = re.match(r"postgresql://([^:]+):([^@]+)@([^/:]+)(?::(\d+))?/(.+)", db_url)
        if not match:
            print("Invalid DATABASE_URL format")
            return

        user, password, host, port, database = match.groups()
        port = port or "5432"  # Default to 5432 if not specified

        # Connect to database
        conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
        cursor = conn.cursor()

        # Check if users table exists and has data
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """
        )
        table_exists = cursor.fetchone()[0]

        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            if user_count > 0:
                print(f"Users already exist ({user_count} users found), skipping initialization")
                cursor.close()
                conn.close()
                return

        print("Initializing users...")

        # Create tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255),
                password_hash TEXT NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_used BOOLEAN DEFAULT false
            )
        """
        )

        # Create index for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_reset_tokens(token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_expires ON password_reset_tokens(expires_at)")

        conn.commit()

        # Create admin users
        admin_users = [
            ("sl7927", "Susan Liao", "Admin@sl7927", "professor"),
            ("sa9082", "Sachin Adlakha", "Admin@sa9082", "professor"),
            ("et2434", "Ethan Tan", "Admin@et2434", "professor"),
        ]

        for username, full_name, password, role in admin_users:
            email = f"{username}@college.edu"
            password_hash = hash_password(password)
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """,
                (username, email, password_hash, full_name, role),
            )
            print(f"Created admin: {username}")

        # Create student users
        student_users = [
            ("sa8820", "Syed Ahnaf Ul Ahsan", "student@sa8820"),
            ("na3649", "Nicole Akmetov", "student@na3649"),
            ("ntb5594", "Nabi Burns-Min", "student@ntb5594"),
            ("hrb9324", "Harry Byala", "student@hrb9324"),
            ("nd2560", "Nikita Drovin-skiy", "student@nd2560"),
            ("ag11389", "Adrian Garcia", "student@ag11389"),
            ("arg9667", "Aarav Gupta", "student@arg9667"),
            ("lh4052", "Liisa Hambazaza", "student@lh4052"),
            ("jh9963", "Justin Hu", "student@jh9963"),
            ("ch5315", "Rami Hu", "student@ch5315"),
            ("wh2717", "Weijie Huang", "student@wh2717"),
            ("bsj5539", "Maybelina J", "student@bsj5539"),
            ("fk2248", "Falisha Khan", "student@fk2248"),
            ("nvk9963", "Neil Khandelwal", "student@nvk9963"),
            ("sil9056", "Simon Levine", "student@sil9056"),
            ("hl6459", "Haoru Li", "student@hl6459"),
            ("zl3894", "Jenny Li", "student@zl3894"),
            ("jom2045", "Janell Magante", "student@jom2045"),
            ("arm9283", "Amelia Mappus", "student@arm9283"),
            ("zm2525", "Zhou Meng", "student@zm2525"),
            ("im2420", "Ishaan Mukherjee", "student@im2420"),
            ("jn3143", "Janvi Nagpal", "student@jn3143"),
            ("jn9106", "Jacob Nathan", "student@jn9106"),
            ("djp10030", "Darius Partovi", "student@djp10030"),
            ("ap10062", "Alexandar Pelletier", "student@ap10062"),
            ("bap9618", "Benjamin Piquet", "student@bap9618"),
            ("fp2331", "Federico Pirelli", "student@fp2331"),
            ("srp8204", "Shaina Pollak", "student@srp8204"),
            ("agr8457", "Alex Reber", "student@agr8457"),
            ("shs9941", "Suzie Sanford", "student@shs9941"),
            ("as19217", "Albert Sun", "student@as19217"),
            ("mat9481", "Mario Toscano", "student@mat9481"),
            ("cw4715", "Chun-Hsiang Wang", "student@cw4715"),
            ("jw9248", "Jingyuan Wang", "student@jw9248"),
            ("sz4766", "Shengbo Zhang", "student@sz4766"),
            ("sz3991", "Shiwen Zhu", "student@sz3991"),
            ("eif2018", "Ethan Flores", "student@eif2018"),
            ("ql2499", "Nick Li", "student@ql2499"),
            ("gs4387", "Gursehaj Singh", "student@gs4387"),
            ("cw4973", "Caden Wang", "student@cw4973"),
            ("jy4383", "Jessica Yuan", "student@jy4383"),
            ("test_1", "Test Student 1", "student@test_1"),
            ("test_2", "Test Student 2", "student@test_2"),
            ("test_3", "Test Student 3", "student@test_3"),
            ("test_4", "Test Student 4", "student@test_4"),
            ("test_5", "Test Student 5", "student@test_5"),
            ("test_6", "Test Student 6", "student@test_6"),
            ("test_7", "Test Student 7", "student@test_7"),
            ("test_8", "Test Student 8", "student@test_8"),
            ("test_9", "Test Student 9", "student@test_9"),
            ("test_10", "Test Student 10", "student@test_10"),
        ]

        for username, full_name, password in student_users:
            email = f"{username}@college.edu"
            password_hash = hash_password(password)
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """,
                (username, email, password_hash, full_name, "student"),
            )
            print(f"Created student: {username}")

        conn.commit()

        # Create directories on EFS
        create_efs_directories()

        # Verify
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'professor'")
        admin_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()[0]

        print(f"\n✅ User initialization complete!")
        print(f"Created {admin_count} admin users")
        print(f"Created {student_count} student users")
        print(f"Total: {admin_count + student_count} users")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR during user initialization: {e}")
        import traceback

        traceback.print_exc()


def create_efs_directories():
    """Create directories on EFS for each student"""
    try:
        # Determine the base path
        if os.path.exists("/mnt/efs"):
            base_path = "/mnt/efs/pythonide-data/ide/Local"
        elif "IDE_DATA_PATH" in os.environ:
            base_path = os.path.join(os.environ["IDE_DATA_PATH"], "ide", "Local")
        else:
            base_path = "/tmp/pythonide-data/ide/Local"

        print(f"Creating directories at: {base_path}")

        # Create base directories
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(os.path.dirname(base_path) + "/Lecture Notes", exist_ok=True)
        os.makedirs(os.path.dirname(base_path) + "/Assignments", exist_ok=True)
        os.makedirs(os.path.dirname(base_path) + "/Tests", exist_ok=True)

        # Create directories ONLY for students (NOT admins/professors)
        student_usernames = [
            "sa8820",
            "na3649",
            "ntb5594",
            "hrb9324",
            "nd2560",
            "ag11389",
            "arg9667",
            "lh4052",
            "jh9963",
            "ch5315",
            "wh2717",
            "bsj5539",
            "fk2248",
            "nvk9963",
            "sil9056",
            "hl6459",
            "zl3894",
            "jom2045",
            "arm9283",
            "zm2525",
            "im2420",
            "jn3143",
            "jn9106",
            "djp10030",
            "ap10062",
            "bap9618",
            "fp2331",
            "srp8204",
            "agr8457",
            "shs9941",
            "as19217",
            "mat9481",
            "cw4715",
            "jw9248",
            "sz4766",
            "sz3991",
            "eif2018",
            "ql2499",
            "gs4387",
            "cw4973",
            "jy4383",
            "test_1",
            "test_2",
            "test_3",
            "test_4",
            "test_5",
            "test_6",
            "test_7",
            "test_8",
            "test_9",
            "test_10",
        ]

        # Only create directories for students
        for username in student_usernames:
            user_dir = os.path.join(base_path, username)
            os.makedirs(user_dir, exist_ok=True)
            workspace_dir = os.path.join(user_dir, "workspace")
            os.makedirs(workspace_dir, exist_ok=True)
            examples_dir = os.path.join(user_dir, "Lecture_Examples")
            os.makedirs(examples_dir, exist_ok=True)

            # Create welcome file for students
            welcome_file = os.path.join(user_dir, "welcome.py")
            if not os.path.exists(welcome_file):
                with open(welcome_file, "w") as f:
                    f.write(
                        f"""# Welcome {username}!
# This is your personal workspace directory.
# Only you and the teaching staff can access files here.

print("Hello {username}!")
print("This is your personal Python IDE workspace.")
print("Start coding and have fun learning Python!")

# Try running this file by clicking the Run button!
"""
                    )
            print(f"Created directory for: {username}")

        print("✅ All student directories created")

    except Exception as e:
        print(f"Error creating directories: {e}")


if __name__ == "__main__":
    init_users_if_needed()
