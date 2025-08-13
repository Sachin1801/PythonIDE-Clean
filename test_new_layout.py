#!/usr/bin/env python3
"""
Test file to demonstrate the new IDE layout features.
Run this file to test:
1. Console output below editor
2. Preview panel on the right
3. REPL functionality
4. Word wrap in editor
"""

import matplotlib.pyplot as plt
import numpy as np

def test_console_output():
    """Test console output functionality"""
    print("=== Testing Console Output ===")
    print("This should appear in the console below the editor")
    print("The console should be collapsible with animation")
    
    # Test different output types
    print("INFO: This is an info message")
    print("WARNING: This is a warning")
    print("ERROR: This is an error message")
    
    return "Console test completed"

def test_input():
    """Test input functionality in console"""
    name = input("Enter your name: ")
    print(f"Hello, {name}!")
    
    age = input("Enter your age: ")
    print(f"You are {age} years old")
    
    return f"Input test completed for {name}"

def generate_plot():
    """Generate a plot to test preview panel"""
    print("=== Generating Plot for Preview Panel ===")
    
    # Create sample data
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x)
    y2 = np.cos(x)
    
    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(x, y1, label='sin(x)', linewidth=2)
    plt.plot(x, y2, label='cos(x)', linewidth=2)
    plt.xlabel('X values')
    plt.ylabel('Y values')
    plt.title('Test Plot for Preview Panel')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot
    plt.savefig('test_plot.png', dpi=100, bbox_inches='tight')
    print("Plot saved as 'test_plot.png'")
    print("Open this file to see it in the preview panel on the right")
    
    plt.show()
    return "Plot generated successfully"

def test_long_line():
    """Test word wrap functionality"""
    print("=== Testing Word Wrap ===")
    print("This is a very long line that should demonstrate the word wrap functionality. When word wrap is enabled, this line should wrap to the next line instead of requiring horizontal scrolling. The word wrap toggle button should be in the header menu.")
    
    # Test code with long line
    very_long_variable_name_to_test_word_wrap_in_code_editor = "This is a test of word wrap in the code editor. When enabled, long lines should wrap automatically."
    print(very_long_variable_name_to_test_word_wrap_in_code_editor)
    
    return "Word wrap test completed"

def main():
    """Main function to run all tests"""
    print("=" * 50)
    print("PYTHON IDE NEW LAYOUT TEST")
    print("=" * 50)
    
    # Test console output
    result1 = test_console_output()
    print(f"✓ {result1}")
    
    # Test long lines for word wrap
    result2 = test_long_line()
    print(f"✓ {result2}")
    
    # Generate plot for preview panel
    result3 = generate_plot()
    print(f"✓ {result3}")
    
    # Test input (interactive)
    if input("\nDo you want to test input functionality? (y/n): ").lower() == 'y':
        result4 = test_input()
        print(f"✓ {result4}")
    
    print("\n" + "=" * 50)
    print("ALL TESTS COMPLETED")
    print("Check the following features:")
    print("1. ✓ Console below editor with collapse button")
    print("2. ✓ Clear button in console header")
    print("3. ✓ REPL input area below console output")
    print("4. ✓ Preview panel on the right (draggable)")
    print("5. ✓ Word wrap toggle in header")
    print("6. ✓ Right-click context menu on files")
    print("7. ✓ Dropdown menu next to files")
    print("8. ✓ Double-click to rename files")
    print("9. ✓ Draggable left sidebar")
    print("=" * 50)

if __name__ == "__main__":
    main()