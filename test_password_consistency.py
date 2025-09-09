#!/usr/bin/env python3
"""
Simple test for password consistency without database dependencies
"""
import hashlib

def generate_consistent_password(username, environment="production"):
    """
    Generate consistent password for a user based on username
    This ensures the same user gets the same password in both local and AWS
    """
    secret_seed = "PythonIDE2025SecureClassroom"
    
    # Create a hash based on username + seed + environment
    hash_input = f"{username}_{secret_seed}_{environment}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()
    
    # Convert hash to a readable password format (12 characters)
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    password = ""
    
    for i in range(12):
        hex_pair = hash_digest[i*2:(i*2)+2]
        char_index = int(hex_pair, 16) % len(chars)
        password += chars[char_index]
    
    # Ensure at least one special character for complexity
    special_chars = "!@#$%^&*"
    special_index = int(hash_digest[-2:], 16) % len(special_chars)
    
    # Replace last character with special character
    password = password[:-1] + special_chars[special_index]
    
    return password

def test_password_consistency():
    """Test that consistent password generation works"""
    print("TESTING PASSWORD CONSISTENCY")
    print("="*60)
    
    test_users = ['sa9082', 'admin_editor', 'sl7927', 'et2434', 'jd1234', 'ab5678']
    
    print("Testing that same environment produces same passwords:")
    for username in test_users:
        pass1 = generate_consistent_password(username, "production")
        pass2 = generate_consistent_password(username, "production")
        
        print(f"  {username}: {pass1} | Same: {'✓' if pass1 == pass2 else '✗'}")
    
    print("\nTesting environment differences:")
    for username in test_users[:3]:  # Just first 3 for brevity
        local_password = generate_consistent_password(username, "local")
        prod_password = generate_consistent_password(username, "production")
        
        print(f"  {username}:")
        print(f"    Local:      {local_password}")
        print(f"    Production: {prod_password}")
        print(f"    Different:  {'✓' if local_password != prod_password else '✗'}")

if __name__ == '__main__':
    test_password_consistency()