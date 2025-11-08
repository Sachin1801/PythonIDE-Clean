#!/usr/bin/env python3
"""
Example 3: CSV Dictionary Operations
Using DictReader and DictWriter for easier column access
"""
import csv

# Write using DictWriter
print("Creating grades.csv with DictWriter...")
with open('grades.csv', 'w', newline='') as file:
    fieldnames = ['Student', 'Assignment', 'Score', 'MaxPoints']
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerow({'Student': 'Alice', 'Assignment': 'HW1', 'Score': 95, 'MaxPoints': 100})
    writer.writerow({'Student': 'Bob', 'Assignment': 'HW1', 'Score': 87, 'MaxPoints': 100})
    writer.writerow({'Student': 'Charlie', 'Assignment': 'HW1', 'Score': 92, 'MaxPoints': 100})
    writer.writerow({'Student': 'Alice', 'Assignment': 'Quiz1', 'Score': 18, 'MaxPoints': 20})
    writer.writerow({'Student': 'Bob', 'Assignment': 'Quiz1', 'Score': 19, 'MaxPoints': 20})

print("✅ grades.csv created\n")

# Read using DictReader
print("Reading with DictReader:")
print("-" * 60)

with open('grades.csv', 'r') as file:
    reader = csv.DictReader(file)

    for row in reader:
        # Access by column name
        score = int(row['Score'])
        max_points = int(row['MaxPoints'])
        percentage = (score / max_points) * 100

        print(f"{row['Student']:10} | {row['Assignment']:8} | "
              f"{score}/{max_points} | {percentage:.1f}%")

print("-" * 60)
