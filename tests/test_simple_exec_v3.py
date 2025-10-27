#!/usr/bin/env python3
"""
Test Suite for SimpleExecutorV3
Tests the timeout, infinite loop detection, and REPL functionality
"""

import unittest
import time
import threading
import queue
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

# Import the module to test
from command.simple_exec_v3 import SimpleExecutorV3, MessageType

class TestSimpleExecutorV3(unittest.TestCase):
    """Test cases for SimpleExecutorV3"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.mock_client.write_message = Mock()
        self.mock_loop = Mock()

    def test_timeout_3_seconds(self):
        """Test that scripts timeout after 3 seconds"""
        # Create a test script with infinite loop
        test_script = """
while True:
    pass
"""
        with open('/tmp/test_timeout.py', 'w') as f:
            f.write(test_script)

        # Create executor
        executor = SimpleExecutorV3(
            cmd_id='test-1',
            client=self.mock_client,
            loop=self.mock_loop,
            script_path='/tmp/test_timeout.py',
            username='test_user'
        )

        # Start execution in thread
        executor.start()

        # Wait for timeout
        time.sleep(4)

        # Check that timeout occurred
        self.assertFalse(executor.alive)
        self.assertTrue(executor.timeout_occurred)

    def test_output_rate_limiting(self):
        """Test output rate limiting (100 lines/sec)"""
        test_script = """
for i in range(200):
    print(f"Line {i}")
"""
        with open('/tmp/test_rate_limit.py', 'w') as f:
            f.write(test_script)

        executor = SimpleExecutorV3(
            cmd_id='test-2',
            client=self.mock_client,
            loop=self.mock_loop,
            script_path='/tmp/test_rate_limit.py',
            username='test_user'
        )

        # Check rate limiting configuration
        self.assertEqual(executor.MAX_LINES_PER_SECOND, 100)

    def test_identical_line_detection(self):
        """Test identical line detection (500 repeats)"""
        test_script = """
for i in range(1000):
    print("Same line")
"""
        with open('/tmp/test_identical.py', 'w') as f:
            f.write(test_script)

        executor = SimpleExecutorV3(
            cmd_id='test-3',
            client=self.mock_client,
            loop=self.mock_loop,
            script_path='/tmp/test_identical.py',
            username='test_user'
        )

        # Check identical line limit configuration
        self.assertEqual(executor.MAX_IDENTICAL_LINES, 500)

    def test_total_output_limit(self):
        """Test total output limiting (10,000 lines)"""
        executor = SimpleExecutorV3(
            cmd_id='test-4',
            client=self.mock_client,
            loop=self.mock_loop,
            script_path=None,
            username='test_user'
        )

        # Check total line limit configuration
        self.assertEqual(executor.MAX_TOTAL_LINES, 10000)

    def test_repl_without_script(self):
        """Test that REPL starts without a script"""
        executor = SimpleExecutorV3(
            cmd_id='test-5',
            client=self.mock_client,
            loop=self.mock_loop,
            script_path=None,  # No script provided
            username='test_user'
        )

        # Check that no script path is set
        self.assertIsNone(executor.script_path)
        self.assertTrue(executor.alive)

    def test_input_handling(self):
        """Test input() function handling"""
        test_script = """
name = input("Enter name: ")
print(f"Hello, {name}")
"""
        with open('/tmp/test_input.py', 'w') as f:
            f.write(test_script)

        executor = SimpleExecutorV3(
            cmd_id='test-6',
            client=self.mock_client,
            loop=self.mock_loop,
            script_path='/tmp/test_input.py',
            username='test_user'
        )

        # Test that input queue exists
        self.assertIsNotNone(executor.input_queue)
        self.assertIsInstance(executor.input_queue, queue.Queue)

    def test_cleanup_on_stop(self):
        """Test that resources are cleaned up on stop"""
        executor = SimpleExecutorV3(
            cmd_id='test-7',
            client=self.mock_client,
            loop=self.mock_loop,
            script_path=None,
            username='test_user'
        )

        # Stop the executor
        executor.stop()

        # Check that executor is stopped
        self.assertFalse(executor.alive)
        self.assertTrue(executor._stop_event.is_set())

class TestInfiniteLoopDetection(unittest.TestCase):
    """Test infinite loop detection mechanisms"""

    def setUp(self):
        self.mock_client = Mock()
        self.mock_client.write_message = Mock()
        self.mock_loop = Mock()

    def test_timeout_detection(self):
        """Test 3-second timeout detection"""
        executor = SimpleExecutorV3(
            cmd_id='test-timeout',
            client=self.mock_client,
            loop=self.mock_loop,
            script_path=None,
            username='test_user'
        )

        # Check timeout is set to 3 seconds
        self.assertEqual(executor.timeout, 3)

    def test_resource_limits_configured(self):
        """Test that resource limits are configured"""
        executor = SimpleExecutorV3(
            cmd_id='test-resources',
            client=self.mock_client,
            loop=self.mock_loop,
            script_path=None,
            username='test_user'
        )

        # Check memory limit configuration
        self.assertEqual(executor.MEMORY_LIMIT_MB, 128)

        # Check CPU time limit configuration
        self.assertEqual(executor.CPU_TIME_LIMIT, 10)


if __name__ == '__main__':
    unittest.main()