#!/usr/bin/env python3
"""
Script to add sz3991 (Shiwen Zhu) to AWS RDS PostgreSQL database
Run this after pushing local changes to sync the new user to production
"""
import os
import sys

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from auth.user_manager_postgres import UserManager
from common.database import db_manager

def add_sz3991_to_aws_rds():
    """Add sz3991 user to AWS RDS database"""
    
    # User data
    username = 'sz3991'
    full_name = 'Shiwen Zhu'
    email = f'{username}@nyu.edu'
    password = 'EaS08VX%fcp8'  # Same password as generated locally
    role = 'student'
    
    print("="*60)
    print("ADDING SZ3991 TO AWS RDS DATABASE")
    print("="*60)
    print(f"Username: {username}")
    print(f"Full Name: {full_name}")
    print(f"Email: {email}")
    print(f"Role: {role}")
    print(f"Environment: {'AWS RDS' if 'amazonaws.com' in os.environ.get('DATABASE_URL', '') else 'Local'}")
    
    # Verify we're connected to AWS RDS
    db_url = os.environ.get('DATABASE_URL', '')
    if 'amazonaws.com' not in db_url:
        print("\n⚠️  WARNING: Not connected to AWS RDS!")
        print(f"Current DATABASE_URL: {db_url[:50]}...")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return False
    
    # Check if user already exists
    try:
        existing_users = db_manager.execute_query(
            "SELECT username FROM users WHERE username = %s", 
            (username,)
        )
        
        if existing_users:
            print(f"\n✓ User {username} already exists in database")
            return True
            
    except Exception as e:
        print(f"\n✗ Error checking existing users: {e}")
        return False
    
    # Create the user
    try:
        manager = UserManager()
        
        print(f"\n📝 Creating user {username}...")
        success, msg = manager.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=role
        )
        
        if success:
            print(f"✓ Successfully created user: {username}")
            print(f"  - Full Name: {full_name}")
            print(f"  - Email: {email}")
            print(f"  - Role: {role}")
            
            # Verify user was created
            verify_user = db_manager.execute_query(
                "SELECT username, full_name, role, created_at FROM users WHERE username = %s",
                (username,)
            )
            
            if verify_user:
                user = verify_user[0]
                print(f"  - Verified in DB: {user['created_at']}")
                
                # Count total users
                total_count = db_manager.execute_query("SELECT COUNT(*) as count FROM users")
                print(f"  - Total users now: {total_count[0]['count']}")
                
                return True
            else:
                print("✗ User creation reported success but user not found in database")
                return False
                
        else:
            print(f"✗ Failed to create user: {msg}")
            return False
            
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        return False

def verify_aws_environment():
    """Verify we're running in AWS environment with correct settings"""
    print("\n" + "="*60)
    print("VERIFYING AWS ENVIRONMENT")
    print("="*60)
    
    required_vars = [
        'DATABASE_URL',
        'IDE_SECRET_KEY', 
        'IDE_DATA_PATH'
    ]
    
    all_present = True
    for var in required_vars:
        value = os.environ.get(var, '')
        if value:
            if var == 'DATABASE_URL':
                # Show partial URL for security
                if 'amazonaws.com' in value:
                    print(f"✓ {var}: ...{value[-40:]}")
                else:
                    print(f"⚠️  {var}: Not AWS RDS (probably local)")
            elif var == 'IDE_SECRET_KEY':
                print(f"✓ {var}: {'*' * 20}...")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: NOT SET")
            all_present = False
    
    return all_present

if __name__ == '__main__':
    print("AWS RDS User Addition Script")
    print("Adding user: sz3991 (Shiwen Zhu)")
    
    # Verify environment
    env_ok = verify_aws_environment()
    
    if not env_ok:
        print("\n⚠️  Environment verification failed. Some required variables are missing.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(1)
    
    # Add user to RDS
    success = add_sz3991_to_aws_rds()
    
    if success:
        print(f"\n✅ SUCCESS: User sz3991 added to AWS RDS")
        print("\n📋 NEXT STEPS:")
        print("1. Run the EFS directory creation script")
        print("2. Test login with sz3991 credentials on AWS environment")
        print("3. Verify the user can access their Local/sz3991/ directory")
        
        print(f"\n🔑 LOGIN CREDENTIALS for sz3991:")
        print(f"Username: sz3991")
        print(f"Password: EaS08VX%fcp8")
        
    else:
        print(f"\n❌ FAILED: Could not add user sz3991 to AWS RDS")
        sys.exit(1)