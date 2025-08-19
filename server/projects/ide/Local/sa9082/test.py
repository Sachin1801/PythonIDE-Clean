# Example Python script
# You can edit and run this file

import datetime

def greet_user(name):
    """Greet the user with current time"""
    current_time = datetime.datetime.now()
    print(f"Hello, {name}!")
    print(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    return current_time

def fibonacci(n):
    """Calculate Fibonacci sequence up to n terms"""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# Main execution
if __name__ == "__main__":
    print("=" * 50)
    print("Welcome to Python IDE Example Script")
    print("=" * 50)
    
    # Greet the user
    greet_user("Student")
    
    # Calculate Fibonacci
    print("\nFibonacci sequence (first 10 terms):")
    fib_sequence = fibonacci(10)
    print(fib_sequence)
    
    print("\n" + "=" * 50)
    print("Try editing this file and running it again!")