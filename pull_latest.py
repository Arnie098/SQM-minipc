import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)

# Download index.html
_, o, _ = ssh.exec_command('cat /www/index.html')
with open('d:\\Ramtech SQM\\www\\index.html', 'w', encoding='utf-8', newline='\n') as f:
    f.write(o.read().decode())

# Download cgi-bin/sqm-settings
_, o, _ = ssh.exec_command('cat /www/cgi-bin/sqm-settings')
with open('d:\\Ramtech SQM\\cgi-bin\\sqm-settings', 'w', encoding='utf-8', newline='\n') as f:
    f.write(o.read().decode())

# Download cgi-bin/traffic
_, o, _ = ssh.exec_command('cat /www/cgi-bin/traffic')
with open('d:\\Ramtech SQM\\cgi-bin\\traffic', 'w', encoding='utf-8', newline='\n') as f:
    f.write(o.read().decode())

# Download cgi-bin/sqm-status
_, o, _ = ssh.exec_command('cat /www/cgi-bin/sqm-status')
with open('d:\\Ramtech SQM\\cgi-bin\\sqm-status', 'w', encoding='utf-8', newline='\n') as f:
    f.write(o.read().decode())

ssh.close()
print("Downloaded latest files from router.")
