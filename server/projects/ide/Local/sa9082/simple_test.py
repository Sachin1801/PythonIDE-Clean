for i in range(4):
    print(i)
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