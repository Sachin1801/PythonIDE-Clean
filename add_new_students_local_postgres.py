#!/usr/bin/env python3
"""
Add new student accounts to local PostgreSQL Docker database
"""

import psycopg2
import bcrypt
import csv
from datetime import datetime

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def connect_to_local_postgres():
    """Connect to local PostgreSQL Docker container"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,  # Docker container port
            database="pythonide",
            user="postgres",
            password="postgres"
        )
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None

def add_new_students_to_postgres():
    """Add new students from CSV to PostgreSQL database"""
    
    # New students that we need to add (the ones we just added to CSV)
    new_students = [
        ('sz3991', 'Shiwen Zhu', 'EaS08VX%fcp8'),
        ('eif2018', 'Ethan Flores', 'O09R981J337*'),
        ('ql2499', 'Nick Li', 'G99R075N924#'),
        ('gs4387', 'Gursehaj Singh', 'J65R317F685@'),
        ('cw4973', 'Caden Wang', 'K74R382N830@'),
        ('jy4383', 'Jessica Yuan', 'C74R761I764@')
    ]
    
    print("=== Adding New Students to Local PostgreSQL ===")
    
    conn = connect_to_local_postgres()
    if not conn:
        print("Could not connect to PostgreSQL Docker container")
        print("Make sure the container is running: docker ps | grep postgres")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("Creating users table...")
            cursor.execute('''
                CREATE TABLE users (
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
            conn.commit()
        
        success_count = 0
        for username, full_name, password in new_students:
            try:
                email = f"{username}@nyu.edu"
                password_hash = hash_password(password)
                
                # Insert or update user
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        full_name = EXCLUDED.full_name
                ''', (username, email, password_hash, full_name, 'student'))
                
                success_count += 1
                print(f"✅ Added/Updated: {username} ({full_name})")
                
            except Exception as e:
                print(f"❌ Failed to add {username}: {e}")
        
        conn.commit()
        
        # Verify accounts
        cursor.execute("""
            SELECT username, full_name, role 
            FROM users 
            WHERE username IN %s
        """, (tuple(s[0] for s in new_students),))
        created_accounts = cursor.fetchall()
        
        # Get total user count
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        print(f"\n=== Summary ===")
        print(f"Accounts processed: {success_count}/6")
        print(f"Accounts verified in database: {len(created_accounts)}")
        print(f"Total users in database: {total_users}")
        
        print(f"\n=== Local Test Credentials ===")
        for username, full_name, password in new_students:
            print(f"{username:<12} : {password:<15} ({full_name})")
        
        cursor.close()
        conn.close()
        
        return success_count >= 5
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    success = add_new_students_to_postgres()
    if success:
        print(f"\n✅ New students added to local PostgreSQL successfully!")
        print(f"✅ Student directories already exist in server/projects/ide/Local/")
        print(f"\nTo test locally:")
        print(f"  cd server && python3 server.py --port 10086")
        print(f"  Visit: http://localhost:10086")
        print(f"\nTry logging in with any of the new student accounts!")
        
        print(f"\nDirectories to check:")
        directories = ['sz3991', 'eif2018', 'ql2499', 'gs4387', 'cw4973', 'jy4383']
        for d in directories:
            print(f"  - server/projects/ide/Local/{d}/")
    else:
        print(f"\n❌ Some accounts failed to add. Check the output above.")