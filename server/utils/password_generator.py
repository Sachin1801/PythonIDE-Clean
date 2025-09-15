#!/usr/bin/env python3
"""
Secure random password generator utility
"""
import secrets
import string
import csv
import os
from datetime import datetime

class PasswordGenerator:
    def __init__(self):
        # Character sets for password generation
        self.letters = string.ascii_letters  # a-z, A-Z
        self.digits = string.digits          # 0-9
        self.symbols = "!@#$%^&*"           # Safe symbols (avoiding quotes, backslashes)
        self.all_chars = self.letters + self.digits + self.symbols
    
    def generate_password(self, length=12, ensure_complexity=True):
        """
        Generate a cryptographically secure random password
        
        Args:
            length (int): Password length (default: 12)
            ensure_complexity (bool): Ensure at least one from each character set
            
        Returns:
            str: Random password
        """
        if ensure_complexity and length < 4:
            raise ValueError("Password length must be at least 4 for complexity requirements")
        
        if ensure_complexity:
            # Ensure at least one character from each set
            password = [
                secrets.choice(string.ascii_lowercase),
                secrets.choice(string.ascii_uppercase),
                secrets.choice(self.digits),
                secrets.choice(self.symbols)
            ]
            
            # Fill remaining length with random characters
            for _ in range(length - 4):
                password.append(secrets.choice(self.all_chars))
            
            # Shuffle the password to avoid predictable patterns
            secrets.SystemRandom().shuffle(password)
            return ''.join(password)
        else:
            # Simple random password
            return ''.join(secrets.choice(self.all_chars) for _ in range(length))
    
    def generate_passwords_for_users(self, users_list, length=12):
        """
        Generate passwords for a list of users
        
        Args:
            users_list (list): List of user dictionaries with 'username' and 'full_name'
            length (int): Password length
            
        Returns:
            list: List of users with passwords added
        """
        users_with_passwords = []
        
        for user in users_list:
            user_copy = user.copy()
            user_copy['password'] = self.generate_password(length)
            user_copy['password_generated_at'] = datetime.now().isoformat()
            users_with_passwords.append(user_copy)
        
        return users_with_passwords
    
    def export_to_csv(self, users_with_passwords, filename_prefix="user_credentials"):
        """
        Export user credentials to CSV file
        
        Args:
            users_with_passwords (list): List of users with passwords
            filename_prefix (str): Prefix for the CSV filename
            
        Returns:
            str: Path to the created CSV file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.csv"
        
        # Create adminData directory if it doesn't exist
        admin_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'adminData'
        )
        os.makedirs(admin_data_dir, exist_ok=True)
        
        filepath = os.path.join(admin_data_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Username', 'Full Name', 'Password', 'Role', 'Email', 'Generated At']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for user in users_with_passwords:
                writer.writerow({
                    'Username': user['username'],
                    'Full Name': user['full_name'],
                    'Password': user['password'],
                    'Role': user.get('role', 'student'),
                    'Email': user.get('email', f"{user['username']}@nyu.edu"),
                    'Generated At': user['password_generated_at']
                })
        
        return filepath
    
    def load_users_from_csv(self, csv_path):
        """
        Load existing users from CSV file (for regenerating passwords)
        
        Args:
            csv_path (str): Path to existing CSV file
            
        Returns:
            list: List of user dictionaries
        """
        users = []
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                users.append({
                    'username': row['Username'].strip(),
                    'full_name': row['Full Name'].strip(),
                    'role': row.get('Role', 'student').strip(),
                    'email': row.get('Email', f"{row['Username'].strip()}@nyu.edu").strip()
                })
        
        return users

def main():
    """Command line interface for password generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate secure passwords for users')
    parser.add_argument('--length', type=int, default=12, 
                        help='Password length (default: 12)')
    parser.add_argument('--count', type=int, default=1,
                        help='Number of passwords to generate (default: 1)')
    parser.add_argument('--csv', type=str,
                        help='CSV file to load users from and regenerate passwords')
    parser.add_argument('--test', action='store_true',
                        help='Generate test passwords and show examples')
    
    args = parser.parse_args()
    
    generator = PasswordGenerator()
    
    if args.test:
        print("Password Generator Test")
        print("=" * 50)
        for i in range(5):
            password = generator.generate_password(args.length)
            print(f"Password {i+1}: {password}")
        return
    
    if args.csv:
        if not os.path.exists(args.csv):
            print(f"CSV file not found: {args.csv}")
            return
        
        print(f"Loading users from: {args.csv}")
        users = generator.load_users_from_csv(args.csv)
        print(f"Loaded {len(users)} users")
        
        # Generate new passwords
        users_with_passwords = generator.generate_passwords_for_users(users, args.length)
        
        # Export to new CSV
        output_file = generator.export_to_csv(users_with_passwords, "regenerated_credentials")
        print(f"New credentials exported to: {output_file}")
        
        # Show first few examples
        print("\nFirst 3 users (example):")
        for user in users_with_passwords[:3]:
            print(f"  {user['username']}: {user['password']}")
    
    else:
        print(f"Generating {args.count} random passwords (length: {args.length}):")
        for i in range(args.count):
            password = generator.generate_password(args.length)
            print(f"  {i+1}: {password}")

if __name__ == '__main__':
    main()