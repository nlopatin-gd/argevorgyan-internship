#!/usr/bin/env python3
#Given a list of integers, Remove duplicates and create a tuple. Find min and max  of the tuple.
import sys
numbers = [2, 5, 12, 4, 2, 5, 12, 4, 6, 13, 25, 36]
print("list of numbers:", numbers)
unique_numbers = list(set(numbers))
unique_tuple = tuple(unique_numbers)
print("Unique numbers as tuple:", unique_tuple)
print("Minimum number:", min(unique_tuple))
print("Maximum number:", max(unique_tuple))
sys.exit(0)
