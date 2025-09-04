#!/usr/bin/env python3
"""
Fix the Jan-06 username issue in AWS RDS
Run this once to update existing database
"""
import psycopg2
import bcrypt

# AWS RDS Configuration
RDS_HOST = "pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com"
RDS_PORT = 5432
RDS_DATABASE = "pythonide"
RDS_USERNAME = "pythonide_admin"
RDS_PASSWORD = "Sachinadlakha9082"

def fix_username():
    """Fix the Jan-06 username to jn9106"""
    try:
        print(f"Connecting to AWS RDS...")
        conn = psycopg2.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            database=RDS_DATABASE,
            user=RDS_USERNAME,
            password=RDS_PASSWORD
        )
        cursor = conn.cursor()
        print("✓ Connected successfully!")
        
        # Check if Jan-06 exists
        cursor.execute("SELECT id, username FROM users WHERE username = 'Jan-06'")
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            print(f"Found user 'Jan-06' with ID {user_id}")
            
            # Check if jn9106 already exists
            cursor.execute("SELECT id FROM users WHERE username = 'jn9106'")
            existing = cursor.fetchone()
            
            if existing:
                print("User 'jn9106' already exists. Deleting 'Jan-06'...")
                # Delete Jan-06 since jn9106 exists
                cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
                cursor.execute("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,))
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                print("✓ Deleted duplicate user 'Jan-06'")
            else:
                print("Renaming 'Jan-06' to 'jn9106'...")
                # Update username
                cursor.execute(
                    "UPDATE users SET username = %s WHERE id = %s",
                    ('jn9106', user_id)
                )
                print("✓ Username updated from 'Jan-06' to 'jn9106'")
                
                # Update password to match the correct pattern
                password_hash = bcrypt.hashpw('student@jn9106'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (password_hash, user_id)
                )
                print("✓ Password updated to 'student@jn9106'")
            
            conn.commit()
            print("\n✅ Username fix complete!")
        else:
            print("No 'Jan-06' user found. Checking if 'jn9106' exists...")
            cursor.execute("SELECT username, full_name FROM users WHERE username = 'jn9106'")
            result = cursor.fetchone()
            if result:
                print(f"✓ User 'jn9106' already exists: {result[1]}")
            else:
                print("Creating 'jn9106' user...")
                # Create the user properly
                email = "jn9106@college.edu"
                password_hash = bcrypt.hashpw('student@jn9106'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                ''', ('jn9106', email, password_hash, 'Jacob Nathan', 'student'))
                conn.commit()
                print("✓ Created user 'jn9106'")
        
        # Verify final state
        cursor.execute("SELECT COUNT(*) FROM users WHERE username IN ('Jan-06', 'jn9106')")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT username FROM users WHERE username IN ('Jan-06', 'jn9106')")
        users = cursor.fetchall()
        
        print(f"\nFinal verification:")
        print(f"Found {count} user(s): {[u[0] for u in users]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_username()