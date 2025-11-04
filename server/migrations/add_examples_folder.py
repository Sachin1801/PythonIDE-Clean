#!/usr/bin/env python3
"""
Migration script to add 'Examples' folder to all existing student directories
This should be run once to update existing student folders
"""
import os
import sys

def add_examples_folders():
    """Add Examples folder to all existing student directories"""
    print("=== ADDING EXAMPLES FOLDERS TO STUDENT DIRECTORIES ===")

    try:
        # Determine the base path
        if os.path.exists("/mnt/efs"):
            base_path = "/mnt/efs/pythonide-data/ide/Local"
        elif "IDE_DATA_PATH" in os.environ:
            base_path = os.path.join(os.environ["IDE_DATA_PATH"], "ide", "Local")
        else:
            base_path = "/tmp/pythonide-data/ide/Local"

        print(f"Base path: {base_path}")

        if not os.path.exists(base_path):
            print(f"ERROR: Base path does not exist: {base_path}")
            return

        # List of all student usernames
        student_usernames = [
            "sa8820", "na3649", "ntb5594", "hrb9324", "nd2560", "ag11389", "arg9667",
            "lh4052", "jh9963", "ch5315", "wh2717", "bsj5539", "fk2248", "nvk9963",
            "sil9056", "hl6459", "zl3894", "jom2045", "arm9283", "zm2525", "im2420",
            "jn3143", "jn9106", "djp10030", "ap10062", "bap9618", "fp2331", "srp8204",
            "agr8457", "shs9941", "as19217", "mat9481", "cw4715", "jw9248", "sz4766",
            "sz3991", "eif2018", "ql2499", "gs4387", "cw4973", "jy4383",
            "test_1", "test_2", "test_3", "test_4", "test_5",
            "test_6", "test_7", "test_8", "test_9", "test_10",
        ]

        created_count = 0
        already_exists_count = 0
        error_count = 0

        for username in student_usernames:
            user_dir = os.path.join(base_path, username)

            # Check if user directory exists
            if not os.path.exists(user_dir):
                print(f"SKIP: User directory does not exist for {username}")
                error_count += 1
                continue

            examples_dir = os.path.join(user_dir, "Lecture_Examples")

            # Create Examples folder if it doesn't exist
            if os.path.exists(examples_dir):
                print(f"EXISTS: {username}/Lecture_Examples (already exists)")
                already_exists_count += 1
            else:
                try:
                    os.makedirs(examples_dir, exist_ok=True)
                    print(f"CREATED: {username}/Lecuture_Examples")
                    created_count += 1
                except Exception as e:
                    print(f"ERROR: Failed to create {username}/Lecture_Examples - {e}")
                    error_count += 1

        print("\n=== MIGRATION SUMMARY ===")
        print(f"Total students: {len(student_usernames)}")
        print(f"✅ Created: {created_count}")
        print(f"⏭️  Already exists: {already_exists_count}")
        print(f"❌ Errors: {error_count}")
        print(f"✅ Migration complete!")

    except Exception as e:
        print(f"ERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    add_examples_folders()
