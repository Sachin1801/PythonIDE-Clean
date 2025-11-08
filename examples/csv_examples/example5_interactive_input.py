#!/usr/bin/env python3
"""
Example 5: Interactive CSV Data Entry
Demonstrates collecting user input and saving to CSV
"""
import csv
import os

# File name
filename = 'student_survey.csv'

# Check if file exists, if not create with header
if not os.path.exists(filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Course', 'Rating', 'Comments'])
    print(f"📝 Created new survey file: {filename}\n")

# Collect survey response
print("=== Student Course Survey ===")
print("Please provide your feedback:\n")

name = input("Your name: ")
course = input("Course name: ")
rating = input("Rating (1-5): ")
comments = input("Comments: ")

# Append to CSV
with open(filename, 'a', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([name, course, rating, comments])

print("\n✅ Response saved to student_survey.csv")

# Display all responses
print("\n📊 All Survey Responses:")
print("=" * 80)

with open(filename, 'r') as file:
    reader = csv.reader(file)
    header = next(reader)

    # Print header
    print(f"{header[0]:15} | {header[1]:20} | {header[2]:6} | {header[3]}")
    print("-" * 80)

    # Print responses
    for row in reader:
        if len(row) >= 4:
            print(f"{row[0]:15} | {row[1]:20} | {row[2]:6} | {row[3]}")

print("=" * 80)
