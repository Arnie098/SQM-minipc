import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)

script = "sed -i 's/ENABLE SQM \\/ CAKE/ENABLE SQM/g' /www/index.html"
ssh.exec_command(script)
ssh.close()
