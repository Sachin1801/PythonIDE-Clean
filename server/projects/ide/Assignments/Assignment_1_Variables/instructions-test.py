# Assignment 1: Variables and Basic Operations
# Due Date: End of Week 2
# Points: 100

"""
Instructions:
1. Complete all the functions below
2. Test your code with the provided test cases
3. Submit your completed file

Grading:
- Correctness: 70%
- Code style: 20%
- Comments: 10%
"""

def calculate_area(length, width):
    """
    Calculate the area of a rectangle
    
    Args:
        length: The length of the rectangle
        width: The width of the rectangle
    
    Returns:
        The area of the rectangle
    """
    # TODO: Implement this function
    pass

def convert_temperature(celsius):
    """
    Convert Celsius to Fahrenheit
    Formula: F = (C * 9/5) + 32
    
    Args:
        celsius: Temperature in Celsius
    
    Returns:
        Temperature in Fahrenheit
    """
    # TODO: Implement this function
    pass

def find_average(numbers):
    """
    Find the average of a list of numbers
    
    Args:
        numbers: A list of numbers
    
    Returns:
        The average of the numbers
    """
    # TODO: Implement this function
    pass

# Test cases (DO NOT MODIFY)
if __name__ == "__main__":
    # Test calculate_area
    assert calculate_area(5, 3) == 15
    assert calculate_area(10, 10) == 100
    
    # Test convert_temperature
    assert convert_temperature(0) == 32
    assert convert_temperature(100) == 212
    
    # Test find_average
    assert find_average([1, 2, 3, 4, 5]) == 3
    assert find_average([10, 20, 30]) == 20
    
    print("All tests passed! Great job!")
