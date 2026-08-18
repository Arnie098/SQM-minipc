#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko, os, time

ROUTER = "192.168.0.109"
USER   = "root"
PASS   = "admin"
PORT   = 22

D = os.path.dirname(os.path.abspath(__file__))

FILES = {
    "/www/cgi-bin/traffic":       os.path.join(D, "cgi-bin", "traffic"),
    "/www/cgi-bin/sqm-status":    os.path.join(D, "cgi-bin", "sqm-status"),
    "/www/cgi-bin/sqm-settings":  os.path.join(D, "cgi-bin", "sqm-settings"),
    "/www/index.html":            os.path.join(D, "www",     "index.html"),
}

def run(ssh, cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    if out.strip(): print(out.strip())
    if err.strip(): print("  [err]", err.strip())
    return out

def upload(ssh, local_path, remote_path):
    """Pipe raw file bytes directly into 'cat > remote' — no encoding needed."""
    data = open(local_path, "rb").read()
    stdin, stdout, stderr = ssh.exec_command(f"cat > {remote_path}", timeout=30)
    stdin.write(data)
    stdin.channel.shutdown_write()
    stdout.read()  # wait for cat to finish
    err = stderr.read().decode(errors='replace').strip()
    if err:
        print(f"  [err] {err}")
    # Verify file size
    _, vout, _ = ssh.exec_command(f"wc -c < {remote_path}")
    size = vout.read().decode().strip()
    print(f"  [OK] {os.path.basename(local_path)} -> {remote_path}  ({size} bytes)")

def ok(msg):  print(f"  [OK] {msg}")
def log(msg): print(f"\n>>> {msg}")

print("\n=== RAMTECH SQM Deployer ===")

# ── Connect ──────────────────────────────────────────────────────────────────
log(f"Connecting to {USER}@{ROUTER}:{PORT}")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(ROUTER, port=PORT, username=USER, password=PASS,
                timeout=15, look_for_keys=False, allow_agent=False)
    ok(f"Connected as {USER}")
except Exception as e:
    print(f"Connection failed: {e}"); sys.exit(1)

# ── System info ───────────────────────────────────────────────────────────────
log("System info")
run(ssh, "uname -a")
run(ssh, "cat /etc/openwrt_release 2>/dev/null || cat /etc/os-release 2>/dev/null | head -4")
run(ssh, "echo PATH=$PATH")
# Try to find opkg
run(ssh, "which opkg 2>/dev/null || find / -name opkg -type f 2>/dev/null | head -3")

# ── Upload files via stdin pipe (no base64 needed) ───────────────────────────
log("Uploading files (stdin pipe -> cat)")
run(ssh, "mkdir -p /www/cgi-bin")

for remote, local in FILES.items():
    upload(ssh, local, remote)

# ── Permissions ───────────────────────────────────────────────────────────────
log("Setting permissions")
run(ssh, "chmod +x /www/cgi-bin/traffic /www/cgi-bin/sqm-status /www/cgi-bin/sqm-settings")
run(ssh, "chmod 644 /www/index.html")
run(ssh, "printf 'RAMTECH' > /etc/ramtech-brand && printf 'eth1' > /etc/ramtech-sqm-iface")
ok("Permissions set")

# ── SQM packages ─────────────────────────────────────────────────────────────
log("Checking SQM packages")
# Try multiple opkg paths
opkg_paths = ["/bin/opkg", "/usr/bin/opkg", "opkg"]
opkg = None
for p in opkg_paths:
    out = run(ssh, f"test -x {p} 2>/dev/null && echo YES || echo NO")
    if "YES" in out:
        opkg = p
        break

if opkg:
    out = run(ssh, f"{opkg} list-installed 2>/dev/null | grep sqm-scripts")
    if "sqm-scripts" not in out:
        print("  -> Installing SQM packages...")
        run(ssh, f"{opkg} update 2>&1 | tail -2", timeout=120)
        run(ssh, f"{opkg} install sqm-scripts kmod-sched-cake 2>&1 | tail -5", timeout=120)
    ok("SQM packages ready")
else:
    print("  [!] opkg not found — skipping package install (may already be installed)")

# ── UCI config ────────────────────────────────────────────────────────────────
log("Configuring UCI")
cmds = [
    "uci -q set firewall.@defaults[0].flow_offloading=0",
    "uci -q set firewall.@defaults[0].flow_offloading_hw=0",
    "uci commit firewall 2>/dev/null",
    "uci -q set network.globals.packet_steering=1",
    "uci commit network 2>/dev/null",
    "uci -q get sqm.@queue[0] >/dev/null 2>&1 || uci add sqm queue >/dev/null 2>&1",
    "uci -q set sqm.@queue[0].interface=eth1",
    "uci -q set sqm.@queue[0].download=100000",
    "uci -q set sqm.@queue[0].upload=100000",
    "uci -q set sqm.@queue[0].enabled=1",
    "uci -q set sqm.@queue[0].qdisc=cake",
    "uci -q set sqm.@queue[0].script=piece_of_cake.qos",
    "uci -q set sqm.@queue[0].linklayer=none",
    "uci commit sqm 2>/dev/null",
]
for c in cmds:
    run(ssh, c)
ok("UCI configured")

# ── Services ──────────────────────────────────────────────────────────────────
log("Restarting services")
run(ssh, "/etc/init.d/sqm enable 2>/dev/null; /etc/init.d/sqm restart 2>/dev/null && echo sqm_ok || echo sqm_skipped")
run(ssh, "/etc/init.d/uhttpd restart && echo uhttpd_ok")
ok("Services done")

# ── Verify ────────────────────────────────────────────────────────────────────
log("Verifying CGI endpoints")
time.sleep(2)

# Try wget (busybox has it even if curl is missing)
for ep, key in [("/cgi-bin/traffic","rx"), ("/cgi-bin/sqm-status","cpu")]:
    out = run(ssh, f"wget -q -O - http://localhost{ep} 2>/dev/null || "
                   f"curl -sf http://localhost{ep} 2>/dev/null || echo UNREACHABLE")
    if key in out:
        ok(f"{ep} -> {out.strip()[:80]}")
    else:
        print(f"  [!] {ep}: {out.strip()[:80] or '(empty)'}")

# Check file sizes on disk
log("File sizes on router")
run(ssh, "ls -la /www/index.html /www/cgi-bin/traffic /www/cgi-bin/sqm-status /www/cgi-bin/sqm-settings")

ssh.close()
print(f"""
=== DEPLOY COMPLETE ===
  Dashboard : http://{ROUTER}/
  LuCI      : http://{ROUTER}/cgi-bin/luci
""")
