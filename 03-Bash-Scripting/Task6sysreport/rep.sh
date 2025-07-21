#!/bin/bash
REPORT_FILE="system_report.txt"

# title
echo "===== System Report =====" >> "$REPORT_FILE"

#  info
echo "Date and Time       : $(date)" >> "$REPORT_FILE"
echo "Current User        : $(whoami)" >> "$REPORT_FILE"
echo "Hostname            : $(hostname)" >> "$REPORT_FILE"
echo "Internal IP Address : $(hostname -I | awk '{print $1}')" >> "$REPORT_FILE"
echo "External IP Address : $(curl -s ifconfig.me || echo 'Unavailable')" >> "$REPORT_FILE"
echo "Distribution        : $(source /etc/os-release && echo "$NAME $VERSION")" >> "$REPORT_FILE"
echo "System Uptime       : $(uptime -p)" >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"

echo "Disk Usage on '/'   : Used: $(df -h / | awk 'NR==2 {print $3}'), Free: $(df -h / | awk 'NR==2 {print $4}')" >> "$REPORT_FILE"
echo "RAM Info            : Total: $(free -h | awk '/^Mem:/ {print $2}'), Free: $(free -h | awk '/^Mem:/ {print $4}')" >> "$REPORT_FILE"
echo "CPU Cores           : $(nproc)" >> "$REPORT_FILE"
echo "CPU mhz             : $(grep "cpu MHz" /proc/cpuinfo | head -n 1 | awk '{print $4, "MHz"}')" >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"

# Append the footer
echo "=========================" >> "$REPORT_FILE"

echo "System report saved to $REPORT_FILE"