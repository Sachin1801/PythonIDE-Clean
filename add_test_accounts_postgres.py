#!/usr/bin/env python3
"""
Add test accounts to local PostgreSQL Docker database
"""

import psycopg2
import bcrypt

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

def add_test_accounts_to_postgres():
    """Add test accounts from credentials to PostgreSQL database"""
    
    # Test accounts with their generated passwords
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
    
    print("=== Adding Test Accounts to Local PostgreSQL ===")
    
    conn = connect_to_local_postgres()
    if not conn:
        print("Could not connect to PostgreSQL Docker container")
        return False
    
    try:
        cursor = conn.cursor()
        
        success_count = 0
        for username, full_name, password in test_accounts:
            try:
                email = f"{username}@nyu.edu"
                password_hash = hash_password(password)
                
                # Insert or update user
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        full_name = EXCLUDED.full_name,
                        email = EXCLUDED.email
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
            WHERE username LIKE 'test_%'
            ORDER BY username
        """)
        created_accounts = cursor.fetchall()
        
        # Get total user count
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        print(f"\n=== Summary ===")
        print(f"Test accounts processed: {success_count}/10")
        print(f"Test accounts verified in database: {len(created_accounts)}")
        print(f"Total users in database: {total_users}")
        
        print(f"\n=== Test Account Credentials (for verification) ===")
        for username, full_name, password in test_accounts:
            print(f"{username:<12} : {password:<15} ({full_name})")
        
        cursor.close()
        conn.close()
        
        return success_count == 10
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    success = add_test_accounts_to_postgres()
    if success:
        print(f"\n✅ Test accounts added to local PostgreSQL successfully!")
        print(f"✅ Test account directories already exist in server/projects/ide/Local/")
        print(f"\nThese accounts are ready for reassignment to real students.")
        print(f"When reassigning:")
        print(f"1. Update username, full_name, email in database")
        print(f"2. Rename directory from Local/test_X/ to Local/{{new_username}}/")  
        print(f"3. Update welcome.py with new username")
        print(f"4. Password and all work files remain unchanged")
    else:
        print(f"\n❌ Some test accounts failed to add. Check the output above.")