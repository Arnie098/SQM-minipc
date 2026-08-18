import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)

# Start busy loop
ssh.exec_command('sh -c "while true; do :; done" & echo $! > /tmp/busy.pid')
time.sleep(2)

# Check top
_, o, _ = ssh.exec_command('top -n 1 | grep "^CPU:" | awk \'{for(i=1;i<=NF;i++) if($i=="idle") print $(i-1)}\'')
print("Idle after loop:", o.read().decode().strip())

# Kill busy loop
ssh.exec_command('kill $(cat /tmp/busy.pid)')
ssh.close()
