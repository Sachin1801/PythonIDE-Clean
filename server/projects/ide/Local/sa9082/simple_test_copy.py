def greet(name):
    print("Hello,", name)
greet("Alice")  # Output: Hello, Alice
def square(x):
    return x * x
print(square(6))  # Output: 36
def add(a, b):
    return a + b
print(add(5, 3))  # Output: 8
#!/usr/bin/env python3
"""Simple test for hybrid REPL"""

# Define variables
x = 10
y = 20
message = "Hello REPL!"

# Simple function
def add(a, b):
    return a + b

# Print outputs
print(f"x = {x}")
print(f"y = {y}")
print(f"x + y = {add(x, y)}")
print(f"Message: {message}")
print("\nVariables available in REPL: x, y, message, add()")