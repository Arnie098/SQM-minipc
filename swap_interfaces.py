import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)

script = """
# Swap WAN and LAN interfaces
uci set network.@device[0].ports='eth1'
uci set network.wan.device='eth0'
uci set network.wan6.device='eth0'
uci commit network

# Update SQM Interface
uci set sqm.eth1.interface='eth0'
uci commit sqm

# Update Dashboard Default Interface
echo 'eth0' > /etc/ramtech-sqm-iface

# Also fix the dashboard UI default string if it had one hardcoded
sed -i 's/eth1 (WAN)/eth0 (WAN)/g' /www/index.html
sed -i 's/interface="eth1"/interface="eth0"/g' /www/index.html

# We will run network restart in the background so SSH can close cleanly
(sleep 2 && /etc/init.d/network restart && /etc/init.d/sqm restart) &
"""

ssh.exec_command(script)
print("Swap initiated.")
ssh.close()
