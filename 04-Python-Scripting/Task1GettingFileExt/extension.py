#!/usr/bin/env python3
#This script accepts the file name and puts its extension to output if there is no extension an exception shoudl be raised
valid_extensions = [
    '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
    '.mp3', '.wav', '.flac',
    '.mp4', '.avi', '.mov', '.mkv',
    '.py', '.java', '.c', '.cpp', '.js', '.html', '.css',
    '.json', '.xml', '.yml', '.yaml',
    '.zip', '.tar', '.gz', '.rar',
]

filename = input("Enter the file name: ")

try:
    with open(filename):
        pass  # Just testing if the file exists
except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    exit(1)


if '.' in filename and not filename.startswith('.'):
    ext = '.' + filename.rsplit('.', 1)[-1].lower()
    if ext in valid_extensions:
        print(f"Your file extension is: {ext} (valid)")
    else:
        print(f"Your file extension is: {ext} (not in the list, but here it is)")
else:
    raise Exception("No extension found in the file name.")
