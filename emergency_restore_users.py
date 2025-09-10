#!/usr/bin/env python3
"""
Emergency script to restore users directly on AWS without CSV file
"""
import os
import sys
import bcrypt
import hashlib
import string
import secrets

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server'))

from common.database import db_manager
from common.file_storage import file_storage

def generate_consistent_password(username, environment="production"):
    """Generate deterministic password based on username and environment"""
    secret_seed = "PythonIDE2025SecureClassroom"
    hash_input = f"{username}_{secret_seed}_{environment}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()
    
    # Convert hash to readable password format
    chars = []
    chars.append(hash_digest[0].upper() if hash_digest[0].isalpha() else 'X')
    chars.append(hash_digest[1:3])
    chars.append(hash_digest[3].upper() if hash_digest[3].isalpha() else 'R')
    chars.append(str(sum(ord(c) for c in hash_digest[:4]) % 10))
    chars.append(hash_digest[4:6])
    chars.append(hash_digest[6].upper() if hash_digest[6].isalpha() else 'Q')
    chars.append(hash_digest[7:9])
    chars.append(str(sum(ord(c) for c in hash_digest[6:10]) % 10))
    
    symbols = ['!', '@', '#', '$', '%', '&', '*']
    symbol_index = sum(ord(c) for c in hash_digest[:8]) % len(symbols)
    chars.append(symbols[symbol_index])
    
    return ''.join(str(c) for c in chars)

def create_user(username, password, role='student'):
    """Create a user with hashed password"""
    try:
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Generate email
        email = f"{username}@college.edu"
        
        # Insert user into database
        query = """
        INSERT INTO users (username, email, password_hash, role) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (username) DO UPDATE 
        SET password_hash = EXCLUDED.password_hash, role = EXCLUDED.role, email = EXCLUDED.email
        """
        db_manager.execute_query(query, (username, email, password_hash.decode('utf-8'), role))
        
        # Directory creation handled by AWS container
        # user_dir = file_storage.ensure_user_directory(username)
        
        return True
    except Exception as e:
        print(f"Error creating user {username}: {e}")
        return False

def main():
    print("=" * 60)
    print("EMERGENCY USER RESTORATION")
    print("=" * 60)
    
    # Hardcoded user list since CSV is missing
    users = [
        # Admin accounts
        ('admin_editor', 'XuR0ibQqhw6#', 'professor'),
        ('sa9082', 'pXzwjLIYE20*', 'professor'),
        ('sl7927', '4qPg1cmJkUa!', 'professor'),
        ('et2434', 'evaTQRwfyhC*', 'professor'),
        
        # Test accounts
        ('admin_viewer', 'AdminView2025!', 'student'),
        ('test_student', 'TestStudent2025!', 'student'),
        ('test_admin', 'TestAdmin2025!', 'professor'),
        
        # Student accounts
        ('ag11389', 'X4fD1caEa39*', 'student'),
        ('agr8457', 'Aab907Q4b4*', 'student'),
        ('ap10062', 'X97807Qc97#', 'student'),
        ('arg9667', 'B0dC9d3Fc04&', 'student'),
        ('arm9283', 'Xd9303Q7a9&', 'student'),
        ('as19217', 'BebD848Ed89!', 'student'),
        ('bap9618', 'Xc2F909Dfc5&', 'student'),
        ('bsj5539', 'B01E5afBe07*', 'student'),
        ('ch5315', 'X96B5d0Q965%', 'student'),
        ('dl8926', 'Fc0Q054E2c4*', 'student'),
        ('dl9362', 'A23B2b5E829@', 'student'),
        ('ecs8863', 'Dba805B8a5!', 'student'),
        ('ee7513', 'F52E8a2Cb23!', 'student'),
        ('hr6456', 'D88F71bEa80@', 'student'),
        ('jd7852', 'Xb7F500A4b9$', 'student'),
        ('lp7436', 'Be4D8e4B5e2&', 'student'),
        ('mm17329', 'Da3D5edFe37#', 'student'),
        ('nyk5356', 'F78F0ebE5f2#', 'student'),
        ('pm7841', 'C47Q638Cc49*', 'student'),
        ('pp8019', 'Eb4A066A2b5@', 'student'),
        ('ps10497', 'C02E0daF406*', 'student'),
        ('pvd5683', 'Ab3806Be37!', 'student'),
        ('rm11092', 'X26D0fbQe25&', 'student'),
        ('rmm9894', 'Xb6F0e8Ce76@', 'student'),
        ('sg12493', 'X51803Da52&', 'student'),
        ('sr10641', 'Ab0R4c7Ed04$', 'student'),
        ('ss18846', 'C56Q855D951!', 'student'),
        ('ss19618', 'C16F5f5Qd14&', 'student'),
        ('sw10013', 'Be6D7ceEf64$', 'student'),
        ('sz4766', 'X88B923Cab1%', 'student'),
        ('vn5684', 'A29D3e9Ae20!', 'student'),
        ('vt5675', 'A43D1c1D141@', 'student'),
        ('xl6213', 'X59841F653!', 'student'),
        ('xs7043', 'E5cBe09Xed0*', 'student'),
        ('zm2525', 'C48E8beAd47&', 'student'),
    ]
    
    success_count = 0
    for username, password, role in users:
        if create_user(username, password, role):
            print(f"✓ Created {role}: {username}")
            success_count += 1
        else:
            print(f"✗ Failed to create: {username}")
    
    print("\n" + "=" * 60)
    print(f"✅ Restored {success_count}/{len(users)} users")
    print("\nTest with:")
    print("  admin_editor / XuR0ibQqhw6#")
    print("  URL: http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com")
    print("=" * 60)

if __name__ == "__main__":
    main()