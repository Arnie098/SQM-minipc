import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)

_, o, _ = ssh.exec_command("cat /www/index.html")
html = o.read().decode()

html = html.replace('MBPS', 'KBPS')
html = html.replace('Mbps', 'Kbps')
html = html.replace('mbps', 'kbps')

stdin, _, _ = ssh.exec_command("cat > /www/index.html")
stdin.write(html.encode())
stdin.channel.shutdown_write()

ssh.close()
print("Done")
