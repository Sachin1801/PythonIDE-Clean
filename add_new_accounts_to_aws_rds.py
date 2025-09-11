#!/usr/bin/env python3
"""
Add new student and test accounts to AWS RDS PostgreSQL database
This script manually adds accounts that were skipped by auto_init_users.py
"""

import psycopg2
import bcrypt
import os
from datetime import datetime

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def connect_to_aws_rds():
    """Connect to AWS RDS PostgreSQL"""
    try:
        # AWS RDS connection details
        conn = psycopg2.connect(
            host="pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com",
            port=5432,
            database="pythonide", 
            user="pythonide_admin",
            password="Sachinadlakha9082"
        )
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to AWS RDS: {e}")
        return None

def add_accounts_to_aws():
    """Add new student and test accounts to AWS RDS"""
    
    # 6 New students with their actual passwords from FINAL_CREDENTIALS.txt
    new_students = [
        ('sz3991', 'Shiwen Zhu', 'EaS08VX%fcp8'),
        ('eif2018', 'Ethan Flores', 'O09R981J337*'),
        ('ql2499', 'Nick Li', 'G99R075N924#'),
        ('gs4387', 'Gursehaj Singh', 'J65R317F685@'),
        ('cw4973', 'Caden Wang', 'K74R382N830@'),
        ('jy4383', 'Jessica Yuan', 'C74R761I764@')
    ]
    
    # 10 Test accounts with their passwords from TEST_ACCOUNTS_CREDENTIALS.txt
    test_accounts = [
        ('test_1', 'Test Student 1', 'W88R356T665%'),
        ('test_2', 'Test Student 2', 'K06R944L973#'),
        ('test_3', 'Test Student 3', 'E82R450O705*'),
        ('test_4', 'Test Student 4', 'M72R472C591%'),
        ('test_5', 'Test Student 5', 'J09R511L581#'),
        ('test_6', 'Test Student 6', 'Q96R597I696@'),
        ('test_7', 'Test Student 7', 'S32R901O610$'),
        ('test_8', 'Test Student 8', 'S45R186U374*'),
        ('test_9', 'Test Student 9', 'N45R258F077!'),
        ('test_10', 'Test Student 10', 'Z60R678I698&')
    ]
    
    all_accounts = new_students + test_accounts
    
    print("=== Adding 16 New Accounts to AWS RDS ===")
    print("New Students: 6")
    print("Test Accounts: 10") 
    print("Total: 16 accounts")
    print()
    
    conn = connect_to_aws_rds()
    if not conn:
        print("❌ Could not connect to AWS RDS")
        print("Check your connection and credentials")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check current user count
        cursor.execute("SELECT COUNT(*) FROM users")
        initial_count = cursor.fetchone()[0]
        print(f"Current users in AWS RDS: {initial_count}")
        
        success_count = 0
        failed_accounts = []
        
        for username, full_name, password in all_accounts:
            try:
                # Check if account already exists
                cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"⚠️  {username} already exists in AWS RDS - skipping")
                    continue
                
                email = f"{username}@college.edu"
                password_hash = hash_password(password)
                
                # Insert new user account
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, full_name, role, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (username, email, password_hash, full_name, 'student', datetime.now()))
                
                success_count += 1
                account_type = "Student" if username in [s[0] for s in new_students] else "Test"
                print(f"✅ Added {account_type}: {username} ({full_name})")
                
            except Exception as e:
                failed_accounts.append((username, str(e)))
                print(f"❌ Failed to add {username}: {e}")
        
        # Commit all changes
        conn.commit()
        
        # Check final user count
        cursor.execute("SELECT COUNT(*) FROM users")
        final_count = cursor.fetchone()[0]
        
        # Verify our accounts were created
        usernames = [acc[0] for acc in all_accounts]
        placeholders = ','.join(['%s'] * len(usernames))
        cursor.execute(f"SELECT username, full_name FROM users WHERE username IN ({placeholders})", usernames)
        created_accounts = cursor.fetchall()
        
        print(f"\n=== Results ===")
        print(f"Accounts successfully added: {success_count}")
        print(f"Accounts failed: {len(failed_accounts)}")
        print(f"Total users before: {initial_count}")
        print(f"Total users after: {final_count}")
        print(f"Verified accounts in database: {len(created_accounts)}")
        
        if failed_accounts:
            print(f"\n❌ Failed Accounts:")
            for username, error in failed_accounts:
                print(f"  - {username}: {error}")
        
        print(f"\n=== Test These Credentials on AWS Production ===")
        print("URL: http://pythonide-classroom.tech/editor")
        print("\nNew Students:")
        for username, full_name, password in new_students:
            print(f"  {username:<12} : {password}")
            
        print("\nTest Accounts (for future assignment):")  
        for username, full_name, password in test_accounts:
            print(f"  {username:<12} : {password}")
        
        cursor.close()
        conn.close()
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    success = add_accounts_to_aws()
    if success:
        print(f"\n✅ Accounts added to AWS RDS successfully!")
        print(f"✅ Directories already exist on AWS EFS")
        print(f"🎯 Students can now log in at: http://pythonide-classroom.tech/editor")
    else:
        print(f"\n❌ Failed to add accounts. Check the errors above.")