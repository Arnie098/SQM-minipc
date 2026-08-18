#!/usr/bin/env python3
import paramiko, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin',
            timeout=15, look_for_keys=False, allow_agent=False)

def r(cmd, t=30):
    _, o, e = ssh.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace')
    err = e.read().decode(errors='replace')
    if out.strip(): print(out.strip())
    if err.strip(): print('  [err]', err.strip())
    return out

def log(m): print(f'\n>>> {m}')
def ok(m):  print(f'  [OK] {m}')

print('=== SQM Disable Test ===')

# Check current drop frequency first
log('Current dmesg eth0 events')
r('dmesg | grep eth0 | tail -20')

log('Current interface drop counters')
r('cat /proc/net/dev')

# Disable SQM completely
log('Stopping SQM entirely')
r('/etc/init.d/sqm stop 2>&1')
r('uci set sqm.eth1.enabled=0')
r('uci commit sqm')
ok('SQM stopped and disabled')

# Remove ALL qdiscs manually to be sure
log('Removing all custom qdiscs from eth1')
r('tc qdisc del dev eth1 root 2>/dev/null && echo "removed root qdisc" || echo "no root qdisc to remove"')
r('tc qdisc del dev eth1 ingress 2>/dev/null && echo "removed ingress" || echo "no ingress to remove"')

# Remove the IFB device entirely
log('Removing IFB device')
r('ip link set ifb4eth1 down 2>/dev/null; ip link del ifb4eth1 2>/dev/null && echo "ifb removed" || echo "no ifb to remove"')

# Restore default pfifo_fast on eth1
log('Restoring default qdisc on eth1')
r('tc qdisc add dev eth1 root pfifo_fast && echo "pfifo_fast restored" || echo "already default"')

# Verify clean state
log('Verify: qdiscs after cleanup')
r('tc qdisc show dev eth1')
r('ip link show ifb4eth1 2>/dev/null || echo "ifb4eth1 gone — good"')

# Force PCIe power management to ON for both NICs (keep active, prevent sleep)
log('Force PCIe devices active (prevent ASPM sleep)')
r('echo on > /sys/bus/pci/devices/0000:01:00.0/power/control && echo "eth0 PCI power=on" || echo "failed"')
r('echo on > /sys/bus/pci/devices/0000:02:00.0/power/control && echo "eth1 PCI power=on" || echo "failed"')

# Ping test
log('Ping 8.8.8.8 (SQM disabled, no shaping)')
r('ping -c 5 -W 2 8.8.8.8')

log('eth0 carrier + speed')
r('cat /sys/class/net/eth0/carrier && cat /sys/class/net/eth0/speed')

ssh.close()
print('''
=== SQM is now completely OFF ===

ACTION REQUIRED:
1. Wait 2-3 minutes and watch if eth0 is stable (no more link drops on console)
2. Run the Waveform bufferbloat test at: https://www.waveform.com/tools/bufferbloat

EXPECTED RESULTS:
  - If test PASSES (connection stays stable): SQM CAKE is causing the drops
    -> We will use a lighter QoS method (fq_codel) that wont crash the NIC
  - If test STILL FAILS (connection still drops): Hardware/ASPM issue
    -> Need to disable ASPM in BIOS or swap the LAN NIC

Tell me which result you get!
''')
