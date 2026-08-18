# RAMTECH SQM — SSH deploy via plink (no interactive password prompt)
param(
    [string]$Router = "192.168.0.109",
    [string]$User   = "root",
    [string]$Pass   = "thea"
)

$D     = Split-Path -Parent $MyInvocation.MyCommand.Definition
$plink = "$env:TEMP\plink.exe"

function B64([string]$path) {
    [Convert]::ToBase64String([IO.File]::ReadAllBytes($path))
}

function SSH([string]$cmd) {
    & $plink -ssh -pw $Pass -batch -no-antispoof "${User}@${Router}" $cmd
}

Write-Host "Reading and encoding local files..." -ForegroundColor Cyan
$t  = B64 "$D\cgi-bin\traffic"
$s  = B64 "$D\cgi-bin\sqm-status"
$se = B64 "$D\cgi-bin\sqm-settings"
$h  = B64 "$D\www\index.html"

Write-Host "Connecting to ${User}@${Router} via plink..." -ForegroundColor Cyan

# All in one remote session
$remoteScript = @"
set -e
echo '[1/5] Directories'
mkdir -p /www/cgi-bin

echo '[2/5] Writing CGI scripts'
printf '%s' '$t'  | base64 -d > /www/cgi-bin/traffic
printf '%s' '$s'  | base64 -d > /www/cgi-bin/sqm-status
printf '%s' '$se' | base64 -d > /www/cgi-bin/sqm-settings

echo '[3/5] Writing dashboard'
printf '%s' '$h' | base64 -d > /www/index.html

echo '[4/5] Permissions + brand defaults'
chmod +x /www/cgi-bin/traffic /www/cgi-bin/sqm-status /www/cgi-bin/sqm-settings
chmod 644 /www/index.html
printf 'RAMTECH' > /etc/ramtech-brand
printf 'eth1'    > /etc/ramtech-sqm-iface

echo '[5/5] SQM config + services'
if ! opkg list-installed 2>/dev/null | grep -q sqm-scripts; then
  echo '  -> Installing sqm-scripts...'
  opkg update && opkg install sqm-scripts kmod-sched-cake luci-app-sqm
fi

uci -q set firewall.@defaults[0].flow_offloading=0
uci -q set firewall.@defaults[0].flow_offloading_hw=0
uci commit firewall 2>/dev/null || true
uci -q set network.globals.packet_steering=1
uci commit network 2>/dev/null || true

uci -q get sqm.@queue[0] >/dev/null 2>&1 || uci add sqm queue >/dev/null 2>&1
uci -q set sqm.@queue[0].interface=eth1
uci -q set sqm.@queue[0].download=100000
uci -q set sqm.@queue[0].upload=100000
uci -q set sqm.@queue[0].enabled=1
uci -q set sqm.@queue[0].qdisc=cake
uci -q set sqm.@queue[0].script=piece_of_cake.qos
uci -q set sqm.@queue[0].linklayer=none
uci commit sqm 2>/dev/null || true
/etc/init.d/sqm enable  2>/dev/null || true
/etc/init.d/sqm restart 2>/dev/null || true
/etc/init.d/uhttpd restart

echo ''
echo '=============================='
echo ' DEPLOY COMPLETE'
echo " Dashboard: http://$Router/"
echo '=============================='
"@

$remoteScript | & $plink -ssh -pw $Pass -batch "${User}@${Router}"
