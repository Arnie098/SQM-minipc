import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)
_, o, _ = ssh.exec_command('cat /www/index.html')
html = o.read().decode()
lines = html.splitlines()
start = -1
for i, line in enumerate(lines):
    if "saveSettings" in line:
        start = i
        break
if start != -1:
    print('\n'.join(lines[start:start+40]))
ssh.close()
