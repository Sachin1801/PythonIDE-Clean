# Week 2: Control Flow in Python

# 1. If statements
score = 85

if score >= 90:
    grade = 'A'
elif score >= 80:
    grade = 'B'
elif score >= 70:
    grade = 'C'
else:
    grade = 'F'

print(f"Score: {score}, Grade: {grade}")

# 2. Loops
print("\nFor loop example:")
for i in range(5):
    print(f"Iteration {i}")

print("\nWhile loop example:")
count = 0
while count < 3:
    print(f"Count is {count}")
    count += 1

# 3. List comprehensions
numbers = [1, 2, 3, 4, 5]
squares = [n**2 for n in numbers]
print(f"\nSquares: {squares}")
