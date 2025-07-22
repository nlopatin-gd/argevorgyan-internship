#!/usr/bin/env python3
# Given a list of integers, remove duplicates
# create a tuple, and find min and max of the tuple.

import sys

def rmdups_preserve_order(numbers):
    seen = set()         # To keep track of numbers already encountered
    unique_numbers = []  # List to store numbers in original order without duplicates

    for num in numbers:
        if num not in seen:      # num is not in seen 
            unique_numbers.append(num)  # Add it to result list
            seen.add(num)              
    return unique_numbers

def main():
    numbers = [2, 5, 12, 4, 2, 5, 12, 4, 6, 13, 25, 36]
    print("List of numbers:", numbers)

    unique_numbers = rmdups_preserve_order(numbers)
    unique_tuple = tuple(unique_numbers)  # Convert list to tuple

    print("Unique numbers:", unique_tuple)
    print("Minimum number:", min(unique_tuple))
    print("Maximum number:", max(unique_tuple))
    sys.exit(0)
if __name__ == "__main__":
    main()
