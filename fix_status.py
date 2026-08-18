import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)

script = """
sed -i 's/DL_MBPS=$((DL_KBPS \\/ 1000))/DL_MBPS=${DL_KBPS:-0}/g' /www/cgi-bin/sqm-status
sed -i 's/UL_MBPS=$((UL_KBPS \\/ 1000))/UL_MBPS=${UL_KBPS:-0}/g' /www/cgi-bin/sqm-status
"""
ssh.exec_command(script)
ssh.close()
