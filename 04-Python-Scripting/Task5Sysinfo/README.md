# System Info Script

This script  displays basic system information based on command-line options provided by the user


### Available Options:

| Flag | Description        
|------|--------------------
| `-d` | Show distro info   
| `-m` | Show memory info   
| `-c` | Show CPU info      
| `-u` | Show current user  
| `-l` | Show load average  
| `-i` | Show IP address    
| `--all` | Show all (Only in V2)

### Example V1:

![exwsl](scr1.png)
![exvm](scr2.png)

### Example V2:
![exwsl](scr3.png)
![exvm](scr4.png)


If no options are provided, the script will show a helpful usage message.

## Requirements

- Python 3
- Unix-like operating system (uses `/etc/os-release`, `free`, `uptime`, etc.)



