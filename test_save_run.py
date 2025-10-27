#!/usr/bin/env python3
"""
Test script to verify file save + run functionality
"""

# Test 1: Basic execution
print("Test 1: Basic execution")
print("Hello from test_save_run.py!")

# Test 2: Variable creation
x = 42
y = "test"
print(f"Variables created: x={x}, y={y}")

# Test 3: Function definition
def greet(name):
    return f"Hello, {name}!"

print(greet("Tester"))

# Test 4: Simple loop
print("Counting to 5:")
for i in range(1, 6):
    print(f"  {i}")

print("\nScript execution complete!")
print("Variables available for REPL: x, y, greet")