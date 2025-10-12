#!/usr/bin/env python3
"""
Load Test: Simulate 50 concurrent students using the Python IDE
"""

import asyncio
import aiohttp
import json
import time
import random
from typing import List

IDE_URL = "http://localhost:10087"
WS_URL = "ws://localhost:10087/ws"

# Color codes for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

class Student:
    def __init__(self, student_id: int):
        self.id = student_id
        self.username = f"test_student_{student_id}"
        self.password = "test123"
        self.token = None
        self.response_times = []
        self.errors = 0

    async def login(self, session: aiohttp.ClientSession):
        """Login and get authentication token"""
        try:
            async with session.post(f"{IDE_URL}/api/login", json={
                "username": self.username,
                "password": self.password
            }) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.token = data.get('token')
                    return True
                else:
                    print(f"{RED}❌ Student {self.id}: Login failed{RESET}")
                    self.errors += 1
                    return False
        except Exception as e:
            print(f"{RED}❌ Student {self.id}: Login error - {e}{RESET}")
            self.errors += 1
            return False

    async def run_activities(self):
        """Simulate typical student activities"""
        if not self.token:
            return

        session = aiohttp.ClientSession()
        try:
            # Connect to WebSocket
            ws = await session.ws_connect(WS_URL, headers={
                "Authorization": f"Bearer {self.token}"
            })

            # Activity 1: Run simple code
            await asyncio.sleep(random.uniform(0, 2))  # Random delay to simulate real behavior
            start = time.time()
            await ws.send_str(json.dumps({
                "cmd": "runcode",
                "id": 1,
                "data": {
                    "code": f"# Student {self.id}\nfor i in range(100):\n    print(i)"
                }
            }))
            msg = await ws.receive(timeout=10)
            self.response_times.append(time.time() - start)

            # Activity 2: Save a file
            await asyncio.sleep(random.uniform(1, 3))
            start = time.time()
            await ws.send_str(json.dumps({
                "cmd": "savefile",
                "id": 2,
                "data": {
                    "path": f"test_student_{self.id}/assignment.py",
                    "content": f"# Assignment for student {self.id}\n" + "x = 42\n" * 100
                }
            }))
            msg = await ws.receive(timeout=10)
            self.response_times.append(time.time() - start)

            # Activity 3: Run more complex code
            await asyncio.sleep(random.uniform(1, 2))
            start = time.time()
            await ws.send_str(json.dumps({
                "cmd": "runcode",
                "id": 3,
                "data": {
                    "code": """
import time
def fibonacci(n):
    if n <= 1: return n
    return fibonacci(n-1) + fibonacci(n-2)

result = [fibonacci(i) for i in range(10)]
print(result)
"""
                }
            }))
            msg = await ws.receive(timeout=15)
            self.response_times.append(time.time() - start)

            # Activity 4: Load a file
            await asyncio.sleep(random.uniform(0.5, 1.5))
            start = time.time()
            await ws.send_str(json.dumps({
                "cmd": "loadfile",
                "id": 4,
                "data": {
                    "path": f"test_student_{self.id}/assignment.py"
                }
            }))
            msg = await ws.receive(timeout=10)
            self.response_times.append(time.time() - start)

            print(f"{GREEN}✅ Student {self.id}: Completed all activities{RESET}")

            await ws.close()
        except asyncio.TimeoutError:
            print(f"{YELLOW}⚠️ Student {self.id}: Request timeout{RESET}")
            self.errors += 1
        except Exception as e:
            print(f"{RED}❌ Student {self.id}: Error - {e}{RESET}")
            self.errors += 1
        finally:
            await session.close()

    async def simulate(self):
        """Full simulation for this student"""
        async with aiohttp.ClientSession() as session:
            # Login first
            if await self.login(session):
                # Then run activities
                await self.run_activities()

        return {
            "student_id": self.id,
            "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else -1,
            "max_response_time": max(self.response_times) if self.response_times else -1,
            "errors": self.errors,
            "success": self.errors == 0 and len(self.response_times) > 0
        }


async def run_load_test(num_students: int = 50):
    """Run the load test with specified number of students"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}🚀 LOAD TEST: Simulating {num_students} Concurrent Students{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    print(f"Target URL: {IDE_URL}")
    print(f"Starting simulation...\n")

    # Create students
    students = [Student(i) for i in range(num_students)]

    # Run all students concurrently
    start_time = time.time()
    results = await asyncio.gather(*[student.simulate() for student in students])
    total_time = time.time() - start_time

    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}📊 LOAD TEST RESULTS{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Successful students: {GREEN}{len(successful)}/{num_students}{RESET}")
    print(f"Failed students: {RED}{len(failed)}/{num_students}{RESET}")

    if successful:
        avg_times = [r["avg_response_time"] for r in successful]
        max_times = [r["max_response_time"] for r in successful]

        overall_avg = sum(avg_times) / len(avg_times)
        overall_max = max(max_times)

        print(f"\n📈 Response Time Statistics:")
        print(f"  Average response time: {overall_avg:.3f}s")
        print(f"  Maximum response time: {overall_max:.3f}s")
        print(f"  Min average: {min(avg_times):.3f}s")
        print(f"  Max average: {max(avg_times):.3f}s")

        # Performance assessment
        print(f"\n🎯 Performance Assessment:")
        if overall_avg < 1.0:
            print(f"  {GREEN}EXCELLENT - System handles {num_students} students very well!{RESET}")
        elif overall_avg < 2.0:
            print(f"  {GREEN}GOOD - System handles {num_students} students adequately{RESET}")
        elif overall_avg < 3.0:
            print(f"  {YELLOW}ACCEPTABLE - Some optimization may help{RESET}")
        else:
            print(f"  {RED}POOR - System struggling with {num_students} students{RESET}")
            print(f"  {RED}Consider enabling multi-process mode{RESET}")

        # Check if any students had issues
        if failed:
            print(f"\n{YELLOW}⚠️ Warning: {len(failed)} students experienced errors{RESET}")
            print("  This might indicate the system is at capacity")

        # Success rate
        success_rate = (len(successful) / num_students) * 100
        print(f"\n✅ Success Rate: {success_rate:.1f}%")

        if success_rate < 90:
            print(f"  {RED}⚠️ Success rate below 90% - system may be overloaded{RESET}")
    else:
        print(f"\n{RED}❌ All tests failed! Is the server running?{RESET}")
        print(f"   Check: docker-compose -f docker-compose.test.yml ps")

    return results


async def continuous_load_test(num_students: int = 50, duration_minutes: int = 5):
    """Run continuous load test for specified duration"""
    print(f"\n{BLUE}🔄 CONTINUOUS LOAD TEST{RESET}")
    print(f"Students: {num_students}, Duration: {duration_minutes} minutes")
    print(f"Starting in 3 seconds...\n")
    await asyncio.sleep(3)

    end_time = time.time() + (duration_minutes * 60)
    iteration = 0

    while time.time() < end_time:
        iteration += 1
        print(f"\n{YELLOW}--- Iteration {iteration} ---{RESET}")
        await run_load_test(num_students)

        remaining = int(end_time - time.time())
        if remaining > 30:
            print(f"\n⏰ Next iteration in 30 seconds... ({remaining}s remaining)")
            await asyncio.sleep(30)
        else:
            break

    print(f"\n{GREEN}✅ Continuous load test completed!{RESET}")


if __name__ == "__main__":
    import sys

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            # Run continuous test
            num_students = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            asyncio.run(continuous_load_test(num_students, duration))
        else:
            # Run single test with specified number of students
            num_students = int(sys.argv[1])
            asyncio.run(run_load_test(num_students))
    else:
        # Default: 50 students
        asyncio.run(run_load_test(50))