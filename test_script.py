"""
Name: Nicole Akmetov
Assignment: 8
Problem: 1
"""

from datetime import datetime

file_obj = open("Akmetov_user_entries.txt", "w")

def phone_num_entry():
    entry = input("Enter numbers and enter Q to stop:")

    with open("Akmetov_user_entries.txt", "w") as file_obj:
        while entry.upper() != "Q":
            file_obj.write(entry + "\n")
            entry = input("Enter numbers and enter Q to stop:")

file_obj = open("Akmetov_formatted_numbers.txt", "w")

def format_num_entry():
    numbers = []
    with open("Akmetov_user_entries.txt", "r") as file_obj:
        for p in file_obj:
            numbers.append(p.strip())

    with open("Akmetov_formatted_numbers.txt", "w") as file_obj:
        for num in numbers:
            if len(num) == 10 and num.isdigit():
                phone = "(" + num[0:3] + ")" + num[3:6] + "-" + num[6:10]
                file_obj.write(phone + "\n")
