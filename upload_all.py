import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)

def upload_file(local_path, remote_path):
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    stdin, _, _ = ssh.exec_command(f"cat > {remote_path}")
    stdin.write(content.encode('utf-8'))
    stdin.channel.shutdown_write()

upload_file('d:\\\\Ramtech SQM\\\\www\\\\index.html', '/www/index.html')
upload_file('d:\\\\Ramtech SQM\\\\cgi-bin\\\\sqm-settings', '/www/cgi-bin/sqm-settings')
upload_file('d:\\\\Ramtech SQM\\\\cgi-bin\\\\sqm-status', '/www/cgi-bin/sqm-status')

ssh.exec_command('chmod +x /www/cgi-bin/sqm-settings /www/cgi-bin/sqm-status')
ssh.close()
print("Uploaded successfully.")
