# Test file for Hybrid REPL functionality
# This script should execute and then transition to REPL mode

print("Starting script execution...")

# Define some variables that should be available in REPL
x = 10
y = 20
result = x + y

print(f"Calculated: {x} + {y} = {result}")

# Define a function
def greet(name):
    return f"Hello, {name}!"

print("Function 'greet' defined")

# Create a list and dictionary
numbers = [1, 2, 3, 4, 5]
data = {"name": "Test", "value": 42}

print(f"Numbers: {numbers}")
print(f"Data: {data}")

print("\nScript execution completed.")
print("All variables (x, y, result, greet, numbers, data) should be available in REPL mode")