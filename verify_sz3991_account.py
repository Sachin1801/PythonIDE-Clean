#!/usr/bin/env python3
"""
Script to verify sz3991 account exists and works in both local and AWS environments
"""
import os
import sys

# Add server directory to path - server is in same directory as this script
current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.join(current_dir, 'server')
if os.path.exists(server_dir):
    sys.path.append(server_dir)
else:
    # Try different patterns
    for pattern in ['server', '.', './server']:
        if os.path.exists(pattern):
            sys.path.append(pattern)
            break

def verify_environment():
    """Detect and verify current environment"""
    print("="*60)
    print("ENVIRONMENT DETECTION")
    print("="*60)
    
    db_url = os.environ.get('DATABASE_URL', '')
    ide_data_path = os.environ.get('IDE_DATA_PATH', '')
    
    if 'amazonaws.com' in db_url:
        env_type = 'AWS Production'
        expected_data_path = '/mnt/efs/pythonide-data'
    elif db_url and 'localhost' not in db_url:
        env_type = 'Remote Database'
        expected_data_path = ide_data_path or '/tmp/pythonide-data'
    else:
        env_type = 'Local Development'
        expected_data_path = ide_data_path or '/tmp/pythonide-data'
    
    print(f"Environment Type: {env_type}")
    print(f"Database URL: {'...' + db_url[-40:] if db_url else 'NOT SET'}")
    print(f"IDE Data Path: {ide_data_path or 'NOT SET'}")
    print(f"Expected Data Path: {expected_data_path}")
    
    return env_type, expected_data_path

def verify_database_user():
    """Verify sz3991 user exists in database"""
    print("\n" + "="*60)
    print("DATABASE VERIFICATION")
    print("="*60)
    
    try:
        from common.database import db_manager
        
        # Check if user exists
        result = db_manager.execute_query(
            "SELECT id, username, full_name, email, role, created_at, last_login FROM users WHERE username = %s",
            ('sz3991',)
        )
        
        if result:
            user = result[0]
            print("✓ User sz3991 found in database:")
            print(f"  - ID: {user['id']}")
            print(f"  - Username: {user['username']}")
            print(f"  - Full Name: {user['full_name']}")
            print(f"  - Email: {user['email']}")
            print(f"  - Role: {user['role']}")
            print(f"  - Created: {user['created_at']}")
            print(f"  - Last Login: {user['last_login'] or 'Never'}")
            return True
        else:
            print("✗ User sz3991 NOT found in database")
            return False
            
    except Exception as e:
        print(f"✗ Database verification failed: {e}")
        return False

def verify_user_directory(expected_data_path):
    """Verify sz3991 directory exists and is accessible"""
    print("\n" + "="*60)
    print("DIRECTORY VERIFICATION")
    print("="*60)
    
    # Possible Local directory paths
    possible_paths = [
        os.path.join(expected_data_path, 'ide', 'Local'),
        '/mnt/efs/pythonide-data/ide/Local',
        '/tmp/pythonide-data/ide/Local',
        'server/projects/ide/Local'
    ]
    
    local_base = None
    for path in possible_paths:
        if os.path.exists(path):
            local_base = path
            print(f"✓ Found Local directory: {path}")
            break
    
    if not local_base:
        print("✗ Could not find Local directory base")
        print("Tried paths:")
        for path in possible_paths:
            print(f"  - {path}")
        return False
    
    # Check sz3991 directory
    user_dir = os.path.join(local_base, 'sz3991')
    
    if os.path.exists(user_dir):
        print(f"✓ User directory exists: {user_dir}")
        
        # Check permissions
        try:
            stat_info = os.stat(user_dir)
            permissions = oct(stat_info.st_mode)[-3:]
            print(f"  - Permissions: {permissions}")
            
            # Check if writable
            test_file = os.path.join(user_dir, '.test_write')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print("  - Write access: ✓")
            except:
                print("  - Write access: ✗")
            
            # List contents
            contents = os.listdir(user_dir)
            if contents:
                print(f"  - Contents: {contents}")
            else:
                print("  - Directory is empty")
                
        except Exception as e:
            print(f"  - Permission check failed: {e}")
        
        return True
    else:
        print(f"✗ User directory does not exist: {user_dir}")
        return False

def test_authentication():
    """Test sz3991 authentication"""
    print("\n" + "="*60)
    print("AUTHENTICATION TEST")
    print("="*60)
    
    try:
        from auth.user_manager_postgres import UserManager
        
        manager = UserManager()
        username = 'sz3991'
        password = 'EaS08VX%fcp8'
        
        print(f"Testing authentication for {username}...")
        
        auth_result, error_msg = manager.authenticate(username, password)
        
        if auth_result:
            print("✓ Authentication successful!")
            print(f"  - User ID: {auth_result['user_id']}")
            print(f"  - Username: {auth_result['username']}")
            print(f"  - Role: {auth_result['role']}")
            print(f"  - Full Name: {auth_result['full_name']}")
            print(f"  - Token: {auth_result['token'][:20]}...")
            print(f"  - Expires: {auth_result['expires_at']}")
            
            # Test session validation
            session = manager.validate_session(auth_result['token'])
            if session:
                print("✓ Session validation successful")
                
                # Logout to clean up
                manager.logout(auth_result['token'])
                print("✓ Logout successful")
                
            return True
        else:
            print(f"✗ Authentication failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"✗ Authentication test failed: {e}")
        return False

def generate_summary_report():
    """Generate a summary report"""
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    
    env_type, expected_data_path = verify_environment()
    db_ok = verify_database_user()
    dir_ok = verify_user_directory(expected_data_path)
    auth_ok = test_authentication()
    
    print(f"\nVerification Results for sz3991:")
    print(f"  Database User: {'✓' if db_ok else '✗'}")
    print(f"  User Directory: {'✓' if dir_ok else '✗'}")
    print(f"  Authentication: {'✓' if auth_ok else '✗'}")
    
    all_ok = db_ok and dir_ok and auth_ok
    
    if all_ok:
        print(f"\n✅ ALL CHECKS PASSED")
        print(f"sz3991 account is ready for use in {env_type}")
        
        print(f"\n🔑 LOGIN CREDENTIALS:")
        print(f"Username: sz3991")
        print(f"Full Name: Shiwen Zhu")
        print(f"Password: EaS08VX%fcp8")
        print(f"Role: student")
        
        print(f"\n📋 ACCOUNT CAPABILITIES:")
        print(f"- Can log in to the IDE")
        print(f"- Has access to Local/sz3991/ directory")
        print(f"- Can create, edit, and run Python files")
        print(f"- Can use the hybrid REPL system")
        print(f"- Student-level permissions (cannot see other students' files)")
        
    else:
        print(f"\n❌ SOME CHECKS FAILED")
        print(f"sz3991 account needs attention before use")
        
        if not db_ok:
            print("  → Run add_sz3991_to_aws_rds.py to create database user")
        if not dir_ok:
            print("  → Run create_sz3991_efs_directory.py to create user directory")
        if not auth_ok:
            print("  → Check password and database connectivity")
    
    return all_ok

if __name__ == '__main__':
    print("PythonIDE Account Verification Script")
    print("Verifying account: sz3991 (Shiwen Zhu)")
    
    success = generate_summary_report()
    
    if not success:
        sys.exit(1)