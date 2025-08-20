#!/usr/bin/env python3
"""
Load testing script to simulate 60 concurrent students using the IDE
Tests the system's ability to handle the target load
"""

import asyncio
import websockets
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor
import statistics

# Configuration
WS_URL = "ws://localhost:10086/ws"
NUM_STUDENTS = 60
TEST_DURATION_SECONDS = 300  # 5 minutes
OPERATIONS_PER_STUDENT_PER_MINUTE = 5

# Test credentials (assuming these are pre-created)
STUDENT_USERNAME_PREFIX = "student"
STUDENT_PASSWORD = "password123"

# Test metrics
metrics = {
    'successful_connections': 0,
    'failed_connections': 0,
    'successful_operations': 0,
    'failed_operations': 0,
    'response_times': [],
    'errors': []
}


class SimulatedStudent:
    """Simulates a single student using the IDE"""
    
    def __init__(self, student_id):
        self.student_id = student_id
        self.username = f"{STUDENT_USERNAME_PREFIX}{student_id:02d}"
        self.websocket = None
        self.authenticated = False
        self.session_id = None
        
    async def connect_and_authenticate(self):
        """Connect to WebSocket and authenticate"""
        try:
            self.websocket = await websockets.connect(WS_URL)
            
            # Wait for auth_required message
            msg = await self.websocket.recv()
            data = json.loads(msg)
            
            if data.get('type') == 'auth_required':
                # Send authentication
                auth_msg = {
                    'cmd': 'authenticate',
                    'username': self.username,
                    'password': STUDENT_PASSWORD
                }
                await self.websocket.send(json.dumps(auth_msg))
                
                # Wait for auth response
                response = await self.websocket.recv()
                auth_data = json.loads(response)
                
                if auth_data.get('type') == 'auth_success':
                    self.authenticated = True
                    self.session_id = auth_data.get('session_id')
                    metrics['successful_connections'] += 1
                    print(f"[Student {self.student_id}] Connected and authenticated")
                    return True
                    
        except Exception as e:
            metrics['failed_connections'] += 1
            metrics['errors'].append(f"Student {self.student_id}: {str(e)}")
            print(f"[Student {self.student_id}] Connection failed: {e}")
            return False
    
    async def perform_operations(self):
        """Perform typical IDE operations"""
        operations = [
            self.list_projects,
            self.create_file,
            self.write_file,
            self.run_python_code,
            self.read_file
        ]
        
        while True:
            try:
                # Pick a random operation
                operation = random.choice(operations)
                
                start_time = time.time()
                success = await operation()
                response_time = time.time() - start_time
                
                if success:
                    metrics['successful_operations'] += 1
                    metrics['response_times'].append(response_time)
                else:
                    metrics['failed_operations'] += 1
                
                # Wait before next operation (simulate thinking time)
                await asyncio.sleep(random.uniform(5, 15))
                
            except Exception as e:
                print(f"[Student {self.student_id}] Operation error: {e}")
                metrics['errors'].append(f"Student {self.student_id} operation: {str(e)}")
                break
    
    async def list_projects(self):
        """List available projects"""
        msg = {
            'cmd': 'ide_list_projects',
            'id': random.randint(1000, 9999)
        }
        await self.websocket.send(json.dumps(msg))
        response = await self.websocket.recv()
        return 'code' in response and '"code":0' in response
    
    async def create_file(self):
        """Create a new Python file"""
        filename = f"test_{self.student_id}_{int(time.time())}.py"
        msg = {
            'cmd': 'ide_create_file',
            'id': random.randint(1000, 9999),
            'data': {
                'projectName': f'Local/{self.username}',
                'parentPath': '',
                'fileName': filename
            }
        }
        await self.websocket.send(json.dumps(msg))
        response = await self.websocket.recv()
        return 'code' in response and '"code":0' in response
    
    async def write_file(self):
        """Write code to a file"""
        code = '''
# Test code by student
import random

def test_function():
    numbers = [random.randint(1, 100) for _ in range(10)]
    return sum(numbers) / len(numbers)

result = test_function()
print(f"Average: {result}")
'''
        msg = {
            'cmd': 'ide_write_file',
            'id': random.randint(1000, 9999),
            'data': {
                'projectName': f'Local/{self.username}',
                'filePath': 'test.py',
                'fileData': code
            }
        }
        await self.websocket.send(json.dumps(msg))
        response = await self.websocket.recv()
        return 'code' in response and '"code":0' in response
    
    async def run_python_code(self):
        """Run a Python script"""
        msg = {
            'cmd': 'run_python_program',
            'cmd_id': random.randint(1000, 9999),
            'data': {
                'projectName': f'Local/{self.username}',
                'filePath': 'test.py'
            }
        }
        await self.websocket.send(json.dumps(msg))
        
        # Wait for execution output
        start_time = time.time()
        while time.time() - start_time < 10:  # 10 second timeout
            response = await self.websocket.recv()
            if 'stdout' in response or 'Script execution completed' in response:
                return True
        return False
    
    async def read_file(self):
        """Read a file"""
        msg = {
            'cmd': 'ide_get_file',
            'id': random.randint(1000, 9999),
            'data': {
                'projectName': f'Local/{self.username}',
                'filePath': 'test.py'
            }
        }
        await self.websocket.send(json.dumps(msg))
        response = await self.websocket.recv()
        return 'code' in response and '"code":0' in response
    
    async def disconnect(self):
        """Disconnect from the server"""
        if self.websocket:
            await self.websocket.close()


async def simulate_student(student_id, duration):
    """Simulate a single student for the test duration"""
    student = SimulatedStudent(student_id)
    
    # Connect and authenticate
    if not await student.connect_and_authenticate():
        return
    
    # Perform operations for the test duration
    try:
        await asyncio.wait_for(
            student.perform_operations(),
            timeout=duration
        )
    except asyncio.TimeoutError:
        pass
    finally:
        await student.disconnect()


async def run_load_test():
    """Run the load test with all students"""
    print(f"Starting load test with {NUM_STUDENTS} students for {TEST_DURATION_SECONDS} seconds")
    print("=" * 60)
    
    start_time = time.time()
    
    # Create tasks for all students
    tasks = []
    for i in range(1, NUM_STUDENTS + 1):
        task = asyncio.create_task(
            simulate_student(i, TEST_DURATION_SECONDS)
        )
        tasks.append(task)
        
        # Stagger the connections slightly
        await asyncio.sleep(0.1)
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    
    duration = time.time() - start_time
    
    # Print results
    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    print(f"Test duration: {duration:.2f} seconds")
    print(f"Target students: {NUM_STUDENTS}")
    print(f"Successful connections: {metrics['successful_connections']}")
    print(f"Failed connections: {metrics['failed_connections']}")
    print(f"Total operations: {metrics['successful_operations'] + metrics['failed_operations']}")
    print(f"Successful operations: {metrics['successful_operations']}")
    print(f"Failed operations: {metrics['failed_operations']}")
    
    if metrics['response_times']:
        print(f"Average response time: {statistics.mean(metrics['response_times']):.3f}s")
        print(f"Median response time: {statistics.median(metrics['response_times']):.3f}s")
        print(f"Max response time: {max(metrics['response_times']):.3f}s")
        print(f"Min response time: {min(metrics['response_times']):.3f}s")
    
    if metrics['errors']:
        print(f"\nErrors encountered: {len(metrics['errors'])}")
        for error in metrics['errors'][:10]:  # Show first 10 errors
            print(f"  - {error}")
    
    # Determine if test passed
    connection_rate = metrics['successful_connections'] / NUM_STUDENTS
    if metrics['successful_operations'] > 0:
        success_rate = metrics['successful_operations'] / (metrics['successful_operations'] + metrics['failed_operations'])
    else:
        success_rate = 0
    
    print("\n" + "=" * 60)
    if connection_rate >= 0.95 and success_rate >= 0.90:
        print("✅ LOAD TEST PASSED")
        print(f"   - {connection_rate*100:.1f}% connection success rate")
        print(f"   - {success_rate*100:.1f}% operation success rate")
    else:
        print("❌ LOAD TEST FAILED")
        print(f"   - Only {connection_rate*100:.1f}% connection success rate (need 95%)")
        print(f"   - Only {success_rate*100:.1f}% operation success rate (need 90%)")
    print("=" * 60)


if __name__ == "__main__":
    print("PythonIDE Load Test - Simulating 60 Concurrent Students")
    print("Make sure the server is running and test users are created!")
    print()
    
    try:
        asyncio.run(run_load_test())
    except KeyboardInterrupt:
        print("\nLoad test interrupted by user")
    except Exception as e:
        print(f"Load test failed with error: {e}")