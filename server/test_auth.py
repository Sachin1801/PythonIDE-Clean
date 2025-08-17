#!/usr/bin/env python3

import requests
import json
import sys

# Test server URL
BASE_URL = "http://localhost:10086"

def test_login():
    """Test login endpoint"""
    print("Testing login...")
    
    # Test with valid credentials
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "sa9082",
        "password": "sa90822024"
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✓ Login successful for sa9082")
            print(f"  Session ID: {data.get('session_id')[:20]}...")
            print(f"  Role: {data.get('role')}")
            print(f"  Full Name: {data.get('full_name')}")
            return data.get('session_id')
        else:
            print(f"✗ Login failed: {data.get('error')}")
            return None
    else:
        print(f"✗ Login request failed with status {response.status_code}")
        return None

def test_invalid_login():
    """Test login with invalid credentials"""
    print("\nTesting invalid login...")
    
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "sa9082",
        "password": "wrongpassword"
    })
    
    if response.status_code == 401:
        print("✓ Invalid login correctly rejected")
    else:
        print(f"✗ Unexpected status code: {response.status_code}")

def test_validate_session(session_id):
    """Test session validation"""
    print("\nTesting session validation...")
    
    response = requests.post(f"{BASE_URL}/api/validate-session", json={
        "session_id": session_id
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✓ Session is valid")
            print(f"  Username: {data.get('username')}")
            print(f"  Role: {data.get('role')}")
        else:
            print(f"✗ Session validation failed: {data.get('error')}")
    else:
        print(f"✗ Session validation request failed with status {response.status_code}")

def test_logout(session_id):
    """Test logout"""
    print("\nTesting logout...")
    
    response = requests.post(f"{BASE_URL}/api/logout", json={
        "session_id": session_id
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✓ Logout successful")
        else:
            print(f"✗ Logout failed: {data.get('error')}")
    else:
        print(f"✗ Logout request failed with status {response.status_code}")

def test_professor_login():
    """Test professor login"""
    print("\nTesting professor login...")
    
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "professor",
        "password": "ChangeMeASAP2024!"
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✓ Professor login successful")
            print(f"  Role: {data.get('role')}")
            print(f"  Full Name: {data.get('full_name')}")
            return data.get('session_id')
    else:
        print(f"✗ Professor login failed with status {response.status_code}")
    
    return None

if __name__ == "__main__":
    print("="*50)
    print("Authentication System Test")
    print("="*50)
    
    print("\n⚠️  Make sure the server is running on port 10086")
    print("Start it with: python server/server.py --port 10086\n")
    
    try:
        # Test student login
        session_id = test_login()
        
        # Test invalid login
        test_invalid_login()
        
        if session_id:
            # Test session validation
            test_validate_session(session_id)
            
            # Test logout
            test_logout(session_id)
            
            # Verify session is invalid after logout
            print("\nVerifying session is invalid after logout...")
            response = requests.post(f"{BASE_URL}/api/validate-session", json={
                "session_id": session_id
            })
            if response.status_code == 401:
                print("✓ Session correctly invalidated after logout")
        
        # Test professor login
        prof_session = test_professor_login()
        
        print("\n" + "="*50)
        print("✓ All authentication tests completed!")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server. Is it running?")
        print("Start the server with: python server/server.py --port 10086")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        sys.exit(1)