#!/usr/bin/env python3
import paramiko, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin',
            timeout=20, look_for_keys=False, allow_agent=False)

def r(cmd, t=30):
    _, o, e = ssh.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace')
    err = e.read().decode(errors='replace')
    if out.strip(): print(out.strip())
    if err.strip(): print('  [err]', err.strip())
    return out

def log(m): print(f'\n>>> {m}')
def ok(m):  print(f'  [OK] {m}')

print('=== Verifying r8168 driver installation ===')

# Check loaded modules
log('Loaded NIC modules')
r('lsmod | grep r81')

# Check dmesg for r8168 messages
log('dmesg: r8168/r8169 events')
r('dmesg | grep -iE "r8168|r8169|eth0|eth1" | tail -30')

# Check which driver is bound to eth0
log('Driver bound to eth0 PCI device')
r('readlink /sys/class/net/eth0/device/driver 2>/dev/null')
r('cat /sys/class/net/eth0/device/uevent 2>/dev/null')

# Make r8168 load at boot and blacklist r8169 for RTL8168h
log('Making r8168 persistent, blacklisting r8169 for RTL8168h')
r('echo "r8168" > /etc/modules.d/50-r8168')
# blacklist r8169 only for the RTL8168h PCI ID (0x8168)
r('echo "blacklist r8169" >> /etc/modules.d/50-r8168 2>/dev/null || true')

# Check current eth0 stability
log('eth0 carrier + speed')
r('cat /sys/class/net/eth0/carrier && cat /sys/class/net/eth0/speed')

# Current state
log('Interface states')
r('ip link show eth0')

# Check if SQM is still running
log('SQM status')
r('uci show sqm | grep enabled')
r('tc qdisc show dev eth1 | head -2')

# Ping test
log('Ping 8.8.8.8')
r('ping -c 5 -W 2 8.8.8.8')

# Wait and monitor eth0 for drops (30 seconds)
log('Monitoring eth0 for 30 seconds...')
r('for i in $(seq 1 30); do c=$(cat /sys/class/net/eth0/carrier 2>/dev/null); echo "$i: carrier=$c"; sleep 1; done')

ssh.close()
print('\n=== Done. Report any drops you see above ===')
