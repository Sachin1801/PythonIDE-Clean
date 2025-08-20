#!/usr/bin/env python3
import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

def backup_existing_files():
    """Create backup of existing files before migration"""
    base_path = Path('server/projects/ide')
    if not base_path.exists():
        base_path = Path('projects/ide')
        if not base_path.exists():
            print("No existing files to backup")
            return None
    
    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(f'backups/pre_migration_{timestamp}')
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy existing files
    print(f"Creating backup at {backup_dir}...")
    for item in base_path.iterdir():
        if item.is_dir():
            shutil.copytree(item, backup_dir / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, backup_dir / item.name)
    
    # Create manifest
    manifest_path = backup_dir / 'manifest.txt'
    with open(manifest_path, 'w') as f:
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                f.write(f"{os.path.join(root, file)}\n")
    
    print(f"✓ Backup created at: {backup_dir}")
    return backup_dir

def setup_directory_structure():
    """Setup the new directory structure for multi-user system"""
    
    # Determine base path
    if Path('server/projects/ide').exists():
        base_path = Path('server/projects/ide')
    elif Path('projects/ide').exists():
        base_path = Path('projects/ide')
    else:
        base_path = Path('server/projects/ide')
        base_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Setting up directory structure at: {base_path}")
    
    # Create main directories
    main_dirs = ['Local', 'Lecture Notes', 'Assignments', 'Tests']
    
    for dir_name in main_dirs:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {dir_name}/")
        
        # Add README files to explain each directory
        readme_path = dir_path / 'README.md'
        
        if dir_name == 'Local':
            readme_content = """# Local User Directories

This directory contains individual user workspaces.
Each user has their own subdirectory: Local/{username}/

Students can only access their own directory.
Professors can access all directories."""
        
        elif dir_name == 'Lecture Notes':
            readme_content = """# Lecture Notes

This directory contains course materials uploaded by professors.
- Students have read-only access
- Professors have full access

Materials are organized by topic or week."""
        
        elif dir_name == 'Assignments':
            readme_content = """# Assignments

This directory contains assignment descriptions and submissions.
- Assignment descriptions are uploaded by professors
- Students submit their work in their own subdirectories
- Structure: Assignments/{assignment_name}/{username}/"""
        
        elif dir_name == 'Tests':
            readme_content = """# Tests

This directory contains test materials and submissions.
- Test descriptions are uploaded by professors
- Students submit their work during test periods
- Structure: Tests/{test_name}/{username}/"""
        
        readme_path.write_text(readme_content)
    
    # Move existing files to a migration folder if they exist
    existing_items = []
    for item in base_path.iterdir():
        if item.name not in main_dirs and item.name != 'README.md':
            existing_items.append(item)
    
    if existing_items:
        migration_dir = base_path / 'Local' / '_migrated_files'
        migration_dir.mkdir(parents=True, exist_ok=True)
        
        for item in existing_items:
            if item.is_file():
                shutil.move(str(item), str(migration_dir / item.name))
                print(f"  Moved {item.name} to migration folder")
    
    print("\n✓ Directory structure setup complete!")
    return base_path

def initialize_student_directories():
    """Create individual directories for each student"""
    
    # Get database path
    if os.path.exists('ide.db'):
        db_path = 'ide.db'
    elif os.path.exists('server/ide.db'):
        db_path = 'server/ide.db'
    else:
        print("Database not found! Run create_users.py first.")
        return False
    
    # Get base path
    if Path('server/projects/ide').exists():
        base_path = Path('server/projects/ide')
    elif Path('projects/ide').exists():
        base_path = Path('projects/ide')
    else:
        base_path = Path('server/projects/ide')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT username, full_name, role FROM users")
    users = cursor.fetchall()
    
    local_path = base_path / 'Local'
    local_path.mkdir(parents=True, exist_ok=True)
    
    created_count = 0
    for username, full_name, role in users:
        # Create user's personal directory
        user_dir = local_path / username
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (user_dir / 'workspace').mkdir(exist_ok=True)
        (user_dir / 'submissions').mkdir(exist_ok=True)
        
        # Create welcome file
        welcome_file = user_dir / 'welcome.py'
        if role == 'student':
            welcome_content = f'''# Welcome {full_name}!
# This is your personal Python workspace

# Try running this simple program:
print("Hello, {full_name}!")
print("Welcome to the Python IDE")

# Your workspace structure:
# - workspace/   : Your coding projects
# - submissions/ : Your submitted assignments

# Quick tips:
# 1. Press Ctrl+S (Cmd+S on Mac) to save your work
# 2. Click Run to execute your code
# 3. Use the console below for output
# 4. Your work is automatically saved to your personal directory

# Let's try some Python:
name = "{username}"
print(f"Your username is: {{name}}")
print(f"Today you'll learn Python programming!")

# Try modifying this code and running it again!
'''
        else:  # Professor
            welcome_content = f'''# Welcome Professor {full_name}!
# This is your workspace with full access to the IDE

# As a professor, you can:
# - Access all student directories
# - Upload lecture materials
# - Grade assignments
# - View all submissions

# Directory structure:
# - Local/{username}/     : Your personal workspace
# - Local/[students]/     : Student workspaces (you have access)
# - Lecture Notes/        : Upload course materials here
# - Assignments/          : Create assignments and view submissions
# - Tests/               : Create tests and view submissions

print("Professor Dashboard Ready")
print(f"Welcome, {full_name}")
print("You have full administrative access")
'''
        
        welcome_file.write_text(welcome_content)
        
        # Create a sample Python file
        sample_file = user_dir / 'workspace' / 'example.py'
        sample_content = '''# Example Python Program
# This file demonstrates basic Python concepts

def greet(name):
    """A simple greeting function"""
    return f"Hello, {name}!"

def calculate_average(numbers):
    """Calculate the average of a list of numbers"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

# Main program
if __name__ == "__main__":
    # Test the greeting function
    print(greet("Python Learner"))
    
    # Test the average function
    scores = [85, 92, 78, 95, 88]
    avg = calculate_average(scores)
    print(f"Average score: {avg:.2f}")
    
    # Try a simple loop
    print("\\nCounting to 5:")
    for i in range(1, 6):
        print(f"  {i}")
'''
        sample_file.write_text(sample_content)
        
        created_count += 1
        print(f"✓ Initialized directory for {username} ({role})")
    
    conn.close()
    
    print(f"\n✓ Created directories for {created_count} users")
    return True

def create_sample_lecture_notes():
    """Create sample lecture materials for testing"""
    
    # Get base path
    if Path('server/projects/ide').exists():
        base_path = Path('server/projects/ide')
    elif Path('projects/ide').exists():
        base_path = Path('projects/ide')
    else:
        base_path = Path('server/projects/ide')
    
    lecture_path = base_path / 'Lecture Notes'
    
    # Create Week 1 materials
    week1_path = lecture_path / 'Week 1 - Introduction'
    week1_path.mkdir(parents=True, exist_ok=True)
    
    intro_file = week1_path / 'introduction.py'
    intro_content = '''# Week 1: Introduction to Python
# Professor: Dr. Smith

"""
Learning Objectives:
1. Understand Python basics
2. Learn about variables and data types
3. Write your first Python program
"""

# 1. Print statements
print("Welcome to Python Programming!")
print("Python is a powerful and easy-to-learn language")

# 2. Variables and data types
name = "Student"          # String
age = 20                 # Integer  
gpa = 3.75              # Float
is_enrolled = True      # Boolean

# 3. Basic operations
result = 10 + 5
print(f"10 + 5 = {result}")

# 4. Getting user input
# Uncomment to try:
# user_name = input("What's your name? ")
# print(f"Hello, {user_name}!")

# Practice exercise:
# Write a program that asks for two numbers and prints their sum
'''
    intro_file.write_text(intro_content)
    
    # Create Week 2 materials
    week2_path = lecture_path / 'Week 2 - Control Flow'
    week2_path.mkdir(parents=True, exist_ok=True)
    
    control_file = week2_path / 'control_flow.py'
    control_content = '''# Week 2: Control Flow in Python

# 1. If statements
score = 85

if score >= 90:
    grade = 'A'
elif score >= 80:
    grade = 'B'
elif score >= 70:
    grade = 'C'
else:
    grade = 'F'

print(f"Score: {score}, Grade: {grade}")

# 2. Loops
print("\\nFor loop example:")
for i in range(5):
    print(f"Iteration {i}")

print("\\nWhile loop example:")
count = 0
while count < 3:
    print(f"Count is {count}")
    count += 1

# 3. List comprehensions
numbers = [1, 2, 3, 4, 5]
squares = [n**2 for n in numbers]
print(f"\\nSquares: {squares}")
'''
    control_file.write_text(control_content)
    
    print("✓ Created sample lecture notes")

def create_sample_assignments():
    """Create sample assignment templates"""
    
    # Get base path
    if Path('server/projects/ide').exists():
        base_path = Path('server/projects/ide')
    elif Path('projects/ide').exists():
        base_path = Path('projects/ide')
    else:
        base_path = Path('server/projects/ide')
    
    assignments_path = base_path / 'Assignments'
    
    # Assignment 1
    hw1_path = assignments_path / 'Assignment_1_Variables'
    hw1_path.mkdir(parents=True, exist_ok=True)
    
    hw1_file = hw1_path / 'instructions.py'
    hw1_content = '''# Assignment 1: Variables and Basic Operations
# Due Date: End of Week 2
# Points: 100

"""
Instructions:
1. Complete all the functions below
2. Test your code with the provided test cases
3. Submit your completed file

Grading:
- Correctness: 70%
- Code style: 20%
- Comments: 10%
"""

def calculate_area(length, width):
    """
    Calculate the area of a rectangle
    
    Args:
        length: The length of the rectangle
        width: The width of the rectangle
    
    Returns:
        The area of the rectangle
    """
    # TODO: Implement this function
    pass

def convert_temperature(celsius):
    """
    Convert Celsius to Fahrenheit
    Formula: F = (C * 9/5) + 32
    
    Args:
        celsius: Temperature in Celsius
    
    Returns:
        Temperature in Fahrenheit
    """
    # TODO: Implement this function
    pass

def find_average(numbers):
    """
    Find the average of a list of numbers
    
    Args:
        numbers: A list of numbers
    
    Returns:
        The average of the numbers
    """
    # TODO: Implement this function
    pass

# Test cases (DO NOT MODIFY)
if __name__ == "__main__":
    # Test calculate_area
    assert calculate_area(5, 3) == 15
    assert calculate_area(10, 10) == 100
    
    # Test convert_temperature
    assert convert_temperature(0) == 32
    assert convert_temperature(100) == 212
    
    # Test find_average
    assert find_average([1, 2, 3, 4, 5]) == 3
    assert find_average([10, 20, 30]) == 20
    
    print("All tests passed! Great job!")
'''
    hw1_file.write_text(hw1_content)
    
    print("✓ Created sample assignments")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup directory structure for Python IDE')
    parser.add_argument('--backup', action='store_true', 
                        help='Create backup of existing files')
    parser.add_argument('--skip-samples', action='store_true',
                        help='Skip creating sample files')
    
    args = parser.parse_args()
    
    print("="*50)
    print("Directory Structure Setup")
    print("="*50)
    
    # Create backup if requested
    if args.backup:
        backup_existing_files()
    
    # Setup directory structure
    setup_directory_structure()
    
    # Initialize student directories
    print("\nInitializing user directories...")
    if not initialize_student_directories():
        print("Failed to initialize student directories")
        print("Make sure the database exists (run create_users.py first)")
        exit(1)
    
    # Create sample content unless skipped
    if not args.skip_samples:
        print("\nCreating sample content...")
        create_sample_lecture_notes()
        create_sample_assignments()
    
    print("\n" + "="*50)
    print("✓ Directory structure setup complete!")
    print("="*50)
    print("\nDirectory layout:")
    print("  server/projects/ide/")
    print("    ├── Local/           (User workspaces)")
    print("    ├── Lecture Notes/   (Course materials)")
    print("    ├── Assignments/     (Homework & submissions)")
    print("    └── Tests/          (Exams & submissions)")