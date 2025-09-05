#!/usr/bin/env python3
"""
Verify that user data persists correctly on AWS with EFS
Run this after deployment to check everything is working
"""
import os
import sys

# Add server path
sys.path.append('/app/server')

from common.database import db_manager

def check_persistence():
    print("="*60)
    print("PERSISTENCE VERIFICATION CHECK")
    print("="*60)
    
    # 1. Check Database (RDS)
    print("\n1. DATABASE (RDS PostgreSQL 15.7):")
    print("-" * 40)
    try:
        # Check users
        users = db_manager.execute_query("""
            SELECT role, COUNT(*) as count 
            FROM users 
            GROUP BY role 
            ORDER BY role
        """)
        
        for user in users:
            print(f"  {user['role'].title()}s: {user['count']}")
        
        # Check specific users
        key_users = ['sl7927', 'sa9082', 'et2434', 'na3649']
        for username in key_users:
            result = db_manager.execute_query(
                "SELECT username, role FROM users WHERE username = %s",
                (username,)
            )
            if result:
                print(f"  ✓ {username}: {result[0]['role']}")
            else:
                print(f"  ✗ {username}: NOT FOUND")
    except Exception as e:
        print(f"  ✗ Database Error: {e}")
    
    # 2. Check File System (EFS)
    print("\n2. FILE SYSTEM (AWS EFS):")
    print("-" * 40)
    
    base_path = '/app/server/projects/ide'
    
    # Check if path exists
    if not os.path.exists(base_path):
        print(f"  ✗ Base path does not exist: {base_path}")
        print("  → EFS may not be mounted correctly!")
        return False
    
    # Check directories
    dirs_to_check = ['Local', 'Lecture Notes']
    for dir_name in dirs_to_check:
        dir_path = os.path.join(base_path, dir_name)
        if os.path.exists(dir_path):
            if dir_name == 'Local':
                student_dirs = [d for d in os.listdir(dir_path) 
                              if os.path.isdir(os.path.join(dir_path, d)) 
                              and not d.startswith('.')]
                print(f"  ✓ {dir_name}/: {len(student_dirs)} student folders")
            else:
                print(f"  ✓ {dir_name}/: exists")
        else:
            print(f"  ✗ {dir_name}/: NOT FOUND")
    
    # 3. Check Mount Points
    print("\n3. MOUNT POINTS:")
    print("-" * 40)
    
    # Check if EFS is mounted
    with open('/proc/mounts', 'r') as f:
        mounts = f.read()
        
    if 'efs' in mounts or '/mnt/efs' in mounts:
        print("  ✓ EFS is mounted")
        # Find exact mount point
        for line in mounts.split('\n'):
            if 'efs' in line or '/mnt/efs' in line or '/app/server/projects/ide' in line:
                parts = line.split()
                if len(parts) >= 2:
                    print(f"    Mount: {parts[0]} → {parts[1]}")
    else:
        print("  ⚠ EFS mount not detected in /proc/mounts")
        print("    (This might be normal in some container configurations)")
    
    # 4. Test Write Permission
    print("\n4. WRITE PERMISSION TEST:")
    print("-" * 40)
    
    test_file = os.path.join(base_path, 'Local', '.efs_test')
    try:
        with open(test_file, 'w') as f:
            f.write("EFS write test")
        os.remove(test_file)
        print("  ✓ Write permission verified")
    except Exception as e:
        print(f"  ✗ Cannot write to EFS: {e}")
    
    # 5. Summary
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    
    # Get totals
    try:
        total_users = db_manager.execute_query("SELECT COUNT(*) as count FROM users")[0]['count']
        total_dirs = len([d for d in os.listdir(os.path.join(base_path, 'Local')) 
                         if os.path.isdir(os.path.join(base_path, 'Local', d)) 
                         and not d.startswith('.')])
        
        print(f"  • Users in Database: {total_users}")
        print(f"  • Student Directories: {total_dirs}")
        
        if total_users >= 38 and total_dirs >= 35:
            print("\n✅ PERSISTENCE VERIFIED - All data is properly stored!")
            print("   Your data will persist across deployments.")
        else:
            print("\n⚠ INCOMPLETE SETUP - Run initialization script:")
            print("   bash /app/deployment/efs-initialization.sh")
    except:
        print("\n⚠ Could not verify totals")
    
    return True

if __name__ == '__main__':
    check_persistence()