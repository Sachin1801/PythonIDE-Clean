#!/usr/bin/env python3
"""
Recreate all user accounts with new persistent storage system
This will clear existing accounts and recreate them with proper file storage
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager
from common.file_storage import file_storage

def recreate_all_accounts():
    """Recreate all accounts with persistent storage"""
    manager = UserManager()
    
    print("=" * 60)
    print("RECREATING ACCOUNTS WITH PERSISTENT STORAGE")
    print("=" * 60)
    print(f"Storage Info: {file_storage.get_storage_info()}")
    print()
    
    # Clear all existing users and sessions
    print("Clearing existing accounts...")
    try:
        manager.db.execute_query("DELETE FROM sessions")
        manager.db.execute_query("DELETE FROM users")
        print("✓ Cleared existing accounts and sessions")
    except Exception as e:
        print(f"⚠ Error clearing accounts: {e}")
    
    # Class roster data from PDF
    users_data = [
        # Admin accounts (professor rights)
        ('sl7927', 'Susan Liao', 'sl7927@nyu.edu', 'professor'),
        ('sa9082', 'Sachin Adlakha', 'sa9082@nyu.edu', 'professor'), 
        ('et2434', 'Ethan Tan', 'et2434@nyu.edu', 'professor'),
        
        # Student accounts
        ('sa8820', 'Syed Ahnaf Ul Ahsan', 'sa8820@nyu.edu', 'student'),
        ('na3649', 'Nicole Akmetov', 'na3649@nyu.edu', 'student'),
        ('ntb5594', 'Nabi Burns-Min', 'ntb5594@nyu.edu', 'student'),
        ('hrb9324', 'Harry Byala', 'hrb9324@nyu.edu', 'student'),
        ('nd2560', 'Nikita Drovin-skiy', 'nd2560@nyu.edu', 'student'),
        ('ag11389', 'Adrian Garcia', 'ag11389@nyu.edu', 'student'),
        ('arg9667', 'Aarav Gupta', 'arg9667@nyu.edu', 'student'),
        ('lh4052', 'Liisa Hambazaza', 'lh4052@nyu.edu', 'student'),
        ('jh9963', 'Justin Hu', 'jh9963@nyu.edu', 'student'),
        ('ch5315', 'Rami Hu', 'ch5315@nyu.edu', 'student'),
        ('wh2717', 'Weijie Huang', 'wh2717@nyu.edu', 'student'),
        ('bsj5539', 'Maybelina J', 'bsj5539@nyu.edu', 'student'),
        ('fk2248', 'Falisha Khan', 'fk2248@nyu.edu', 'student'),
        ('nvk9963', 'Neil Khandelwal', 'nvk9963@nyu.edu', 'student'),
        ('sil9056', 'Simon Levine', 'sil9056@nyu.edu', 'student'),
        ('hl6459', 'Haoru Li', 'hl6459@nyu.edu', 'student'),
        ('zl3894', 'Jenny Li', 'zl3894@nyu.edu', 'student'),
        ('jom2045', 'Janell Magante', 'jom2045@nyu.edu', 'student'),
        ('arm9283', 'Amelia Mappus', 'arm9283@nyu.edu', 'student'),
        ('zm2525', 'Zhou Meng', 'zm2525@nyu.edu', 'student'),
        ('im2420', 'Ishaan Mukherjee', 'im2420@nyu.edu', 'student'),
        ('jn3143', 'Janvi Nagpal', 'jn3143@nyu.edu', 'student'),
        ('jan9106', 'Jacob Nathan', 'jan9106@nyu.edu', 'student'),
        ('djp10030', 'Darius Partovi', 'djp10030@nyu.edu', 'student'),
        ('ap10062', 'Alexandar Pelletier', 'ap10062@nyu.edu', 'student'),
        ('bap9618', 'Benjamin Piquet', 'bap9618@nyu.edu', 'student'),
        ('fp2331', 'Federico Pirelli', 'fp2331@nyu.edu', 'student'),
        ('srp8204', 'Shaina Pollak', 'srp8204@nyu.edu', 'student'),
        ('agr8457', 'Alex Reber', 'agr8457@nyu.edu', 'student'),
        ('shs9941', 'Suzie Sanford', 'shs9941@nyu.edu', 'student'),
        ('as19217', 'Albert Sun', 'as19217@nyu.edu', 'student'),
        ('mat9481', 'Mario Toscano', 'mat9481@nyu.edu', 'student'),
        ('cw4715', 'Chun-Hsiang Wang', 'cw4715@nyu.edu', 'student'),
        ('jw9248', 'Jingyuan Wang', 'jw9248@nyu.edu', 'student'),
        ('sz4766', 'Shengbo Zhang', 'sz4766@nyu.edu', 'student'),
    ]
    
    created_count = 0
    failed_count = 0
    
    print("\nCreating accounts with persistent storage...")
    print("-" * 60)
    
    for username, full_name, email, role in users_data:
        # Set password based on role
        if role == 'professor':
            password = f"Admin@{username}"
        else:
            password = f"student@{username}"
        
        success, msg = manager.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=role
        )
        
        if success:
            created_count += 1
            role_label = "ADMIN" if role == 'professor' else "STUDENT"
            print(f"✓ Created {role_label}: {username} ({full_name})")
        else:
            failed_count += 1
            print(f"✗ Failed to create {username}: {msg}")
    
    print("\n" + "=" * 60)
    print("RECREATION COMPLETE")
    print("=" * 60)
    print(f"Successfully created: {created_count} accounts")
    print(f"Failed: {failed_count} accounts") 
    print(f"Storage location: {file_storage.get_storage_info()['storage_root']}")
    print(f"Storage type: {file_storage.get_storage_info()['type']}")
    
    if failed_count == 0:
        print("✅ All accounts recreated successfully with persistent storage!")
    else:
        print(f"⚠️  {failed_count} accounts failed to create")
    
    return created_count, failed_count

if __name__ == '__main__':
    recreate_all_accounts()