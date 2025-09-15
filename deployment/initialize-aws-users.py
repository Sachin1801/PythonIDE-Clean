#!/usr/bin/env python3
"""
Initialize users directly on AWS RDS PostgreSQL from local machine
This script connects to your AWS RDS and creates all users
"""
import os
import sys
import psycopg2
import bcrypt
from datetime import datetime
import csv

# AWS RDS Configuration
RDS_ENDPOINT = "pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com"
RDS_PORT = 5432
RDS_DATABASE = "pythonide"
RDS_USERNAME = "pythonide_admin"
RDS_PASSWORD = "Sachinadlakha9082"

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_users_from_csv():
    """Create all users from the CSV file"""
    csv_file = '/home/sachinadlakha/on-campus/PythonIDE-Clean/adminData/class_credentials_20250901_192739.csv'
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found at {csv_file}")
        return False
    
    # Connect to AWS RDS
    try:
        print(f"Connecting to AWS RDS at {RDS_ENDPOINT}...")
        conn = psycopg2.connect(
            host=RDS_ENDPOINT,
            port=RDS_PORT,
            database=RDS_DATABASE,
            user=RDS_USERNAME,
            password=RDS_PASSWORD
        )
        cursor = conn.cursor()
        print("✓ Connected to AWS RDS successfully")
        
        # Create tables if they don't exist
        print("Creating tables if needed...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255),
                password_hash TEXT NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_used BOOLEAN DEFAULT false
            )
        ''')
        
        conn.commit()
        print("✓ Tables created/verified")
        
        # Remove existing users (optional - comment out if you want to keep them)
        print("Removing existing users...")
        cursor.execute("DELETE FROM users")
        conn.commit()
        print("✓ Existing users removed")
        
        # Read CSV and create users
        print("Creating users from CSV...")
        with open(csv_file, 'r') as f:
            csv_reader = csv.DictReader(f)
            users_created = 0
            
            for row in csv_reader:
                username = row['Username'].strip()
                full_name = row['Full Name'].strip()
                password = row['Password'].strip()
                notes = row['Notes'].strip()
                
                # Determine role based on notes
                if 'Admin' in notes:
                    role = 'professor'
                else:
                    role = 'student'
                
                # Create email
                email = f"{username}@college.edu"
                
                # Hash password
                password_hash = hash_password(password)
                
                # Insert user
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE
                    SET email = EXCLUDED.email,
                        password_hash = EXCLUDED.password_hash,
                        full_name = EXCLUDED.full_name,
                        role = EXCLUDED.role
                ''', (username, email, password_hash, full_name, role))
                
                users_created += 1
                print(f"  ✓ Created {role}: {username} ({full_name})")
            
            conn.commit()
            print(f"\n✓ Created {users_created} users successfully")
            
        # Verify users
        cursor.execute("SELECT username, role, full_name FROM users ORDER BY role DESC, username")
        users = cursor.fetchall()
        
        print("\n" + "="*60)
        print("USERS IN AWS RDS DATABASE")
        print("="*60)
        
        admins = [u for u in users if u[1] == 'professor']
        students = [u for u in users if u[1] == 'student']
        
        print(f"\nAdmins ({len(admins)}):")
        for user in admins:
            print(f"  - {user[0]} ({user[2]})")
        
        print(f"\nStudents ({len(students)}):")
        for user in students:
            print(f"  - {user[0]} ({user[2]})")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("="*60)
    print("AWS RDS USER INITIALIZATION")
    print("="*60)
    print()
    print("Using AWS RDS configuration from environment...")
    
    if create_users_from_csv():
        print("\n✅ SUCCESS! All users created in AWS RDS")
        print("\nYou can now log in to your application at:")
        print("http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com")
        print("\nTest with:")
        print("  Admin: sa9082 / Admin@sa9082")
        print("  Student: na3649 / student@na3649")
    else:
        print("\n❌ Failed to create users")

if __name__ == "__main__":
    main()