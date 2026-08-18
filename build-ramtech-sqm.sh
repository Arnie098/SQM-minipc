#!/bin/bash
# ============================================================
#  RAMTECH SQM – OpenWrt x86/64 Image Builder
#  Run on Ubuntu 20.04 / 22.04 / 24.04 or Debian 11/12
#  Usage:  bash build-ramtech-sqm.sh
# ============================================================
set -euo pipefail

OWRT_VER="23.05.5"
TARGET="x86/64"
PROFILE="x86_64"
BUILDER_NAME="openwrt-imagebuilder-${OWRT_VER}-x86-64.Linux-x86_64"
BUILDER_FILE="${BUILDER_NAME}.tar.xz"
BUILDER_URL="https://downloads.openwrt.org/releases/${OWRT_VER}/targets/${TARGET}/${BUILDER_FILE}"
BUILD_DIR="./openwrt-builder"
DIST_DIR="./dist"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

PACKAGES="
  luci luci-ssl-nginx
  luci-app-sqm sqm-scripts kmod-sched-cake kmod-sched-fq-codel
  ip-full iptables kmod-ipt-conntrack
  curl wget-ssl
  -dnsmasq dnsmasq-full
  nano htop tcpdump
"

banner() { printf '\n\033[1;36m%s\033[0m\n' "$*"; }
ok()     { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }
err()    { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; }

banner "RAMTECH SQM — OpenWrt ${OWRT_VER} Image Builder"
printf "Target : %s | Profile: %s\n\n" "$TARGET" "$PROFILE"

# Check host deps
for cmd in wget make tar; do
  command -v "$cmd" >/dev/null 2>&1 || { err "Missing: $cmd. Run: sudo apt install wget make tar"; exit 1; }
done

mkdir -p "$BUILD_DIR" "$DIST_DIR"
cd "$BUILD_DIR"

# 1 ── Download Image Builder
banner "[1/4] Image Builder"
if [ ! -f "$BUILDER_FILE" ]; then
  wget -q --show-progress "$BUILDER_URL" -O "$BUILDER_FILE"
else
  ok "Already downloaded — skipping"
fi

# 2 ── Extract
banner "[2/4] Extracting"
if [ ! -d "$BUILDER_NAME" ]; then
  tar -xJf "$BUILDER_FILE"
  ok "Extracted $BUILDER_NAME"
else
  ok "Already extracted — skipping"
fi

cd "$BUILDER_NAME"

# 3 ── Inject custom files
banner "[3/4] Injecting custom files"
mkdir -p files/www/cgi-bin \
         files/etc/uci-defaults

# CGI backend scripts
cp "$SCRIPT_DIR/cgi-bin/traffic"       files/www/cgi-bin/traffic
cp "$SCRIPT_DIR/cgi-bin/sqm-status"    files/www/cgi-bin/sqm-status
cp "$SCRIPT_DIR/cgi-bin/sqm-settings"  files/www/cgi-bin/sqm-settings
chmod +x files/www/cgi-bin/*

# Dashboard
cp "$SCRIPT_DIR/www/index.html"        files/www/index.html

# First-boot config
cp "$SCRIPT_DIR/uci-defaults/99-ramtech-sqm" files/etc/uci-defaults/99-ramtech-sqm
chmod +x files/etc/uci-defaults/99-ramtech-sqm

# Brand defaults
printf 'RAMTECH' > files/etc/ramtech-brand
printf 'eth1'    > files/etc/ramtech-sqm-iface

ok "Files injected"

# 4 ── Build
banner "[4/4] Building image  (10–15 min)"
make image \
  PROFILE="$PROFILE" \
  PACKAGES="$(echo $PACKAGES)" \
  FILES="files" \
  2>&1 | tee ../../build.log

# Copy output images
banner "Copying images to $DIST_DIR"
for fmt in ext4-combined-efi squashfs-combined-efi; do
  SRC=$(find bin/targets/x86/64/ -name "*${fmt}.img.gz" | head -1)
  if [ -n "$SRC" ]; then
    DEST="../../$DIST_DIR/ramtech-sqm-${OWRT_VER}-x86-64-${fmt}.img.gz"
    cp "$SRC" "$DEST"
    ok "${fmt}: dist/$(basename "$DEST")"
  fi
done

cat <<EOF

╔══════════════════════════════════════════════════════════╗
║  BUILD COMPLETE — flash one of the images in ./dist/    ║
║                                                          ║
║  Windows  → Rufus (select the .img.gz directly)         ║
║  Any OS   → balenaEtcher                                 ║
║  Linux    → zcat *.img.gz | sudo dd of=/dev/sdX bs=4M   ║
║                                                          ║
║  After boot:  http://192.168.1.1/   (dashboard)         ║
║               http://192.168.1.1/cgi-bin/luci  (LuCI)  ║
╚══════════════════════════════════════════════════════════╝
EOF
