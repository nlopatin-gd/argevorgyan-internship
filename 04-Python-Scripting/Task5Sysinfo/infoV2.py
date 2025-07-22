#!/usr/bin/env python3
import platform, argparse, getpass, socket, subprocess, sys, psutil
def distro():
     print("Distro:", platform.platform() if platform.system() != "Linux" else next((l.split('=')[1].strip('"') for l in open("/etc/os-release") if l.startswith("PRETTY_NAME")), "Unknown"))
def memory():
     m = psutil.virtual_memory(); print(f"Memory: Total {m.total//1024//1024} MB | Avail {m.available//1024//1024} MB")
def cpu():
     print("CPU:", platform.processor(), "| Cores (L/P):", psutil.cpu_count(True), "/", psutil.cpu_count(False))
def user():
     print("User:", getpass.getuser())
def load():
     print("Load:", ", ".join(f"{x:.2f}" for x in psutil.getloadavg()))
def ip():
    try:
        ip = subprocess.check_output(["curl", "-s", "ifconfig.me"]).decode().strip()
        print("IP Address:", ip)
    except Exception as e:
        print("Could not get IP address:", e)
p = argparse.ArgumentParser(description="Short System Info Script")
for f, h in zip("dmculi", ["Distro", "Memory", "CPU", "User", "Load", "IP"]): p.add_argument(f"-{f}", action="store_true", help=h)
p.add_argument("--all", action="store_true", help="Show all")
args = p.parse_args()

if not any(vars(args).values()): p.print_help(); sys.exit(1)
if args.all or args.d: distro()
if args.all or args.m: memory()
if args.all or args.c: cpu()
if args.all or args.u: user()
if args.all or args.l: load()
if args.all or args.i: ip()
