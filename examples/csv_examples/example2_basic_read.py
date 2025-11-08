#!/usr/bin/env python3
"""
Example 2: Basic CSV Reading
This script demonstrates how to read a CSV file
Run example1_basic_write.py first to create the CSV file
"""
import csv
import os

# Check if file exists
if not os.path.exists('students.csv'):
    print("❌ Error: students.csv not found!")
    print("Please run example1_basic_write.py first")
    exit(1)

# Read the CSV file
print("📖 Reading students.csv...")
print("-" * 60)

with open('students.csv', 'r') as file:
    reader = csv.reader(file)

    # Read header
    header = next(reader)
    print(f"Columns: {', '.join(header)}\n")

    # Read each row
    for row in reader:
        name, student_id, grade, gpa = row
        print(f"{name:20} | {student_id} | {grade:10} | GPA: {gpa}")

print("-" * 60)
print("✅ File read successfully!")
