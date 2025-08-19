#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager

def create_initial_users():
    manager = UserManager()
    
    # Create professor account
    success, msg = manager.create_user(
        username='professor',
        email='professor@college.edu',
        password='ChangeMeASAP2024!',
        full_name='Susan Liao',
        role='professor'
    )
    if success:
        print(f"✓ Created professor account")
    else:
        print(f"✗ Failed to create professor: {msg}")
    
    # Create sample students (you can expand this list)
    students = [
        ('sa9082', 'sa9082@nyu.edu', 'Sachin Adlakha'),
        ('jd1234', 'jd1234@college.edu', 'John Doe'),
        ('ab5678', 'ab5678@college.edu', 'Alice Brown'),
        ('mk9012', 'mk9012@college.edu', 'Mary Kim'),
        ('rs3456', 'rs3456@college.edu', 'Robert Smith'),
        ('lj7890', 'lj7890@college.edu', 'Linda Johnson'),
        ('tm2345', 'tm2345@college.edu', 'Tom Miller'),
        ('sw6789', 'sw6789@college.edu', 'Sarah Wilson'),
        ('dg0123', 'dg0123@college.edu', 'David Garcia'),
        ('jm4567', 'jm4567@college.edu', 'Jennifer Martinez'),
        # Add more students as needed to reach 60
    ]
    
    created_count = 0
    for username, email, full_name in students:
        # Generate initial password (username + year)
        initial_password = f"{username}2024"
        
        success, msg = manager.create_user(
            username=username,
            email=email,
            password=initial_password,
            full_name=full_name,
            role='student'
        )
        
        if success:
            print(f"✓ Created user: {username}")
            created_count += 1
        else:
            print(f"✗ Failed to create {username}: {msg}")
    
    print(f"\n{'='*50}")
    print(f"Created {created_count + 1} users total (1 professor + {created_count} students)")
    print(f"{'='*50}")
    print("\nInitial passwords:")
    print("  Professor: ChangeMeASAP2024!")
    print("  Students: {username}2024")
    print("\n⚠️  IMPORTANT: Users should change these passwords after first login!")
    
    return True

def add_bulk_students(start_num=1, end_num=60):
    """Helper function to add many students at once"""
    manager = UserManager()
    created = 0
    
    for i in range(start_num, end_num + 1):
        username = f"student{i:03d}"  # student001, student002, etc.
        email = f"{username}@college.edu"
        full_name = f"Student {i}"
        password = f"{username}2024"
        
        success, msg = manager.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role='student'
        )
        
        if success:
            created += 1
            if i % 10 == 0:  # Progress indicator
                print(f"  Created {created} students...")
        
    print(f"✓ Bulk created {created} students")
    return created

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Create initial users for Python IDE')
    parser.add_argument('--bulk', action='store_true', 
                        help='Create 60 numbered student accounts (student001-student060)')
    parser.add_argument('--start', type=int, default=1,
                        help='Starting student number for bulk creation')
    parser.add_argument('--end', type=int, default=60,
                        help='Ending student number for bulk creation')
    
    args = parser.parse_args()
    
    if args.bulk:
        print("Creating bulk student accounts...")
        add_bulk_students(args.start, args.end)
        # Also create the professor
        manager = UserManager()
        success, msg = manager.create_user(
            username='professor',
            email='professor@college.edu',
            password='ChangeMeASAP2024!',
            full_name='Dr. Smith',
            role='professor'
        )
        if success:
            print("✓ Created professor account")
    else:
        print("Creating initial users...")
        create_initial_users()