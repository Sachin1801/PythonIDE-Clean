# Test file for Hybrid REPL with input() functionality
# This demonstrates how input() works during script execution
# and how the variables are available in REPL mode afterward

print("Testing input() with Hybrid REPL")
print("-" * 40)

# Get user's name
name = input("What is your name? ")
print(f"Hello, {name}!")

# Get user's age
age_str = input("How old are you? ")
try:
    age = int(age_str)
    print(f"You are {age} years old.")
    
    # Calculate something based on input
    birth_year = 2024 - age
    print(f"You were likely born in {birth_year}")
except ValueError:
    print(f"'{age_str}' is not a valid age!")
    age = None
    birth_year = None

# Get user's favorite color
color = input("What's your favorite color? ")
print(f"Nice! {color} is a great color!")

# Create a dictionary with all the collected data
user_data = {
    "name": name,
    "age": age,
    "birth_year": birth_year,
    "favorite_color": color
}

print("\n" + "=" * 40)
print("Summary of collected data:")
for key, value in user_data.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 40)
print("Script execution completed!")
print("All variables are now available in REPL mode:")
print("  - name: your entered name")
print("  - age: your age as integer (if valid)")
print("  - birth_year: calculated birth year")
print("  - color: your favorite color")
print("  - user_data: dictionary with all data")
print("\nTry typing these variable names in the REPL!")