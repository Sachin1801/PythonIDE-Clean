#!/usr/bin/env python3
"""
Example 1: Basic CSV Writing
This script demonstrates how to create a CSV file with student data
"""
import csv

# Create a CSV file
with open('students.csv', 'w', newline='') as file:
    writer = csv.writer(file)

    # Write header
    writer.writerow(['Name', 'StudentID', 'Grade', 'GPA'])

    # Write student records
    writer.writerow(['Alice Johnson', 'A001', 'Junior', 3.8])
    writer.writerow(['Bob Smith', 'A002', 'Sophomore', 3.5])
    writer.writerow(['Charlie Brown', 'A003', 'Senior', 3.9])
    writer.writerow(['Diana Prince', 'A004', 'Freshman', 4.0])

print("✅ CSV file 'students.csv' created successfully!")
print("📁 File location: Same directory as this script")
print("\nRun example2_basic_read.py to read this file")
