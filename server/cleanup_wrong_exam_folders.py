#!/usr/bin/env python3
"""
Cleanup script to remove incorrectly named folders in exam environment
ONLY runs on exam environment paths - will NOT touch main IDE folders

Safety Features:
- Only targets exam-specific paths (containing 'exam' in path name)
- Will not touch main IDE paths (/mnt/efs/pythonide-data)
- Deletes ONLY folders without "exam_" prefix that match known NetIDs
- Provides detailed logging of all actions
"""
import os
import shutil
import sys


def cleanup_wrong_folders(dry_run=False):
    """
    Remove folders without exam_ prefix in exam environment

    Args:
        dry_run (bool): If True, only print what would be deleted without actually deleting
    """
    print("=" * 70)
    print("EXAM ENVIRONMENT FOLDER CLEANUP SCRIPT")
    print("=" * 70)
    print(f"Mode: {'DRY RUN (no actual deletion)' if dry_run else 'LIVE (will delete folders)'}")
    print()

    # ONLY target exam environment paths
    exam_paths = [
        "/mnt/efs/pythonide-data-exam/ide/Local",  # Production EFS
        "/app/server/exam-projects/ide/Local",      # Docker volume
        "/tmp/pythonide-data-exam/ide/Local"        # Local testing
    ]

    # List of expected NetIDs (without exam_ prefix) - these are WRONG folders if found
    wrong_folder_names = [
        "sa8820", "na3649", "ntb5594", "hrb9324", "nd2560",
        "ag11389", "arg9667", "lh4052", "jh9963", "ch5315",
        "wh2717", "bsj5539", "fk2248", "nvk9963", "sil9056",
        "hl6459", "zl3894", "jom2045", "arm9283", "zm2525",
        "im2420", "jn3143", "jn9106", "djp10030", "ap10062",
        "bap9618", "fp2331", "srp8204", "agr8457", "shs9941",
        "as19217", "mat9481", "cw4715", "jw9248", "sz4766",
        "sz3991", "eif2018", "ql2499", "gs4387", "cw4973", "jy4383",
        "test_1", "test_2", "test_3", "test_4", "test_5",
        "test_6", "test_7", "test_8", "test_9", "test_10",
    ]

    total_deleted = 0
    total_checked = 0

    for base_path in exam_paths:
        if not os.path.exists(base_path):
            print(f"⏭️  Skipping (path doesn't exist): {base_path}")
            continue

        print(f"\n📂 Checking exam path: {base_path}")

        # Safety check: ensure this is an exam path
        if "exam" not in base_path.lower():
            print(f"⚠️  SAFETY CHECK FAILED - Not an exam path: {base_path}")
            print(f"   Skipping to prevent accidental deletion of main IDE folders!")
            continue

        # Additional safety: ensure this is NOT main IDE path
        if "pythonide-data/ide" in base_path and "exam" not in base_path:
            print(f"⚠️  SAFETY CHECK FAILED - This looks like main IDE path: {base_path}")
            print(f"   Skipping to prevent accidental deletion!")
            continue

        # List all folders
        try:
            folder_list = os.listdir(base_path)
            print(f"   Found {len(folder_list)} items in directory")
        except Exception as e:
            print(f"❌ Error listing directory: {e}")
            continue

        for folder_name in folder_list:
            folder_path = os.path.join(base_path, folder_name)
            total_checked += 1

            # Only process directories, not files
            if not os.path.isdir(folder_path):
                print(f"   ⏭️  Skipping (not a directory): {folder_name}")
                continue

            # Check if folder lacks "exam_" prefix and matches known NetIDs
            if folder_name in wrong_folder_names:
                # This is a wrong folder (NetID without "exam_" prefix)
                if dry_run:
                    print(f"   🔍 [DRY RUN] Would delete: {folder_name}")
                else:
                    try:
                        print(f"   🗑️  Deleting wrong folder: {folder_name}")
                        shutil.rmtree(folder_path)
                        print(f"   ✅ Deleted successfully: {folder_name}")
                        total_deleted += 1
                    except Exception as e:
                        print(f"   ❌ Error deleting {folder_name}: {e}")
            elif folder_name.startswith("exam_"):
                # This is a correct folder - keep it
                print(f"   ✅ Keeping correct folder: {folder_name}")
            else:
                # Unknown folder (not in our list) - report but don't delete
                print(f"   ⚠️  Unknown folder (not deleted): {folder_name}")

    print()
    print("=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    print(f"Total items checked: {total_checked}")
    if dry_run:
        print(f"Folders that would be deleted: {total_deleted}")
        print()
        print("⚠️  This was a DRY RUN - no actual deletion occurred")
        print("Run with --live to actually delete the folders")
    else:
        print(f"Folders deleted: {total_deleted}")
        print()
        print("✅ Cleanup completed successfully!")
    print("=" * 70)


def main():
    """Command line interface for cleanup script"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Cleanup incorrectly named folders in exam environment"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually delete folders (default is dry-run mode)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only show what would be deleted without actually deleting (default)"
    )

    args = parser.parse_args()

    # If --live is specified, turn off dry-run
    dry_run = not args.live

    if not dry_run:
        print()
        print("⚠️  WARNING: You are about to delete folders!")
        print("⚠️  This will only affect exam environment paths.")
        print("⚠️  Main IDE folders will NOT be touched.")
        print()
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted by user.")
            sys.exit(0)

    cleanup_wrong_folders(dry_run=dry_run)


if __name__ == "__main__":
    main()
