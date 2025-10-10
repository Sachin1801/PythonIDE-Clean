#!/usr/bin/env python3
"""
Test cases for LEGITIMATE scripts that should NOT be killed
These scripts produce lots of output but are NOT infinite loops
Run each test case individually by uncommenting the specific section
"""

# ==============================================================================
# TEST 1: Large Range Loops (Finite but Many Lines)
# Expected: Should complete successfully (100 lines)
# ==============================================================================
"""
for i in range(100):
    print(f"Processing item {i}")
print("Done!")
"""

# ==============================================================================
# TEST 2: Fast Data Processing with Progress
# Expected: Should complete successfully (75 lines)
# ==============================================================================
"""
data = list(range(75))
for i, item in enumerate(data):
    print(f"Processing: {i}/{len(data)}")
    result = item * 2
print("Processing complete!")
"""

# ==============================================================================
# TEST 3: Reading Large Files Line by Line
# Expected: Should complete successfully (80 lines)
# ==============================================================================
"""
lines = ["Line " + str(i) for i in range(80)]
for line in lines:
    print(f"Reading: {line}")
print("File processed successfully")
"""

# ==============================================================================
# TEST 4: Matrix/Table Printing
# Expected: Should complete successfully (100 lines)
# ==============================================================================
"""
for i in range(1, 11):
    for j in range(1, 11):
        print(f"{i} x {j} = {i*j}")
print("Table complete")
"""

# ==============================================================================
# TEST 5: Debug Logging During Algorithm
# Expected: Should complete successfully (~200 lines)
# ==============================================================================
"""
arr = [64, 34, 25, 12, 22, 11, 90, 45, 33, 77]
n = len(arr)
for i in range(n):
    for j in range(0, n-i-1):
        print(f"Comparing {arr[j]} and {arr[j+1]}")
        if arr[j] > arr[j+1]:
            arr[j], arr[j+1] = arr[j+1], arr[j]
            print(f"Swapped!")
print(f"Sorted: {arr}")
"""

# ==============================================================================
# TEST 6: Progress Bar Simulation
# Expected: Should complete successfully (51 lines with delays)
# ==============================================================================
"""
import time
for i in range(0, 101, 2):
    print(f"Downloading: {i}%")
    time.sleep(0.01)
print("Download complete!")
"""

# ==============================================================================
# TEST 7: Recursive But Bounded
# Expected: Should complete successfully (40 lines)
# ==============================================================================
"""
def factorial_verbose(n):
    print(f"Computing factorial({n})")
    if n <= 1:
        return 1
    result = n * factorial_verbose(n-1)
    print(f"factorial({n}) = {result}")
    return result

factorial_verbose(20)
"""

# ==============================================================================
# TEST 8: Data Generation with Limit
# Expected: Should complete successfully (60 lines)
# ==============================================================================
"""
a, b = 0, 1
count = 0
while count < 60:
    print(f"Fibonacci #{count}: {a}")
    a, b = b, a + b
    count += 1
print("Sequence complete")
"""

# ==============================================================================
# TEST 9: ASCII Art Generation
# Expected: Should complete successfully (19 lines)
# ==============================================================================
"""
size = 10
for i in range(size):
    print("*" * (i + 1))
for i in range(size - 1, 0, -1):
    print("*" * i)
print("Pattern complete!")
"""

# ==============================================================================
# TEST 10: Test Results Output
# Expected: Should complete successfully (80 lines)
# ==============================================================================
"""
tests = ["test_login", "test_logout", "test_signup", "test_profile",
         "test_settings", "test_api", "test_database", "test_cache"]

for test in tests * 5:
    print(f"Running {test}...")
    print(f"✓ {test} passed")

print(f"\\nAll {len(tests)*5} tests passed!")
"""

# ==============================================================================
# TEST 11: Scientific Computation with Output
# Expected: Should complete successfully (~25 lines)
# ==============================================================================
"""
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = []
for num in range(2, 100):
    if is_prime(num):
        print(f"Found prime: {num}")
        primes.append(num)

print(f"Total primes found: {len(primes)}")
"""

# ==============================================================================
# TEST 12: Error Recovery with Retries
# Expected: Should complete successfully (~15-30 lines)
# ==============================================================================
"""
import random

for endpoint in ["api/users", "api/posts", "api/comments"]:
    retries = 0
    while retries < 5:
        print(f"Attempting {endpoint} (try {retries + 1})")
        if random.random() > 0.3:
            print(f"✓ {endpoint} succeeded")
            break
        retries += 1
        print(f"✗ {endpoint} failed, retrying...")
    else:
        print(f"ERROR: {endpoint} failed after 5 attempts")

print("API testing complete")
"""

# ==============================================================================
# TEST 13: Large But Legitimate Output (Edge Case)
# Expected: Should complete successfully (500 lines - under all limits)
# ==============================================================================
"""
for i in range(500):
    print(f"Line {i}: Processing data...")
print("Large batch complete!")
"""

# ==============================================================================
# TEST 14: Repeated But Limited Output (Edge Case)
# Expected: Should complete successfully (100 identical lines - under 500 limit)
# ==============================================================================
"""
for i in range(100):
    print("Processing...")  # Same line 100 times
print("Repetitive task complete!")
"""

# ==============================================================================
# DEFAULT TEST - Run a safe example
# ==============================================================================

print("Running legitimate script test...")
print("This should NOT be terminated as infinite loop")
print()

# Matrix multiplication table (100 lines quickly)
for i in range(1, 11):
    for j in range(1, 11):
        print(f"{i} x {j} = {i*j}")
print("\nTable complete - Script finished successfully!")