#!/usr/bin/env python3
# This script reads a log file and counts unique user agents
import sys

try:
    lines = open(sys.argv[1]).readlines()  # Read file lines
except:
    print("Usage: script.py <access_log_file>")  # Show usage message
    sys.exit(1)

usercount = {}  # dict for user counts

for line in lines:
    useragent = line.split('"')[-2]  # extract user agent
    usercount[useragent] = usercount.get(useragent, 0) + 1  # increment count

print(f"\nTotal unique User Agents: {len(usercount)}\n")  # total count
# Sort user agents by count 
for useragent in sorted(usercount, key=usercount.get, reverse=True):
    print(usercount[useragent], " -", useragent)  # 
    
if len(usercount) == 0:
    print("No user agents found in the log file.")  # check empty
    sys.exit(0)  
    