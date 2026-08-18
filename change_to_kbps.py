import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.109', username='root', password='admin', timeout=15)

# 1. Update index.html labels
_, o, _ = ssh.exec_command("sed -i 's/DOWNLOAD LIMIT (MBPS)/DOWNLOAD LIMIT (KBPS)/g' /www/index.html")
o.read()
_, o, _ = ssh.exec_command("sed -i 's/UPLOAD LIMIT (MBPS)/UPLOAD LIMIT (KBPS)/g' /www/index.html")
o.read()
_, o, _ = ssh.exec_command("sed -i 's/ Mbps/ Kbps/g' /www/index.html")
o.read()

# 2. Update cgi-bin/sqm-settings
script = """#!/bin/sh

urldecode() {
    printf '%b' "$(printf '%s' "$1" | sed 's/+/ /g; s/%\\([0-9A-Fa-f][0-9A-Fa-f]\\)/\\\\x\\1/g')"
}

get_field() {
    local body="$1" name="$2"
    printf '%s' "$body" | grep -o "${name}=[^&]*" | head -1 | cut -d= -f2-
}

IFACE=$(cat /etc/ramtech-sqm-iface 2>/dev/null)
IFACE=${IFACE:-eth1}
SQM_SECTION=$(uci show sqm 2>/dev/null | grep "\\.interface='${IFACE}'" | sed 's/\\.interface=.*//' | head -1)
[ -z "$SQM_SECTION" ] && SQM_SECTION="sqm.eth1"

if [ "$REQUEST_METHOD" = "POST" ]; then
    BODY=$(dd bs=1 count=$CONTENT_LENGTH 2>/dev/null)
    DL_RAW=$(get_field "$BODY" "download")
    UL_RAW=$(get_field "$BODY" "upload")
    IFACE_NEW=$(get_field "$BODY" "interface")
    ENABLED=$(get_field "$BODY" "enabled")
    BRAND=$(get_field "$BODY" "brand")

    # Values are now in Kbps
    DL_KBPS=$(urldecode "$DL_RAW")
    UL_KBPS=$(urldecode "$UL_RAW")
    
    IFACE_NEW_CLEAN=$(urldecode "$IFACE_NEW" | awk '{print $1}')
    BRAND=$(urldecode "$BRAND")

    [ -z "$DL_KBPS" ] || [ "$DL_KBPS" -lt 100 ] 2>/dev/null && DL_KBPS=10000
    [ -z "$UL_KBPS" ] || [ "$UL_KBPS" -lt 100 ] 2>/dev/null && UL_KBPS=10000
    [ -n "$IFACE_NEW_CLEAN" ] && IFACE="$IFACE_NEW_CLEAN"
    [ -n "$BRAND" ] && printf '%s' "$BRAND" > /etc/ramtech-brand
    printf '%s' "$IFACE" > /etc/ramtech-sqm-iface

    SQM_SECTION="sqm.eth1"

    uci set "${SQM_SECTION}.interface=${IFACE}"
    uci set "${SQM_SECTION}.download=${DL_KBPS}"
    uci set "${SQM_SECTION}.upload=${UL_KBPS}"
    uci set "${SQM_SECTION}.enabled=${ENABLED:-1}"
    uci set "${SQM_SECTION}.qdisc=cake"
    uci set "${SQM_SECTION}.script=piece_of_cake.qos"
    uci set "${SQM_SECTION}.linklayer=ethernet"
    uci set "${SQM_SECTION}.overhead=44"
    uci commit sqm
    /etc/init.d/sqm restart >/dev/null 2>&1

    printf 'Content-Type: application/json\\r\\n\\r\\n'
    printf '{"success":true,"status":"ok","download":%s,"upload":%s,"interface":"%s","enabled":%s}' \
        "$DL_KBPS" "$UL_KBPS" "$IFACE" "${ENABLED:-1}"
else
    # GET request - return raw Kbps values
    DL_K=$(uci get "${SQM_SECTION}.download" 2>/dev/null)
    UL_K=$(uci get "${SQM_SECTION}.upload" 2>/dev/null)
    EN=$(uci get "${SQM_SECTION}.enabled" 2>/dev/null)
    IF=$(uci get "${SQM_SECTION}.interface" 2>/dev/null)
    
    # Don't divide by 1000 anymore
    DL_M=${DL_K:-10000}
    UL_M=${UL_K:-10000}
    BRAND=$(cat /etc/ramtech-brand 2>/dev/null)
    
    IF_UI="$IF"
    [ "$IF" = "eth1" ] && IF_UI="eth1 (WAN)"
    
    printf 'Content-Type: application/json\\r\\n\\r\\n'
    printf '{"download":%s,"upload":%s,"interface":"%s","enabled":%s,"brand":"%s","section":"%s"}' \
        "$DL_M" "$UL_M" "$IF_UI" "${EN:-1}" "${BRAND:-RAMTECH}" "${SQM_SECTION}"
fi
"""

stdin, _, _ = ssh.exec_command("cat > /www/cgi-bin/sqm-settings")
stdin.write(script.encode())
stdin.channel.shutdown_write()
ssh.exec_command("chmod +x /www/cgi-bin/sqm-settings")
ssh.close()
print("Done")
