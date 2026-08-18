import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)
_, o, _ = ssh.exec_command('cat /www/index.html')
with open('d:\\Ramtech SQM\\www_index.html', 'w', encoding='utf-8') as f:
    f.write(o.read().decode())
ssh.close()
