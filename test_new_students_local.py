#!/usr/bin/env python3
"""
Test script to add new student accounts to local PostgreSQL database
"""

import os
import sys
import psycopg2
import bcrypt

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def test_local_accounts():
    """Add new student accounts to local database for testing"""
    
    # New students with their credentials from FINAL_CREDENTIALS.txt
    new_students = [
        ('eif2018', 'Ethan Flores', 'O09R981J337*'),
        ('ql2499', 'Nick Li', 'G99R075N924#'),
        ('gs4387', 'Gursehaj Singh', 'J65R317F685@'),
        ('cw4973', 'Caden Wang', 'K74R382N830@'),
        ('jy4383', 'Jessica Yuan', 'C74R761I764@')
    ]
    
    print("=== Testing New Student Accounts Locally ===")
    
    # Try different local database connection methods
    connection_attempts = [
        # Standard local PostgreSQL
        {
            'host': 'localhost',
            'database': 'pythonide',
            'user': 'postgres',
            'password': 'postgres',
            'port': 5432
        },
        # Alternative with different user
        {
            'host': 'localhost', 
            'database': 'pythonide',
            'user': 'pythonide_admin',
            'password': 'postgres',
            'port': 5432
        },
        # Try with no password
        {
            'host': 'localhost',
            'database': 'pythonide', 
            'user': 'postgres',
            'password': '',
            'port': 5432
        }
    ]
    
    conn = None
    for i, config in enumerate(connection_attempts, 1):
        try:
            print(f"Attempt {i}: Connecting to local database...")
            conn = psycopg2.connect(**config)
            print(f"✅ Connected successfully with config {i}")
            break
        except Exception as e:
            print(f"❌ Attempt {i} failed: {e}")
            continue
    
    if not conn:
        print("\n❌ Could not connect to local PostgreSQL database")
        print("Please ensure PostgreSQL is running and database exists")
        print("\nTo set up local database:")
        print("  sudo service postgresql start")
        print("  sudo -u postgres createdb pythonide")
        print("  sudo -u postgres psql -c \"ALTER USER postgres PASSWORD 'postgres';\"")
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
        
        # Add new students
        success_count = 0
        for username, full_name, password in new_students:
            try:
                email = f"{username}@college.edu"
                password_hash = hash_password(password)
                
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
        
        # Verify accounts were created
        cursor.execute("SELECT username, full_name FROM users WHERE username IN %s", 
                      (tuple(s[0] for s in new_students),))
        created_accounts = cursor.fetchall()
        
        print(f"\n=== Summary ===")
        print(f"Accounts processed: {success_count}/5")
        print(f"Accounts in database: {len(created_accounts)}")
        
        print(f"\n=== Test Login Credentials ===")
        for username, full_name, password in new_students:
            print(f"{username:<12} : {password:<15} ({full_name})")
        
        cursor.close()
        conn.close()
        
        return success_count == 5
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    success = test_local_accounts()
    if success:
        print("\n✅ Ready to test locally! Start the local server:")
        print("   cd server && python3 server.py --port 10086")
        print("   Then visit: http://localhost:10086")
    else:
        print("\n❌ Setup incomplete. Check database connection.")