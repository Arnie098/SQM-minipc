import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)
ssh.exec_command('sed -i \'s/"status":"ok"/"success":true,"status":"ok"/g\' /www/cgi-bin/sqm-settings')
ssh.close()
