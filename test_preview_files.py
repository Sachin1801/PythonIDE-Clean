#!/usr/bin/env python3
"""
Test script to create sample files for testing the new preview functionality
"""

import os
import csv
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

# Create test directory
test_dir = "server/projects/ide/TestPreview"
os.makedirs(test_dir, exist_ok=True)

# 1. Create a test PNG image
img = Image.new('RGB', (800, 600), color=(73, 109, 137))
draw = ImageDraw.Draw(img)
draw.text((350, 280), "Test Image", fill=(255, 255, 255))
draw.rectangle([100, 100, 700, 500], outline=(255, 255, 255), width=3)
img.save(os.path.join(test_dir, "test_image.png"))
print("Created test_image.png")

# 2. Create a test CSV file
csv_file = os.path.join(test_dir, "test_data.csv")
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Age', 'City', 'Salary', 'Department'])
    writer.writerow(['John Doe', 30, 'New York', 75000, 'Engineering'])
    writer.writerow(['Jane Smith', 28, 'San Francisco', 85000, 'Design'])
    writer.writerow(['Bob Johnson', 35, 'Chicago', 65000, 'Marketing'])
    writer.writerow(['Alice Brown', 32, 'Boston', 90000, 'Engineering'])
    writer.writerow(['Charlie Davis', 29, 'Seattle', 70000, 'Sales'])
print("Created test_data.csv")

# 3. Create a Python file for comparison
py_file = os.path.join(test_dir, "regular_file.py")
with open(py_file, 'w') as f:
    f.write('''# This is a regular Python file
# It should open in the regular editor, not fullscreen

def hello_world():
    print("Hello, World!")
    
if __name__ == "__main__":
    hello_world()
''')
print("Created regular_file.py")

print(f"\nTest files created in: {test_dir}")
print("\nTo test the new functionality:")
print("1. Click on test_image.png - should open in fullscreen")
print("2. Click on test_data.csv - should open in fullscreen")
print("3. Click on regular_file.py - should open in regular editor")
print("4. Right-click on PNG/CSV files to see 'Open in Editor Tab' option")