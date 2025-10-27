# Test 3: Error Handling
print("Testing error handling")
print("This line will print")

x = 10
y = 0

print(f"x = {x}, y = {y}")
print("Attempting division by zero...")

result = x / y  # This will cause an error

# These lines should not execute
print("This should not print")
z = 100