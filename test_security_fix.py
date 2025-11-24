#!/usr/bin/env python3
"""
Test script to verify the file write permission fix.
This script tests various attack vectors that students might use to write to read-only directories.

EXPECTED BEHAVIOR:
- All write attempts to Lecture Notes/ should FAIL with PermissionError
- All read attempts from Lecture Notes/ should SUCCEED
- All write attempts to student's own Local/{username}/ should SUCCEED
"""

print("=" * 60)
print("SECURITY TEST: File Write Permission Enforcement")
print("=" * 60)

# Test 1: Try to write CSV to Lecture Notes using absolute path
print("\n[TEST 1] Attempting to write CSV to Lecture Notes (absolute path)")
try:
    with open('/mnt/efs/pythonide-data/Lecture Notes/malicious.csv', 'w') as f:
        f.write('hacked,data\n')
    print("❌ SECURITY BREACH: Write to Lecture Notes/ succeeded (SHOULD HAVE FAILED)")
except PermissionError as e:
    print(f"✅ BLOCKED: {e}")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Test 2: Try to write text file to Lecture Notes
print("\n[TEST 2] Attempting to write text file to Lecture Notes")
try:
    with open('/mnt/efs/pythonide-data/Lecture Notes/hack.txt', 'w') as f:
        f.write('This should not work')
    print("❌ SECURITY BREACH: Write succeeded (SHOULD HAVE FAILED)")
except PermissionError as e:
    print(f"✅ BLOCKED: {e}")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Test 3: Try to use pandas to write CSV to Lecture Notes
print("\n[TEST 3] Attempting pandas CSV write to Lecture Notes")
try:
    import pandas as pd
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    df.to_csv('/mnt/efs/pythonide-data/Lecture Notes/pandas_hack.csv')
    print("❌ SECURITY BREACH: Pandas write succeeded (SHOULD HAVE FAILED)")
except PermissionError as e:
    print(f"✅ BLOCKED: {e}")
except Exception as e:
    print(f"⚠️  Pandas not available or other error: {e}")

# Test 4: Try to use pathlib to write to Lecture Notes
print("\n[TEST 4] Attempting pathlib write to Lecture Notes")
try:
    from pathlib import Path
    Path('/mnt/efs/pythonide-data/Lecture Notes/pathlib_hack.txt').write_text('hacked')
    print("❌ SECURITY BREACH: Pathlib write succeeded (SHOULD HAVE FAILED)")
except PermissionError as e:
    print(f"✅ BLOCKED: {e}")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Test 5: Try to delete file in Lecture Notes
print("\n[TEST 5] Attempting to delete file in Lecture Notes")
try:
    import os
    os.remove('/mnt/efs/pythonide-data/Lecture Notes/some_file.txt')
    print("❌ SECURITY BREACH: Delete succeeded (SHOULD HAVE FAILED)")
except PermissionError as e:
    print(f"✅ BLOCKED: {e}")
except FileNotFoundError:
    print("⚠️  File doesn't exist (can't test delete)")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Test 6: Try to create directory in Lecture Notes
print("\n[TEST 6] Attempting to create directory in Lecture Notes")
try:
    import os
    os.mkdir('/mnt/efs/pythonide-data/Lecture Notes/hacked_folder')
    print("❌ SECURITY BREACH: mkdir succeeded (SHOULD HAVE FAILED)")
except PermissionError as e:
    print(f"✅ BLOCKED: {e}")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Test 7: Try to rename file across directories
print("\n[TEST 7] Attempting to rename/move file to Lecture Notes")
try:
    import os
    # This assumes there's a file in the student's directory
    os.rename('test.txt', '/mnt/efs/pythonide-data/Lecture Notes/moved.txt')
    print("❌ SECURITY BREACH: Rename to Lecture Notes succeeded (SHOULD HAVE FAILED)")
except PermissionError as e:
    print(f"✅ BLOCKED: {e}")
except FileNotFoundError:
    print("⚠️  Source file doesn't exist (can't test rename)")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Test 8: Try directory traversal attack
print("\n[TEST 8] Attempting directory traversal attack")
try:
    with open('/mnt/efs/pythonide-data/Local/student1/../Lecture Notes/traversal.txt', 'w') as f:
        f.write('traversal attack')
    print("❌ SECURITY BREACH: Directory traversal succeeded (SHOULD HAVE FAILED)")
except PermissionError as e:
    print(f"✅ BLOCKED: {e}")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Test 9: POSITIVE TEST - Read from Lecture Notes (SHOULD SUCCEED)
print("\n[TEST 9] Reading from Lecture Notes (SHOULD SUCCEED)")
try:
    # This will fail if the directory doesn't exist, but that's OK for testing
    import os
    files = os.listdir('/mnt/efs/pythonide-data/Lecture Notes')
    print(f"✅ SUCCESS: Read access to Lecture Notes/ works (found {len(files)} files)")
except FileNotFoundError:
    print("⚠️  Lecture Notes directory doesn't exist in test environment")
except PermissionError as e:
    print(f"❌ ERROR: Read access blocked (SHOULD HAVE SUCCEEDED): {e}")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Test 10: POSITIVE TEST - Write to student's own directory (SHOULD SUCCEED)
print("\n[TEST 10] Writing to student's own directory (SHOULD SUCCEED)")
try:
    # This test assumes script is running in student's Local/{username}/ directory
    with open('test_file.txt', 'w') as f:
        f.write('This is allowed')
    print("✅ SUCCESS: Write to own directory works")
    # Clean up
    import os
    os.remove('test_file.txt')
except PermissionError as e:
    print(f"❌ ERROR: Write to own directory blocked (SHOULD HAVE SUCCEEDED): {e}")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)
print("\nSUMMARY:")
print("- Tests 1-8: Should all be BLOCKED with PermissionError")
print("- Test 9: Should SUCCEED (read access to Lecture Notes)")
print("- Test 10: Should SUCCEED (write access to own directory)")
