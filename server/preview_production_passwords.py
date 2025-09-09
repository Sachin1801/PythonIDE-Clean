#!/usr/bin/env python3
"""
Preview what the production passwords will be without creating users
"""
import hashlib

def generate_consistent_password(username, environment="production"):
    """Generate consistent password for a user"""
    secret_seed = "PythonIDE2025SecureClassroom"
    
    hash_input = f"{username}_{secret_seed}_{environment}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()
    
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    password = ""
    
    for i in range(12):
        hex_pair = hash_digest[i*2:(i*2)+2]
        char_index = int(hex_pair, 16) % len(chars)
        password += chars[char_index]
    
    special_chars = "!@#$%^&*"
    special_index = int(hash_digest[-2:], 16) % len(special_chars)
    password = password[:-1] + special_chars[special_index]
    
    return password

# Key admin accounts
admins = ['admin_editor', 'sa9082', 'sl7927', 'et2434', 'test_admin']

print("🔑 AWS PRODUCTION PASSWORDS PREVIEW")
print("="*60)
print("These will be the passwords when you deploy to AWS:\n")

print("ADMIN ACCOUNTS:")
for username in admins:
    password = generate_consistent_password(username, "production")
    print(f"  {username}: {password}")

print(f"\n🚨 MOST IMPORTANT: admin_editor password = {generate_consistent_password('admin_editor', 'production')}")
print("\nThese passwords will be:")
print("1. Shown in console when you run the AWS migration")
print("2. Saved to CSV file in adminData/ on AWS")
print("3. Always the same every time you run the script on AWS")