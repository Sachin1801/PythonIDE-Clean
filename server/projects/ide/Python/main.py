import sys
from datetime import datetime
from typing import List, Dict, Any

def print_section_header(title: str) -> None:
    """Print a formatted section header"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def get_string_input() -> str:
    """Get and validate string input"""
    while True:
        try:
            name = input("Enter your name: ").strip()
            if name:
                return name
            else:
                print("❌ Name cannot be empty. Please try again.")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input cancelled by user.")
            return "Unknown"

def get_integer_input() -> int:
    """Get and validate integer input"""
    while True:
        try:
            age = int(input("Enter your age: "))
            if 0 <= age <= 150:
                return age
            else:
                print("❌ Age must be between 0 and 150.")
        except ValueError:
            print("❌ Please enter a valid integer.")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input cancelled by user.")
            return 0

def get_float_input() -> float:
    """Get and validate float input"""
    while True:
        try:
            height = float(input("Enter your height in meters (e.g., 1.75): "))
            if 0.5 <= height <= 3.0:
                return height
            else:
                print("❌ Height must be between 0.5 and 3.0 meters.")
        except ValueError:
            print("❌ Please enter a valid number.")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input cancelled by user.")
            return 0.0

def get_boolean_input() -> bool:
    """Get and validate boolean input"""
    while True:
        try:
            response = input("Do you like programming? (yes/no or y/n): ").lower().strip()
            if response in ['yes', 'y', 'true', '1']:
                return True
            elif response in ['no', 'n', 'false', '0']:
                return False
            else:
                print("❌ Please enter yes/no or y/n.")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input cancelled by user.")
            return False

def get_list_input() -> List[str]:
    """Get and create a list from user input"""
    try:
        hobbies_str = input("Enter your hobbies (comma-separated): ")
        hobbies = [hobby.strip() for hobby in hobbies_str.split(',') if hobby.strip()]
        return hobbies if hobbies else ["No hobbies entered"]
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Input cancelled by user.")
        return ["Unknown"]

def get_choice_input() -> str:
    """Get choice from predefined options"""
    options = ["Red", "Blue", "Green", "Yellow", "Purple"]
    
    print("\nAvailable colors:")
    for i, color in enumerate(options, 1):
        print(f"  {i}. {color}")
    
    while True:
        try:
            choice = input("Choose your favorite color (1-5): ")
            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]
            else:
                print(f"❌ Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("❌ Please enter a valid number.")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input cancelled by user.")
            return "Unknown"

def demonstrate_error_handling():
    """Demonstrate various error scenarios for IDE testing"""
    print_section_header("ERROR HANDLING DEMONSTRATION")
    
    # Division by zero
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        print(f"✅ Caught ZeroDivisionError: {e}")
    
    # List index error
    try:
        my_list = [1, 2, 3]
        value = my_list[10]
    except IndexError as e:
        print(f"✅ Caught IndexError: {e}")
    
    # Dictionary key error
    try:
        my_dict = {"a": 1, "b": 2}
        value = my_dict["z"]
    except KeyError as e:
        print(f"✅ Caught KeyError: {e}")
    
    # Type error
    try:
        result = "hello" + 5
    except TypeError as e:
        print(f"✅ Caught TypeError: {e}")

def display_user_data(user_data: Dict[str, Any]) -> None:
    """Display user data in multiple formats"""
    print_section_header("USER DATA DISPLAY")
    
    # Simple print
    print("📊 SIMPLE FORMAT:")
    for key, value in user_data.items():
        print(f"  {key}: {value}")
    
    # Formatted strings
    print(f"\n🎯 FORMATTED STRING:")
    print(f"  Hello {user_data['name']}! You are {user_data['age']} years old.")
    print(f"  Height: {user_data['height']:.2f}m")
    print(f"  Programming enthusiast: {'Yes' if user_data['likes_programming'] else 'No'}")
    
    # Table format
    print(f"\n📋 TABLE FORMAT:")
    print(f"{'Property':<20} {'Value':<30}")
    print("-" * 50)
    for key, value in user_data.items():
        print(f"{key.replace('_', ' ').title():<20} {str(value):<30}")
    
    # JSON-like format
    print(f"\n🔧 JSON-LIKE FORMAT:")
    print("{")
    for i, (key, value) in enumerate(user_data.items()):
        comma = "," if i < len(user_data) - 1 else ""
        if isinstance(value, str):
            print(f'  "{key}": "{value}"{comma}')
        elif isinstance(value, list):
            print(f'  "{key}": {value}{comma}')
        else:
            print(f'  "{key}": {value}{comma}')
    print("}")

def main():
    """Main function to orchestrate the testing script"""
    print_section_header("IDE TESTING SCRIPT - MULTIPLE INPUT TYPES")
    print("This script will test various input and output scenarios.")
    print("Press Ctrl+C at any time to cancel input.")
    
    # Collect user data
    print_section_header("DATA COLLECTION")
    
    user_data = {}
    user_data['name'] = get_string_input()
    user_data['age'] = get_integer_input()
    user_data['height'] = get_float_input()
    user_data['likes_programming'] = get_boolean_input()
    user_data['hobbies'] = get_list_input()
    user_data['favorite_color'] = get_choice_input()
    user_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Display collected data
    display_user_data(user_data)
    
    # Demonstrate error handling
    demonstrate_error_handling()
    
    # Test different print scenarios
    print_section_header("OUTPUT TESTING")
    print("🖨️  Testing various output methods:")
    print("   - Standard print() ✅")
    print("   - Formatted f-strings ✅")
    print("   - Multi-line strings ✅")
    print("""   - Triple-quoted strings ✅
   - With line breaks ✅
   - And special characters: !@#$%^&*() ✅""")
    
    # Test with different data types in output
    test_variables = {
        'string': "Hello World",
        'integer': 42,
        'float': 3.14159,
        'boolean': True,
        'list': [1, 2, 3, 4, 5],
        'dict': {'key1': 'value1', 'key2': 'value2'},
        'none': None
    }
    
    print(f"\n🔬 VARIABLE TYPE TESTING:")
    for var_name, var_value in test_variables.items():
        print(f"  {var_name} ({type(var_value).__name__}): {var_value}")
    
    # Final summary
    print_section_header("TESTING COMPLETE")
    print(f"✅ Successfully tested input collection for user: {user_data['name']}")
    print(f"✅ Demonstrated error handling scenarios")
    print(f"✅ Tested multiple output formatting methods")
    print(f"✅ Script completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n🎉 IDE Testing Script finished successfully!")
    print(f"   Total data points collected: {len(user_data)}")
    print(f"   User hobbies count: {len(user_data['hobbies'])}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n❌ Script interrupted by user. Goodbye!")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error occurred: {e}")
        print(f"Error type: {type(e).__name__}")
        sys.exit(1)