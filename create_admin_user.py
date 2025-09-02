#!/usr/bin/env python3
import os
import psycopg2
import bcrypt
from datetime import datetime

# Database connection details
DATABASE_URL = "postgresql://pythonide_admin:Sachinadlakha9082@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide"

def create_admin_user(username, password):
    """Create an admin user in the database"""
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing user's password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                UPDATE users 
                SET password = %s, is_admin = true, updated_at = %s
                WHERE username = %s
            """, (hashed_password, datetime.now(), username))
            print(f"✅ Updated existing user '{username}' with new password and admin privileges")
        else:
            # Create new user
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                INSERT INTO users (username, password, is_admin, created_at, updated_at)
                VALUES (%s, %s, true, %s, %s)
            """, (username, hashed_password, datetime.now(), datetime.now()))
            print(f"✅ Created new admin user '{username}'")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Creating/updating admin users...")
    
    # Create admin accounts
    admin_accounts = [
        ("sa9082", "Admin@sa9082"),
        ("sl7927", "Admin@sl7927"),
        ("et2434", "Admin@et2434"),
    ]
    
    for username, password in admin_accounts:
        create_admin_user(username, password)
    
    print("\n✅ Admin accounts ready!")
    print("\nYou can now login with:")
    for username, password in admin_accounts:
        print(f"  Username: {username} | Password: {password}")