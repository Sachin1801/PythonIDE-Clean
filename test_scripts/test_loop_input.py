# Test 4: Input in Loop
print("Number Guessing Game")
print("-" * 30)

import random
secret = random.randint(1, 50)
attempts = 0
max_attempts = 5

print(f"I'm thinking of a number between 1 and 50")
print(f"You have {max_attempts} attempts to guess it!")

while attempts < max_attempts:
    attempts += 1
    guess_str = input(f"Attempt {attempts}/{max_attempts} - Enter your guess: ")

    try:
        guess = int(guess_str)

        if guess == secret:
            print(f"🎉 Correct! The number was {secret}")
            print(f"You got it in {attempts} attempts!")
            break
        elif guess < secret:
            print("Too low! Try a higher number.")
        else:
            print("Too high! Try a lower number.")

        if attempts < max_attempts:
            print(f"You have {max_attempts - attempts} attempts left.")

    except ValueError:
        print(f"'{guess_str}' is not a valid number. Try again.")

else:
    print(f"\n😔 Sorry! The number was {secret}")
    print("Better luck next time!")

print("\nGame Over!")
print(f"Variables in REPL: secret={secret}, attempts={attempts}")