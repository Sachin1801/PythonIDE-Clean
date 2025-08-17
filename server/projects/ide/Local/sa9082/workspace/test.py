# Example Python Program
# This file demonstrates basic Python concepts

def greet(name):
    """A simple greeting function"""
    return f"Hello, {name}!"

def calculate_average(numbers):
    """Calculate the average of a list of numbers"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

# Main program
if __name__ == "__main__":
    # Test the greeting function
    print(greet("Python Learner"))
    
    # Test the average function
    scores = [85, 92, 78, 95, 88]
    avg = calculate_average(scores)
    print(f"Average score: {avg:.2f}")
    
    # Try a simple loop
    print("\nCounting to 5:")
    for i in range(1, 6):
        print(f"  {i}")
