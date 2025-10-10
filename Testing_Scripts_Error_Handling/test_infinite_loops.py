#!/usr/bin/env python3
"""
Test cases for INFINITE LOOPS that should be detected and terminated
Run each test case individually by uncommenting the specific section
"""

# ==============================================================================
# TEST 1: Classic While Loop (Missing Increment)
# Expected: Should terminate with rate limit error
# ==============================================================================
"""
i = 0
while i < 10:
    print(f"Value: {i}")
    # Forgot: i += 1
"""

# ==============================================================================
# TEST 2: While True with Print
# Expected: Should terminate with rate limit error
# ==============================================================================
"""
while True:
    print("This will run forever!")
"""

# ==============================================================================
# TEST 3: For Loop with List Modification
# Expected: Should terminate with rate limit error
# ==============================================================================
"""
numbers = [1, 2, 3]
for n in numbers:
    print(n)
    numbers.append(n + 1)  # Keeps adding to list!
"""

# ==============================================================================
# TEST 4: Recursive Print (Stack Overflow)
# Expected: Should terminate with rate limit or stack overflow
# ==============================================================================
"""
def print_forever(n=0):
    print(f"Recursion depth: {n}")
    print_forever(n + 1)

print_forever()
"""

# ==============================================================================
# TEST 5: Wrong Condition Check
# Expected: Should terminate with rate limit error
# ==============================================================================
"""
count = 10
while count > 0:
    print(f"Countdown: {count}")
    count += 1  # Should be count -= 1
"""

# ==============================================================================
# TEST 6: Nested Infinite Loops
# Expected: Should terminate with rate limit error
# ==============================================================================
"""
while True:
    for i in range(1000000):
        print(f"Nested: {i}")
        if i < 0:  # Never true
            break
"""

# ==============================================================================
# TEST 7: Generator Infinite Loop
# Expected: Should terminate with rate limit error
# ==============================================================================
"""
def infinite_gen():
    n = 0
    while True:
        yield n
        n += 1

for num in infinite_gen():
    print(f"Generated: {num}")
"""

# ==============================================================================
# TEST 8: List Comprehension Abuse
# Expected: Should terminate with rate limit error
# ==============================================================================
"""
import itertools
for i in itertools.count():
    print(f"Count: {i}")
"""

# ==============================================================================
# TEST 9: String Concatenation Loop
# Expected: Should terminate with total lines limit (exponential growth)
# ==============================================================================
"""
text = "a"
while len(text) < 1000000:
    print(text)
    text = text + text  # Exponential growth!
"""

# ==============================================================================
# TEST 10: Same Line Repeated
# Expected: Should terminate with identical lines detection (500+ repetitions)
# ==============================================================================
"""
while True:
    print("Hello")  # Same line forever
"""

# ==============================================================================
# TEST 11: CPU-Intensive Without Output
# Expected: May NOT be caught (no output) - needs CPU monitoring
# ==============================================================================
"""
while True:
    x = 999999 ** 999999  # Heavy CPU, no output
"""

# ==============================================================================
# TEST 12: Mixed Output Rates
# Expected: Should terminate when burst exceeds rate limit
# ==============================================================================
"""
import random
while True:
    if random.random() > 0.5:
        for i in range(100):
            print(f"Burst: {i}")
    else:
        print("Single line")
"""

# ==============================================================================
# UNCOMMENT ONE TEST AT A TIME TO RUN
# ==============================================================================

# Default test - Classic infinite loop
print("Starting infinite loop test...")
i = 0
while i < 10:
    print(f"Value: {i}")
    # Forgot: i += 1