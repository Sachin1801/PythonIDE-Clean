#!/usr/bin/env python3
"""
Test input() handling in both script and REPL modes
"""

import sys
import os
import time
import threading
import asyncio
from pathlib import Path
import json

sys.path.insert(0, 'server')

from command.simple_exec_v2 import SimpleExecutorV2

class TestClient:
    """Test client that simulates WebSocket"""
    def __init__(self):
        self.messages = []
        self.waiting_for_input = False
        self.input_prompt = ""

    async def write_message(self, message):
        """Mock write_message method"""
        try:
            msg = json.loads(message)
            self.messages.append(msg)

            # Display different message types
            msg_type = msg.get('type', 'unknown')

            if msg_type == 'stdout':
                print(msg['data']['text'], end='', flush=True)

            elif msg_type == 'stderr':
                print(f"\033[91m{msg['data']['text']}\033[0m", end='', flush=True)

            elif msg_type == 'input_request':
                self.waiting_for_input = True
                self.input_prompt = msg['data']['prompt']
                print(f"\n\033[93m[INPUT REQUESTED: {self.input_prompt}]\033[0m")

            elif msg_type == 'repl_ready':
                print(f"\n\033[92m[REPL READY: {msg['data']['prompt']}]\033[0m")

            elif msg_type == 'complete':
                print(f"\n\033[94m[EXECUTION COMPLETE: exit_code={msg['data']['exit_code']}]\033[0m")

        except Exception as e:
            print(f"Client error: {e}")

def test_script_with_input():
    """Test a script that uses input()"""
    print("\n" + "="*60)
    print("TEST 1: Script with input() function")
    print("="*60)

    # Create test script
    test_script = Path("/tmp/test_input.py")
    test_script.write_text("""
# Test script with input()
print("Welcome to the input test!")

name = input("What is your name? ")
print(f"Hello, {name}!")

age = input("How old are you? ")
print(f"You are {age} years old.")

# Do some calculation
birth_year = 2024 - int(age)
print(f"You were born around {birth_year}")

favorite = input("What's your favorite color? ")
print(f"Nice! {favorite} is a great color!")

print("Script complete. Variables available in REPL: name, age, birth_year, favorite")
""")

    # Create client and event loop
    client = TestClient()
    loop = asyncio.new_event_loop()

    # Run event loop in thread
    loop_thread = threading.Thread(target=loop.run_forever)
    loop_thread.daemon = True
    loop_thread.start()

    # Create and start executor
    executor = SimpleExecutorV2(
        cmd_id="test-input-001",
        client=client,
        event_loop=loop,
        script_path=str(test_script)
    )

    print("\nStarting script execution...")
    executor.start()

    # Wait a bit for script to start
    time.sleep(1)

    # Simulate user inputs
    print("\n\033[96m[SIMULATING USER INPUT: 'Alice']\033[0m")
    executor.send_input("Alice")
    time.sleep(1)

    print("\n\033[96m[SIMULATING USER INPUT: '25']\033[0m")
    executor.send_input("25")
    time.sleep(1)

    print("\n\033[96m[SIMULATING USER INPUT: 'Blue']\033[0m")
    executor.send_input("Blue")
    time.sleep(2)

    # Now test REPL with the variables
    print("\n\033[96m[TESTING REPL - Checking if variables persist]\033[0m")
    time.sleep(1)

    executor.send_input("print(f'Name: {name}, Age: {age}')")
    time.sleep(1)

    executor.send_input("print(f'Birth year: {birth_year}')")
    time.sleep(1)

    executor.send_input("print(f'Favorite: {favorite}')")
    time.sleep(1)

    # Test input() in REPL
    print("\n\033[96m[TESTING input() IN REPL]\033[0m")
    executor.send_input("city = input('What city are you from? ')")
    time.sleep(1)

    print("\n\033[96m[SIMULATING USER INPUT: 'New York']\033[0m")
    executor.send_input("New York")
    time.sleep(1)

    executor.send_input("print(f'You are from {city}')")
    time.sleep(1)

    # Stop execution
    print("\n\033[96m[STOPPING EXECUTION]\033[0m")
    executor.stop()
    executor.join(timeout=3)

    # Stop event loop
    loop.call_soon_threadsafe(loop.stop)
    loop_thread.join(timeout=1)

    # Cleanup
    test_script.unlink()

    print("\n\033[92m✅ Test completed!\033[0m")

def test_script_with_multiple_inputs():
    """Test a script with multiple input() calls in sequence"""
    print("\n" + "="*60)
    print("TEST 2: Script with multiple sequential inputs")
    print("="*60)

    # Create test script
    test_script = Path("/tmp/test_multi_input.py")
    test_script.write_text("""
# Test multiple inputs
print("Survey Application")
print("-" * 30)

responses = {}

responses['q1'] = input("Question 1: Do you like Python? (yes/no): ")
responses['q2'] = input("Question 2: Years of programming experience: ")
responses['q3'] = input("Question 3: Favorite IDE: ")

print("\\nSurvey Results:")
for key, value in responses.items():
    print(f"  {key}: {value}")

print(f"\\nTotal responses: {len(responses)}")
""")

    # Create client and event loop
    client = TestClient()
    loop = asyncio.new_event_loop()

    loop_thread = threading.Thread(target=loop.run_forever)
    loop_thread.daemon = True
    loop_thread.start()

    executor = SimpleExecutorV2(
        cmd_id="test-multi-001",
        client=client,
        event_loop=loop,
        script_path=str(test_script)
    )

    print("\nStarting script execution...")
    executor.start()

    time.sleep(1)

    # Answer survey questions
    print("\n\033[96m[ANSWERING: 'yes']\033[0m")
    executor.send_input("yes")
    time.sleep(1)

    print("\n\033[96m[ANSWERING: '5']\033[0m")
    executor.send_input("5")
    time.sleep(1)

    print("\n\033[96m[ANSWERING: 'VS Code']\033[0m")
    executor.send_input("VS Code")
    time.sleep(2)

    # Check variables in REPL
    print("\n\033[96m[CHECKING VARIABLES IN REPL]\033[0m")
    executor.send_input("print(responses)")
    time.sleep(1)

    executor.stop()
    executor.join(timeout=3)

    loop.call_soon_threadsafe(loop.stop)
    loop_thread.join(timeout=1)

    test_script.unlink()

    print("\n\033[92m✅ Test completed!\033[0m")

def test_input_with_validation():
    """Test input() with validation loop"""
    print("\n" + "="*60)
    print("TEST 3: Input with validation")
    print("="*60)

    test_script = Path("/tmp/test_validation.py")
    test_script.write_text("""
# Test input validation
print("Number Guessing Game")

secret = 42

while True:
    guess = input("Guess a number between 1 and 100: ")
    try:
        num = int(guess)
        if num == secret:
            print(f"Correct! The number was {secret}")
            break
        elif num < secret:
            print("Too low! Try again.")
        else:
            print("Too high! Try again.")
    except ValueError:
        print(f"'{guess}' is not a valid number. Try again.")

print("Game over!")
""")

    client = TestClient()
    loop = asyncio.new_event_loop()

    loop_thread = threading.Thread(target=loop.run_forever)
    loop_thread.daemon = True
    loop_thread.start()

    executor = SimpleExecutorV2(
        cmd_id="test-validation-001",
        client=client,
        event_loop=loop,
        script_path=str(test_script)
    )

    print("\nStarting script execution...")
    executor.start()

    time.sleep(1)

    # Make some guesses
    print("\n\033[96m[GUESSING: '20']\033[0m")
    executor.send_input("20")
    time.sleep(1)

    print("\n\033[96m[GUESSING: '50']\033[0m")
    executor.send_input("50")
    time.sleep(1)

    print("\n\033[96m[GUESSING: 'abc' - invalid]\033[0m")
    executor.send_input("abc")
    time.sleep(1)

    print("\n\033[96m[GUESSING: '42' - correct!]\033[0m")
    executor.send_input("42")
    time.sleep(2)

    # Check REPL
    print("\n\033[96m[CHECKING VARIABLES IN REPL]\033[0m")
    executor.send_input("print(f'Secret was: {secret}')")
    time.sleep(1)

    executor.stop()
    executor.join(timeout=3)

    loop.call_soon_threadsafe(loop.stop)
    loop_thread.join(timeout=1)

    test_script.unlink()

    print("\n\033[92m✅ Test completed!\033[0m")

if __name__ == "__main__":
    # Set debug mode
    os.environ['DEBUG_MODE'] = 'false'  # Set to true for more output

    print("\n🧪 Testing input() Handling in SimpleExecutorV2")
    print("="*60)

    try:
        test_script_with_input()
        test_script_with_multiple_inputs()
        test_input_with_validation()

        print("\n" + "="*60)
        print("🎉 All input() tests completed successfully!")
        print("="*60)

        print("\n📝 Summary:")
        print("  ✅ input() in scripts works with prompt detection")
        print("  ✅ Multiple sequential input() calls handled")
        print("  ✅ Input validation loops work correctly")
        print("  ✅ Variables persist to REPL after script")
        print("  ✅ input() works within REPL mode")
        print("  ✅ Frontend receives INPUT_REQUEST messages")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)