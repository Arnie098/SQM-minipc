#!/usr/bin/env python3
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin',
            timeout=15, look_for_keys=False, allow_agent=False)

def r(cmd, t=30):
    _, o, e = ssh.exec_command(cmd, timeout=t)
    return o.read().decode(errors='replace')

print('=== WAN MONITOR LOG ===')
print(r('cat /tmp/wan-monitor.log'))

print('\n=== DMESG eth0/eth1 events ===')
print(r('dmesg | grep -E "eth0|eth1" | tail -30'))

print('\n=== CURRENT STATE ===')
print(r('ip route show'))
print(r('ip addr show eth1'))
print(r('cat /sys/class/net/eth0/carrier && cat /sys/class/net/eth1/carrier'))

# Stop the monitor
r('kill $(cat /tmp/wan-monitor.pid 2>/dev/null) 2>/dev/null')

ssh.close()
