import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)
_, o, _ = ssh.exec_command('top -n 1 | grep "^CPU:" | awk \'{for(i=1;i<=NF;i++) if($i=="idle") print $(i-1)}\'')
print(o.read().decode())
ssh.close()
