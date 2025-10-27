#!/usr/bin/env python3
"""
Test harness for SimpleExecutor
Tests basic script execution and REPL functionality
"""

import sys
import os
import json
import asyncio
import threading
import time
from pathlib import Path

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from command.simple_exec import SimpleExecutor
from command.exec_protocol import MessageType

class MockClient:
    """Mock WebSocket client for testing"""
    def __init__(self):
        self.messages = []
        self.lock = threading.Lock()

    async def write_message(self, message):
        """Mock write_message method"""
        try:
            msg = json.loads(message)

            # Thread-safe append
            with self.lock:
                self.messages.append(msg)

            # Print for debugging
            msg_type = msg.get('type', 'unknown')
            if msg_type == 'stdout':
                print(f"📤 STDOUT: {msg['data']['text']}", end='')
            elif msg_type == 'stderr':
                print(f"📤 STDERR: {msg['data']['text']}", end='')
            elif msg_type == 'repl_ready':
                print(f"🎯 REPL READY: {msg['data']['prompt']}")
            elif msg_type == 'complete':
                print(f"✅ COMPLETE: exit_code={msg['data']['exit_code']}")
            elif msg_type == 'error':
                print(f"❌ ERROR: {msg['data']['error']}")
            elif msg_type == 'debug':
                print(f"🔍 DEBUG: {msg['data']['text']}")
        except Exception as e:
            print(f"⚠️ Mock client error: {e}")

def test_basic_script():
    """Test basic script execution"""
    print("\n" + "="*50)
    print("TEST 1: Basic Script Execution")
    print("="*50)

    # Create test script
    test_script = Path("/tmp/test_basic.py")
    test_script.write_text("""
print("Hello from script!")
x = 42
y = x * 2
print(f"x = {x}, y = {y}")
""")

    # Create mock client and event loop
    client = MockClient()
    loop = asyncio.new_event_loop()

    # Run event loop in thread to process async messages
    loop_thread = threading.Thread(target=loop.run_forever)
    loop_thread.daemon = True
    loop_thread.start()

    # Create and start executor
    executor = SimpleExecutor(
        cmd_id="test-001",
        client=client,
        event_loop=loop,
        script_path=str(test_script)
    )

    # Start executor in thread
    executor.start()

    # Wait for script to complete
    time.sleep(3)

    # Stop executor
    executor.stop()
    executor.join(timeout=2)

    # Stop event loop
    loop.call_soon_threadsafe(loop.stop)
    loop_thread.join(timeout=1)

    # Check results
    print("\n📊 Results:")
    print(f"  - Total messages: {len(client.messages)}")

    # Group messages by type
    for msg in client.messages:
        print(f"    - {msg.get('type')}: {str(msg.get('data', {}))[:100]}")

    stdout_msgs = [m for m in client.messages if m.get('type') == 'stdout']
    print(f"  - Stdout messages: {len(stdout_msgs)}")

    if stdout_msgs:
        # Check if output contains expected text
        full_output = ''.join([m['data']['text'] for m in stdout_msgs])
        print(f"  - Full output length: {len(full_output)} chars")
        print(f"  - Output preview: {full_output[:200]}")

        assert "Hello from script!" in full_output, f"Missing expected output. Got: {full_output}"
        assert "x = 42" in full_output, f"Missing variable output. Got: {full_output}"
    else:
        print("  ⚠️  No stdout messages received!")
        print(f"  All messages: {client.messages}")

    print("✅ Test passed!" if stdout_msgs else "❌ Test failed - no output captured")

    # Cleanup
    test_script.unlink()
    loop.close()

def test_script_with_error():
    """Test script with error"""
    print("\n" + "="*50)
    print("TEST 2: Script with Error")
    print("="*50)

    # Create test script with error
    test_script = Path("/tmp/test_error.py")
    test_script.write_text("""
print("Before error")
x = 1 / 0  # This will cause ZeroDivisionError
print("After error - should not print")
""")

    # Create mock client and event loop
    client = MockClient()
    loop = asyncio.new_event_loop()

    # Create and start executor
    executor = SimpleExecutor(
        cmd_id="test-002",
        client=client,
        event_loop=loop,
        script_path=str(test_script)
    )

    # Start executor in thread
    executor.start()

    # Wait for script to complete
    time.sleep(2)

    # Stop executor
    executor.stop()
    executor.join(timeout=2)

    # Check results
    print("\n📊 Results:")
    stderr_msgs = [m for m in client.messages if m.get('type') == 'stderr']
    stdout_msgs = [m for m in client.messages if m.get('type') == 'stdout']

    print(f"  - Stderr messages: {len(stderr_msgs)}")
    print(f"  - Stdout messages: {len(stdout_msgs)}")

    # Check output
    full_output = ''.join([m['data']['text'] for m in stdout_msgs])
    assert "Before error" in full_output, "Missing output before error"
    assert "After error" not in full_output, "Should not have output after error"

    # Check for error in stderr
    full_stderr = ''.join([m['data']['text'] for m in stderr_msgs if m.get('type') == 'stderr'])
    assert "ZeroDivisionError" in full_stderr or "exit code" in full_stderr, "Missing error indication"

    print("✅ Test passed!")

    # Cleanup
    test_script.unlink()
    loop.close()

def test_repl_mode():
    """Test REPL mode with script variables"""
    print("\n" + "="*50)
    print("TEST 3: REPL Mode (Manual Interaction)")
    print("="*50)

    # Create test script
    test_script = Path("/tmp/test_repl.py")
    test_script.write_text("""
print("Script starting...")
x = 100
y = 200
def greet(name):
    return f"Hello, {name}!"
print("Script complete. Variables x, y, and greet() are available.")
""")

    # Create mock client and event loop
    client = MockClient()
    loop = asyncio.new_event_loop()

    # Create and start executor
    executor = SimpleExecutor(
        cmd_id="test-003",
        client=client,
        event_loop=loop,
        script_path=str(test_script)
    )

    print("Starting executor with REPL...")
    executor.start()

    # Wait for script to complete and REPL to start
    time.sleep(3)

    # Check if REPL is ready
    repl_ready = any(m.get('type') == 'repl_ready' for m in client.messages)
    if repl_ready:
        print("\n🎯 REPL is active! Sending test commands...")

        # Send some REPL commands
        executor.send_input("print(x)")
        time.sleep(1)

        executor.send_input("print(y)")
        time.sleep(1)

        executor.send_input("print(x + y)")
        time.sleep(1)

        # Try the function if it was preserved
        executor.send_input("print(greet('World'))")
        time.sleep(1)
    else:
        print("⚠️  REPL did not start (script may have had an error)")

    # Stop executor
    print("\nStopping executor...")
    executor.stop()
    executor.join(timeout=2)

    print("✅ Test complete!")

    # Cleanup
    test_script.unlink()
    loop.close()

def test_timeout():
    """Test script timeout"""
    print("\n" + "="*50)
    print("TEST 4: Script Timeout (3 seconds)")
    print("="*50)

    # Create test script that runs too long
    test_script = Path("/tmp/test_timeout.py")
    test_script.write_text("""
import time
print("Starting long operation...")
time.sleep(5)  # This exceeds the 3-second timeout
print("This should not print")
""")

    # Create mock client and event loop
    client = MockClient()
    loop = asyncio.new_event_loop()

    # Create and start executor
    executor = SimpleExecutor(
        cmd_id="test-004",
        client=client,
        event_loop=loop,
        script_path=str(test_script)
    )

    # Start executor in thread
    start_time = time.time()
    executor.start()

    # Wait for timeout
    time.sleep(5)

    # Stop executor
    executor.stop()
    executor.join(timeout=2)

    elapsed = time.time() - start_time

    # Check results
    print(f"\n📊 Results:")
    print(f"  - Elapsed time: {elapsed:.1f}s")

    # Check for timeout message
    stderr_msgs = [m for m in client.messages if m.get('type') == 'stderr']
    full_stderr = ''.join([m['data']['text'] for m in stderr_msgs])

    assert "timed out" in full_stderr.lower(), "Missing timeout message"
    assert elapsed < 4.5, "Timeout took too long"

    print("✅ Test passed!")

    # Cleanup
    test_script.unlink()
    loop.close()

if __name__ == "__main__":
    # Set debug mode
    os.environ['DEBUG_MODE'] = 'true'

    print("\n🧪 Testing SimpleExecutor Implementation")
    print("="*60)

    try:
        test_basic_script()
        test_script_with_error()
        test_repl_mode()
        test_timeout()

        print("\n" + "="*60)
        print("🎉 All tests completed!")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)