#!/usr/bin/env python3
import requests
import json

# ALB URL
BASE_URL = "http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com"

def reset_admin():
    """Use the setup endpoint to create admin user"""
    try:
        # Call setup endpoint
        response = requests.get(f"{BASE_URL}/api/setup")
        print(f"Setup response: {response.text}")
        
        # Try to login with default admin
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Default admin account created!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("\n⚠️ Setup may have failed. Trying alternative...")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_admin()