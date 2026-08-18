import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)

with open('d:\\\\Ramtech SQM\\\\www\\\\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

stdin, _, _ = ssh.exec_command("cat > /www/index.html")
stdin.write(html.encode('utf-8'))
stdin.channel.shutdown_write()

ssh.close()
print("Done uploading index.html")
