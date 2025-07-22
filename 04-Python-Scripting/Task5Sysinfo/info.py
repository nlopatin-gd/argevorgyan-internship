#!/usr/bin/env python3
# This script accepts user options to display system information
import os
import sys
import argparse
import platform

def distro():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME"):
                    print("Distro:", line.strip().split("=")[1].strip('"'))
                    return
    except:
        print("Could not read distro info.")

def memory():
    print("Memory Info:")
    os.system("echo Total: $(free -h | awk '/^Mem:/ {print $2}'), Free: $(free -h | awk '/^Mem:/ {print $4}')")

def cpu():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    print("CPU:", line.split(":")[1].strip())
                    break
    except:
        print("Could not read CPU info.")

def user():
    os.system("whoami | awk '{print \"User:\", $1}'")

def load():
    os.system("uptime | awk -F'load average:' '{print \"Load average:\", $2}'")

def ip():
    os.system("hostname -I | awk '{print \"IP Address:\", $1}'")

parser = argparse.ArgumentParser(description="Basic system info script") # parser

# help and make arg true if given
parser.add_argument("-d", action="store_true", help="Distro info") 
parser.add_argument("-m", action="store_true", help="Memory info")
parser.add_argument("-c", action="store_true", help="CPU info")
parser.add_argument("-u", action="store_true", help="User info")
parser.add_argument("-l", action="store_true", help="Load average")
parser.add_argument("-i", action="store_true", help="IP address")

args = parser.parse_args()

# execute based on options
if args.d:
    distro()
if args.m:
    memory()
if args.c:
    cpu()
if args.u:
    user()
if args.l:
    load()
if args.i:
    ip()

# If no args given, print help
if not any(vars(args).values()):
    parser.print_help()
    sys.exit(1)
