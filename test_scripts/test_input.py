# Test 2: Input Function Testing
print("Testing input() function in new REPL")
print("-" * 40)

name = input("What is your name? ")
print(f"Hello, {name}!")

age = input("How old are you? ")
print(f"You are {age} years old.")

# Calculate birth year
birth_year = 2024 - int(age)
print(f"You were born around {birth_year}")

favorite_color = input("What's your favorite color? ")
print(f"Nice! {favorite_color} is a great color!")

print("\nScript complete!")
print("Variables available in REPL: name, age, birth_year, favorite_color")

# After script, try in REPL:
# >>> print(f"Summary: {name} is {age} years old and likes {favorite_color}")