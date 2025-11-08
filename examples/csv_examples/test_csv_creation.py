#!/usr/bin/env python3
"""
Diagnostic script to test CSV file creation and show exact location
"""
import csv
import os

# Show current working directory
print("=" * 60)
print("🔍 DIAGNOSTIC INFORMATION")
print("=" * 60)
print(f"Current working directory: {os.getcwd()}")
print(f"Script location: {os.path.abspath(__file__)}")
print()

# Create CSV file
csv_filename = 'test_students.csv'
print(f"Creating CSV file: {csv_filename}")

with open(csv_filename, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Name', 'StudentID', 'Grade', 'GPA'])
    writer.writerow(['Alice Johnson', 'A001', 'Junior', 3.8])
    writer.writerow(['Bob Smith', 'A002', 'Sophomore', 3.5])

print(f"✅ CSV file created successfully!")
print()

# Get absolute path of created file
abs_path = os.path.abspath(csv_filename)
print(f"📁 Absolute path: {abs_path}")
print()

# Verify file exists
if os.path.exists(csv_filename):
    file_size = os.path.getsize(csv_filename)
    print(f"✅ File verification: EXISTS")
    print(f"📊 File size: {file_size} bytes")
else:
    print(f"❌ File verification: NOT FOUND")
print()

# List all CSV files in current directory
print("📋 All CSV files in current directory:")
csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
if csv_files:
    for f in csv_files:
        size = os.path.getsize(f)
        print(f"  - {f} ({size} bytes)")
else:
    print("  (no CSV files found)")

print()
print("=" * 60)
print("🎯 TO SEE THE FILE IN IDE:")
print("1. Refresh the file tree (click refresh icon)")
print("2. Navigate to the same folder as this script")
print("3. Look for 'test_students.csv'")
print("=" * 60)
