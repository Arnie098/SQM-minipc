import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)
_, o, e = ssh.exec_command('REQUEST_METHOD=POST CONTENT_LENGTH=71 /www/cgi-bin/sqm-settings <<EOF\ndownload=10240&upload=10240&interface=eth1%20%28WAN%29&enabled=1&brand=\nEOF')
print("STDOUT:", o.read().decode())
print("STDERR:", e.read().decode())
ssh.close()
