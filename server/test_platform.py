#!/usr/bin/env python3

"""
Comprehensive test suite for the multi-user Python IDE platform
Run this to verify all components are working correctly
"""

import requests
import json
import websocket
import time
import sys
import threading
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:10086"
WS_URL = "ws://localhost:10086/ws"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}Testing: {test_name}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")

# ==============================================================================
# 1. AUTHENTICATION TESTS
# ==============================================================================

def test_authentication():
    print_test_header("Authentication System")
    
    # Test student login
    print("\n1. Testing student login...")
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "sa9082",
        "password": "sa90822024"
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print_success(f"Student login successful")
            print_info(f"  Username: {data.get('username')}")
            print_info(f"  Role: {data.get('role')}")
            print_info(f"  Session: {data.get('session_id')[:20]}...")
            student_session = data.get('session_id')
        else:
            print_error("Student login failed")
            return None, None
    else:
        print_error(f"Login request failed: {response.status_code}")
        return None, None
    
    # Test professor login
    print("\n2. Testing professor login...")
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "professor",
        "password": "ChangeMeASAP2024!"
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print_success(f"Professor login successful")
            print_info(f"  Username: {data.get('username')}")
            print_info(f"  Role: {data.get('role')}")
            professor_session = data.get('session_id')
        else:
            print_error("Professor login failed")
            return student_session, None
    else:
        print_error(f"Login request failed: {response.status_code}")
        return student_session, None
    
    # Test invalid login
    print("\n3. Testing invalid login...")
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "sa9082",
        "password": "wrongpassword"
    })
    
    if response.status_code == 401:
        print_success("Invalid login correctly rejected")
    else:
        print_error(f"Invalid login not rejected properly: {response.status_code}")
    
    # Test session validation
    print("\n4. Testing session validation...")
    response = requests.post(f"{BASE_URL}/api/validate-session", json={
        "session_id": student_session
    })
    
    if response.status_code == 200:
        print_success("Session validation successful")
    else:
        print_error("Session validation failed")
    
    return student_session, professor_session

# ==============================================================================
# 2. WEBSOCKET CONNECTION TESTS
# ==============================================================================

def test_websocket_auth(session_id):
    print_test_header("WebSocket Authentication")
    
    print("\n1. Testing WebSocket connection without auth...")
    try:
        ws = websocket.create_connection(WS_URL)
        response = ws.recv()
        data = json.loads(response)
        
        if data.get('type') == 'auth_required':
            print_success("WebSocket requires authentication")
        else:
            print_error("WebSocket didn't request authentication")
        
        ws.close()
    except Exception as e:
        print_error(f"WebSocket connection failed: {e}")
        return False
    
    print("\n2. Testing WebSocket with valid session...")
    try:
        ws = websocket.create_connection(WS_URL)
        
        # Wait for auth request
        ws.recv()
        
        # Send authentication
        ws.send(json.dumps({
            "cmd": "authenticate",
            "session_id": session_id
        }))
        
        # Check response
        response = ws.recv()
        data = json.loads(response)
        
        if data.get('type') == 'auth_success':
            print_success("WebSocket authentication successful")
            print_info(f"  Authenticated as: {data.get('username')}")
            print_info(f"  Role: {data.get('role')}")
            return ws
        else:
            print_error("WebSocket authentication failed")
            ws.close()
            return None
            
    except Exception as e:
        print_error(f"WebSocket test failed: {e}")
        return None

# ==============================================================================
# 3. FILE OPERATION TESTS
# ==============================================================================

def test_file_operations(ws, username="sa9082"):
    print_test_header("File Operations")
    
    # Test saving a file
    print("\n1. Testing file save...")
    ws.send(json.dumps({
        "cmd": "save_file",
        "path": f"Local/{username}/test_file.py",
        "content": "print('Hello from test!')"
    }))
    
    response = json.loads(ws.recv())
    if response.get('success'):
        print_success("File saved successfully")
    else:
        print_error(f"File save failed: {response.get('error')}")
    
    # Test reading a file
    print("\n2. Testing file read...")
    ws.send(json.dumps({
        "cmd": "get_file",
        "path": f"Local/{username}/test_file.py"
    }))
    
    response = json.loads(ws.recv())
    if response.get('success'):
        print_success("File read successfully")
        print_info(f"  Content: {response.get('content')[:50]}...")
    else:
        print_error(f"File read failed: {response.get('error')}")
    
    # Test listing directory
    print("\n3. Testing directory listing...")
    ws.send(json.dumps({
        "cmd": "list_directory",
        "path": f"Local/{username}"
    }))
    
    response = json.loads(ws.recv())
    if response.get('success'):
        print_success("Directory listed successfully")
        files = response.get('files', [])
        dirs = response.get('directories', [])
        print_info(f"  Files: {len(files)}")
        print_info(f"  Directories: {len(dirs)}")
        for f in files[:3]:
            print_info(f"    - {f.get('name')}")
    else:
        print_error(f"Directory listing failed: {response.get('error')}")
    
    # Test creating directory
    print("\n4. Testing directory creation...")
    ws.send(json.dumps({
        "cmd": "create_directory",
        "path": f"Local/{username}/new_folder"
    }))
    
    response = json.loads(ws.recv())
    if response.get('success'):
        print_success("Directory created successfully")
    else:
        print_error(f"Directory creation failed: {response.get('error')}")

# ==============================================================================
# 4. PERMISSION TESTS
# ==============================================================================

def test_permissions(student_ws, professor_ws):
    print_test_header("Permission System")
    
    # Test student trying to access another student's files
    print("\n1. Testing student accessing another student's files...")
    student_ws.send(json.dumps({
        "cmd": "get_file",
        "path": "Local/jd1234/welcome.py"
    }))
    
    response = json.loads(student_ws.recv())
    if not response.get('success'):
        print_success("Student correctly denied access to another student's files")
    else:
        print_error("SECURITY ISSUE: Student accessed another student's files!")
    
    # Test student accessing lecture notes (read-only)
    print("\n2. Testing student accessing lecture notes...")
    student_ws.send(json.dumps({
        "cmd": "list_directory",
        "path": "Lecture Notes"
    }))
    
    response = json.loads(student_ws.recv())
    if response.get('success'):
        print_success("Student can read lecture notes")
    else:
        print_error("Student cannot access lecture notes")
    
    # Test professor accessing student files
    print("\n3. Testing professor accessing student files...")
    professor_ws.send(json.dumps({
        "cmd": "list_directory",
        "path": "Local/sa9082"
    }))
    
    response = json.loads(professor_ws.recv())
    if response.get('success'):
        print_success("Professor can access student files")
    else:
        print_error("Professor cannot access student files")
    
    # Test directory traversal protection
    print("\n4. Testing directory traversal protection...")
    student_ws.send(json.dumps({
        "cmd": "get_file",
        "path": "../../../etc/passwd"
    }))
    
    response = json.loads(student_ws.recv())
    if not response.get('success'):
        print_success("Directory traversal correctly blocked")
    else:
        print_error("SECURITY ISSUE: Directory traversal not blocked!")

# ==============================================================================
# 5. LOAD TEST
# ==============================================================================

def simulate_user(user_id, results):
    """Simulate a single user session"""
    try:
        # Login
        response = requests.post(f"{BASE_URL}/api/login", json={
            "username": f"student{user_id:03d}",
            "password": f"student{user_id:03d}2024"
        })
        
        if response.status_code != 200:
            results[user_id] = "Login failed"
            return
        
        session_id = response.json().get('session_id')
        
        # Connect WebSocket
        ws = websocket.create_connection(WS_URL)
        ws.recv()  # Auth request
        
        ws.send(json.dumps({
            "cmd": "authenticate",
            "session_id": session_id
        }))
        
        auth_response = json.loads(ws.recv())
        if auth_response.get('type') != 'auth_success':
            results[user_id] = "WebSocket auth failed"
            return
        
        # Perform some operations
        for i in range(3):
            ws.send(json.dumps({
                "cmd": "save_file",
                "path": f"Local/student{user_id:03d}/test_{i}.py",
                "content": f"print('User {user_id}, file {i}')"
            }))
            ws.recv()
            time.sleep(0.1)
        
        ws.close()
        results[user_id] = "Success"
        
    except Exception as e:
        results[user_id] = f"Error: {str(e)}"

def test_load(num_users=10):
    print_test_header(f"Load Test ({num_users} concurrent users)")
    
    print(f"\nSimulating {num_users} concurrent users...")
    print_info("This may take a few moments...")
    
    threads = []
    results = {}
    
    start_time = time.time()
    
    for i in range(1, num_users + 1):
        thread = threading.Thread(target=simulate_user, args=(i, results))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    # Analyze results
    success_count = sum(1 for r in results.values() if r == "Success")
    
    print(f"\nResults:")
    print_info(f"  Time taken: {elapsed:.2f} seconds")
    print_info(f"  Successful: {success_count}/{num_users}")
    
    if success_count == num_users:
        print_success(f"All {num_users} users completed successfully!")
    else:
        print_error(f"Some users failed:")
        for user_id, result in results.items():
            if result != "Success":
                print_error(f"  User {user_id}: {result}")

# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def main():
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}Python IDE Multi-User Platform Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
    
    print_info("\n⚠️  Make sure the server is running on port 10086")
    print_info("Start it with: cd server && source venv/bin/activate && python server.py --port 10086\n")
    
    input("Press Enter to start testing...")
    
    try:
        # Test authentication
        student_session, professor_session = test_authentication()
        
        if not student_session:
            print_error("\nAuthentication failed. Cannot continue tests.")
            return
        
        # Test WebSocket with student
        print("\n" + "="*60)
        student_ws = test_websocket_auth(student_session)
        
        if student_ws:
            # Test file operations
            print("\n" + "="*60)
            test_file_operations(student_ws, "sa9082")
            
            # Test permissions
            if professor_session:
                professor_ws = test_websocket_auth(professor_session)
                if professor_ws:
                    print("\n" + "="*60)
                    test_permissions(student_ws, professor_ws)
                    professor_ws.close()
            
            student_ws.close()
        
        # Load test (optional)
        print("\n" + "="*60)
        response = input("\nRun load test with 10 concurrent users? (y/n): ")
        if response.lower() == 'y':
            test_load(10)
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}Test Suite Complete!{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
        
    except requests.exceptions.ConnectionError:
        print_error("\n✗ Cannot connect to server. Is it running?")
        print_info("Start the server with: cd server && source venv/bin/activate && python server.py --port 10086")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n✗ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()