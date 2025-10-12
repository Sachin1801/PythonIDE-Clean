#!/usr/bin/env python3
"""
Performance Testing Script for Python IDE
Tests single-process vs multi-process Tornado configuration
"""

import asyncio
import aiohttp
import json
import time
import statistics
from typing import List, Dict
import sys
import argparse

# Test configuration
IDE_URL = "http://localhost:10087"
WS_URL = "ws://localhost:10087/ws"

class PerformanceTest:
    def __init__(self, num_students: int = 10, test_duration: int = 30):
        self.num_students = num_students
        self.test_duration = test_duration
        self.results = []

    async def test_login(self, session: aiohttp.ClientSession, student_id: int) -> float:
        """Test login endpoint performance"""
        start = time.time()
        try:
            async with session.post(f"{IDE_URL}/api/login", json={
                "username": f"test_student_{student_id}",
                "password": "test123"
            }) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return time.time() - start, data.get('token')
                else:
                    print(f"Login failed for student {student_id}: {resp.status}")
                    return -1, None
        except Exception as e:
            print(f"Login error for student {student_id}: {e}")
            return -1, None

    async def test_websocket(self, student_id: int, token: str) -> Dict:
        """Test WebSocket connection and code execution"""
        results = {
            "connect_time": 0,
            "code_exec_time": 0,
            "file_save_time": 0,
            "errors": 0
        }

        try:
            session = aiohttp.ClientSession()

            # Test WebSocket connection
            start = time.time()
            ws = await session.ws_connect(WS_URL, headers={
                "Authorization": f"Bearer {token}"
            })
            results["connect_time"] = time.time() - start

            # Test code execution
            start = time.time()
            await ws.send_str(json.dumps({
                "cmd": "runcode",
                "id": 1,
                "data": {
                    "code": f"# Student {student_id} test\nfor i in range(10):\n    print(f'Test {{i}}')"
                }
            }))

            # Wait for response
            msg = await ws.receive(timeout=5)
            if msg.type == aiohttp.WSMsgType.TEXT:
                results["code_exec_time"] = time.time() - start
            else:
                results["errors"] += 1

            # Test file save
            start = time.time()
            await ws.send_str(json.dumps({
                "cmd": "savefile",
                "id": 2,
                "data": {
                    "path": f"test_student_{student_id}/test.py",
                    "content": f"# Test file for student {student_id}\nprint('Hello World')"
                }
            }))

            msg = await ws.receive(timeout=5)
            if msg.type == aiohttp.WSMsgType.TEXT:
                results["file_save_time"] = time.time() - start
            else:
                results["errors"] += 1

            await ws.close()
            await session.close()

        except Exception as e:
            print(f"WebSocket error for student {student_id}: {e}")
            results["errors"] += 1

        return results

    async def simulate_student(self, student_id: int) -> Dict:
        """Simulate a single student's activities"""
        student_results = {
            "student_id": student_id,
            "login_time": 0,
            "ws_connect_time": 0,
            "code_exec_time": 0,
            "file_save_time": 0,
            "total_errors": 0
        }

        async with aiohttp.ClientSession() as session:
            # Login
            login_time, token = await self.test_login(session, student_id)
            if login_time > 0 and token:
                student_results["login_time"] = login_time

                # WebSocket tests
                ws_results = await self.test_websocket(student_id, token)
                student_results.update(ws_results)
                student_results["ws_connect_time"] = ws_results["connect_time"]
                student_results["code_exec_time"] = ws_results["code_exec_time"]
                student_results["file_save_time"] = ws_results["file_save_time"]
                student_results["total_errors"] = ws_results["errors"]
            else:
                student_results["total_errors"] = 1

        return student_results

    async def run_load_test(self) -> None:
        """Run concurrent load test with multiple students"""
        print(f"\n🚀 Starting load test with {self.num_students} concurrent students...")
        print(f"   Test duration: {self.test_duration} seconds")
        print(f"   Target URL: {IDE_URL}")
        print("-" * 60)

        # Run all students concurrently
        tasks = [self.simulate_student(i) for i in range(self.num_students)]
        self.results = await asyncio.gather(*tasks)

        # Calculate and display statistics
        self.display_results()

    def display_results(self):
        """Display test results and statistics"""
        print("\n📊 PERFORMANCE TEST RESULTS")
        print("=" * 60)

        # Filter out failed results
        successful_results = [r for r in self.results if r["total_errors"] == 0]

        if not successful_results:
            print("❌ All tests failed! Check if the server is running.")
            return

        metrics = {
            "login_time": [r["login_time"] for r in successful_results if r["login_time"] > 0],
            "ws_connect_time": [r["ws_connect_time"] for r in successful_results if r["ws_connect_time"] > 0],
            "code_exec_time": [r["code_exec_time"] for r in successful_results if r["code_exec_time"] > 0],
            "file_save_time": [r["file_save_time"] for r in successful_results if r["file_save_time"] > 0],
        }

        print(f"✅ Successful tests: {len(successful_results)}/{self.num_students}")
        print(f"❌ Failed tests: {self.num_students - len(successful_results)}")
        print()

        for metric_name, values in metrics.items():
            if values:
                avg = statistics.mean(values)
                median = statistics.median(values)
                p95 = sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0]

                print(f"📈 {metric_name.replace('_', ' ').title()}:")
                print(f"   Average: {avg:.3f}s")
                print(f"   Median:  {median:.3f}s")
                print(f"   95th %:  {p95:.3f}s")
                print()

        # Overall assessment
        avg_response = statistics.mean([
            statistics.mean(metrics["login_time"]) if metrics["login_time"] else 0,
            statistics.mean(metrics["code_exec_time"]) if metrics["code_exec_time"] else 0,
        ])

        print("-" * 60)
        if avg_response < 1.0:
            print(f"🎉 EXCELLENT: Average response time {avg_response:.2f}s")
        elif avg_response < 2.0:
            print(f"✅ GOOD: Average response time {avg_response:.2f}s")
        elif avg_response < 3.0:
            print(f"⚠️ ACCEPTABLE: Average response time {avg_response:.2f}s")
        else:
            print(f"❌ POOR: Average response time {avg_response:.2f}s - needs optimization")


async def compare_configurations():
    """Compare single-process vs multi-process performance"""
    print("\n" + "="*80)
    print("🔬 TORNADO MULTI-PROCESS OPTIMIZATION TEST")
    print("="*80)

    # Instructions
    print("\n📋 TEST PROCEDURE:")
    print("1. First, we'll test with single-process (current configuration)")
    print("2. Then, we'll test with multi-process (optimized configuration)")
    print("3. Finally, we'll compare the results")

    input("\nPress Enter to start single-process test...")

    # Test 1: Single process
    print("\n🔧 TEST 1: SINGLE-PROCESS MODE")
    print("-" * 40)
    test1 = PerformanceTest(num_students=20, test_duration=30)
    await test1.run_load_test()
    single_process_results = test1.results

    print("\n" + "="*80)
    print("⚠️ IMPORTANT: Now restart the server with multi-process mode:")
    print("   1. Stop current docker-compose (Ctrl+C)")
    print("   2. Run: TEST_TORNADO_PROCESSES=2 docker-compose -f docker-compose.test.yml up")
    print("   3. Wait for server to start")
    input("\nPress Enter when multi-process server is ready...")

    # Test 2: Multi-process
    print("\n🔧 TEST 2: MULTI-PROCESS MODE (2 processes)")
    print("-" * 40)
    test2 = PerformanceTest(num_students=20, test_duration=30)
    await test2.run_load_test()
    multi_process_results = test2.results

    # Compare results
    print("\n" + "="*80)
    print("📊 COMPARISON RESULTS")
    print("="*80)

    # Calculate improvements
    single_avg = statistics.mean([r["code_exec_time"] for r in single_process_results if r["code_exec_time"] > 0])
    multi_avg = statistics.mean([r["code_exec_time"] for r in multi_process_results if r["code_exec_time"] > 0])

    improvement = ((single_avg - multi_avg) / single_avg) * 100

    print(f"\n🎯 Code Execution Performance:")
    print(f"   Single-process: {single_avg:.3f}s average")
    print(f"   Multi-process:  {multi_avg:.3f}s average")
    print(f"   Improvement:    {improvement:.1f}%")

    if improvement > 20:
        print(f"\n🎉 SIGNIFICANT IMPROVEMENT! Multi-process is {improvement:.1f}% faster!")
    elif improvement > 0:
        print(f"\n✅ IMPROVEMENT: Multi-process is {improvement:.1f}% faster")
    else:
        print(f"\n⚠️ NO IMPROVEMENT: Single-process might be sufficient")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Performance test for Python IDE")
    parser.add_argument("--students", type=int, default=10, help="Number of concurrent students")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    parser.add_argument("--compare", action="store_true", help="Compare single vs multi-process")

    args = parser.parse_args()

    if args.compare:
        asyncio.run(compare_configurations())
    else:
        test = PerformanceTest(num_students=args.students, test_duration=args.duration)
        asyncio.run(test.run_load_test())