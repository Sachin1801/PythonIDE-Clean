#!/usr/bin/env python3
"""
Test login functionality for new students on local server
"""

import requests
import json

def test_student_login(username, password):
    """Test login for a student account"""
    
    login_url = "http://localhost:10086/api/login"
    
    payload = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            login_url, 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ {username}: Login successful")
                return True
            else:
                print(f"❌ {username}: Login failed - {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ {username}: HTTP {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {username}: Connection error - {e}")
        return False

def test_all_new_students():
    """Test all new student accounts"""
    
    new_students = [
        ('sz3991', 'EaS08VX%fcp8', 'Shiwen Zhu'),
        ('eif2018', 'O09R981J337*', 'Ethan Flores'),
        ('ql2499', 'G99R075N924#', 'Nick Li'),
        ('gs4387', 'J65R317F685@', 'Gursehaj Singh'),
        ('cw4973', 'K74R382N830@', 'Caden Wang'),
        ('jy4383', 'C74R761I764@', 'Jessica Yuan')
    ]
    
    print("=== Testing New Student Logins ===")
    print("Server: http://localhost:10086")
    print()
    
    success_count = 0
    total_count = len(new_students)
    
    for username, password, full_name in new_students:
        if test_student_login(username, password):
            success_count += 1
    
    print(f"\n=== Results ===")
    print(f"Successful logins: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("✅ All new student accounts are working!")
        print("\nYou can now:")
        print("1. Visit http://localhost:10086 in your browser")
        print("2. Test login with any of the new student credentials")
        print("3. Verify their directories are accessible in the IDE")
        return True
    else:
        print("❌ Some accounts failed to login. Check the database setup.")
        return False

if __name__ == "__main__":
    try:
        success = test_all_new_students()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        success = False