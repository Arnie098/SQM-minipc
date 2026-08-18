import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)
_, o, _ = ssh.exec_command('grep -A 30 "function saveSettings" /www/index.html')
print(o.read().decode())
ssh.close()
