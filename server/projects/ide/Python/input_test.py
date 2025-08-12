#!/usr/bin/env python3
"""
Comprehensive test for input handling in the IDE
Tests various input scenarios to ensure robust input detection
"""

print("=== Input Test Suite ===")

# Test 1: Silent input() - no prompt
print("\n1. Testing silent input() - this should detect input automatically:")
name = input()
print(f"You entered: {name}")

# Test 2: Input with prompt ending in ": "
print("\n2. Testing input with colon prompt:")
age = input("Enter your age: ")
print(f"Your age is: {age}")

# Test 3: Input with prompt ending in "? "
print("\n3. Testing input with question prompt:")
city = input("What city are you from? ")
print(f"You're from: {city}")

# Test 4: Multiple consecutive inputs
print("\n4. Testing multiple consecutive inputs:")
first = input("First name: ")
last = input("Last name: ")
print(f"Full name: {first} {last}")

# Test 5: Input after some processing
print("\n5. Testing input after computation:")
import time
time.sleep(0.5)  # Small delay
hobby = input()
print(f"Your hobby: {hobby}")

# Test 6: Input with custom prompt
print("\n6. Testing custom prompt:")
color = input(">>> Enter favorite color: ")
print(f"Favorite color: {color}")

print("\n=== All tests completed! ===")
