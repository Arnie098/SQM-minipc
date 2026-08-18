#!/usr/bin/env python3
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15, look_for_keys=False, allow_agent=False)
def r(cmd):
    _, o, _ = ssh.exec_command(cmd, timeout=30)
    return o.read().decode(errors='replace')

print('=== SQM CONFIG ===')
print(r('uci show sqm'))

print('\n=== NETWORK GLOBALS ===')
print(r('uci show network.globals'))

print('\n=== DMESG ===')
print(r('dmesg | grep -iE "eth0|r8169|sqm|cake" | tail -40'))

print('\n=== ETHTOOL OFFLOADS ===')
print(r('ethtool -k eth0 | grep -E "on|off"'))

ssh.close()
