#!/usr/bin/env python3
#This script counts occurrences of all characters within a string
str_input = input("Enter a string: ") # input string
seen = set() # avoiding printing duplicates
print(f"You entered: {str_input}") 

for char in str_input: 
    if char == ' ': #skip spaces
        continue
    if char not in seen: # check if character has been seen before 
        
        print(f"{char}: {str_input.count(char)}") #count occurrences
        seen.add(char) 