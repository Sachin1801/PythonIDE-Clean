# Test error handling and try/except blocks
def safe_divide(a, b):
    try:
        result = a / b
        return f"{a} / {b} = {result}"
    except ZeroDivisionError:
        return "Error: Cannot divide by zero!"
    except Exception as e:
        return f"Error: {str(e)}"

print(safe_divide(10, 2))
print(safe_divide(10, 0))