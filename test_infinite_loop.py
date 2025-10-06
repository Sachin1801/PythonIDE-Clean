#!/usr/bin/env python3
"""
Test infinite loop to verify timeout works
"""

print("Starting infinite loop test...")
i = 0
while True:
    i += 1
    if i % 10000000 == 0:
        print(f"Still running... {i}")