#!/usr/bin/env python3
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15, look_for_keys=False, allow_agent=False)

def r(cmd, t=30):
    _, o, e = ssh.exec_command(cmd, timeout=t)
    return o.read().decode(errors='replace') + e.read().decode(errors='replace')

print("=== Router Cleanup ===")

# Remove kmod-r8168
print("Removing kmod-r8168...")
print(r("apk del kmod-r8168 2>/dev/null || opkg remove kmod-r8168 2>/dev/null"))

# Remove blacklist
print("Removing r8168 blacklist/configs...")
print(r("rm -f /etc/modules.d/50-r8168"))
print(r("rm -f /etc/modules.d/30-r8169"))

# Remove hotplug scripts
print("Removing temporary hotplug scripts...")
print(r("rm -f /etc/hotplug.d/iface/13-eth0-fix"))
print(r("rm -f /etc/hotplug.d/iface/12-sqm-tune"))

# Ensure r8169 is loaded
print("Loading r8169 driver...")
print(r("modprobe r8169"))

print("=== Done ===")
ssh.close()
