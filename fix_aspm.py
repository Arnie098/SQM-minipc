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

print('=== Post-reboot ASPM check ===')

# Check if pcie_aspm=force took effect
log('Kernel cmdline (verify pcie_aspm=force)')
r('cat /proc/cmdline')

# Try setting ASPM policy now (should work with pcie_aspm=force)
log('Setting ASPM policy to performance')
out = r('echo performance > /sys/module/pcie_aspm/parameters/policy 2>/dev/null && echo ASPM_POLICY_SET || echo ASPM_STILL_LOCKED')
aspm_worked = 'ASPM_POLICY_SET' in out

log('Current ASPM policy')
r('cat /sys/module/pcie_aspm/parameters/policy 2>/dev/null || echo not_readable')

# Force PCIe devices to active (D0) state
log('Force PCIe NICs to active power state')
r('echo on > /sys/bus/pci/devices/0000:01:00.0/power/control && echo eth0_D0_active')
r('echo on > /sys/bus/pci/devices/0000:02:00.0/power/control && echo eth1_D0_active')

# Check dmesg for ASPM messages and eth0 drops
log('DMESG: ASPM + eth0 events since boot')
r('dmesg | grep -iE "aspm|eth0|r8169" | tail -20')

# Re-enable SQM (now that ASPM should be fixed)
log('Re-enabling SQM with CAKE at 90 Mbps')
r('uci set sqm.eth1.enabled=1')
r('uci set sqm.eth1.download=90000')
r('uci set sqm.eth1.upload=90000')
r('uci set sqm.eth1.linklayer=ethernet')
r('uci set sqm.eth1.overhead=44')
r('uci commit sqm')
r('/etc/init.d/sqm restart 2>&1')
time.sleep(2)

# Verify CAKE is running
log('CAKE qdisc verify')
r('tc qdisc show dev eth1')
r('tc qdisc show dev ifb4eth1 2>/dev/null')

# Final ping test
log('Ping 8.8.8.8')
r('ping -c 5 -W 2 8.8.8.8')

log('eth0 carrier')
r('cat /sys/class/net/eth0/carrier && cat /sys/class/net/eth0/speed')

ssh.close()

if aspm_worked:
    print('''
=== ASPM FIXED! SQM RE-ENABLED ===
pcie_aspm=force is working — OS now controls ASPM.
ASPM policy set to performance (NICs never sleep).
SQM CAKE is back at 90 Mbps upload + 90 Mbps download.

-> Run the Waveform bufferbloat test now.
   The connection should stay stable and you should get an A grade!
''')
else:
    print('''
=== ASPM STILL LOCKED BY BIOS ===
The BIOS is preventing OS control of ASPM.

Options:
1. Enter BIOS/UEFI and disable ASPM or set to L0s only
2. Or accept SQM with occasional 3s dropouts (every 1-5 min)
   -> The drops are hardware, not software

SQM has been re-enabled regardless.
''')
