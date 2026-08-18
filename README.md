# RAMTECH SQM — OpenWrt Mini PC Router

Custom OpenWrt firmware image for x86/64 Mini PCs with CAKE SQM pre-installed
and a browser-based dashboard for real-time monitoring and configuration.

---

## Project Structure

```
Ramtech SQM/
├── cgi-bin/
│   ├── traffic          ← Realtime WAN RX/TX bytes → JSON
│   ├── sqm-status       ← CPU, RAM, uptime, WAN IP, SQM state → JSON
│   └── sqm-settings     ← GET/POST SQM settings via UCI
├── www/
│   └── index.html       ← Dashboard UI
├── uci-defaults/
│   └── 99-ramtech-sqm   ← First-boot auto-configuration
├── dist/                ← Built images go here
├── build-ramtech-sqm.sh ← Linux image builder
└── deploy.ps1           ← Windows direct-deploy to running router
```

---

## Option A — Deploy to a Running OpenWrt Router (Windows)

If OpenWrt is already running on your Mini PC:

```powershell
# Run in PowerShell from the project folder
.\deploy.ps1
```

Type `thea` when prompted for the SSH/SCP password.

Dashboard will be live at: **http://192.168.0.109/**

---

## Option B — Build a Flashable Image (Linux / WSL2)

### Requirements
- Ubuntu 20.04 / 22.04 / 24.04 or Debian 11/12
- ~4 GB free disk space, internet connection

### Install build dependencies
```bash
sudo apt update
sudo apt install -y wget make tar gawk unzip python3 libncurses-dev
```

### Build
```bash
bash build-ramtech-sqm.sh
```

Takes 10–15 minutes. Output images land in `./dist/`.

---

## Flashing the Image

| Tool | Platform | Notes |
|------|----------|-------|
| **Rufus** | Windows | Select the `.img.gz` file, "DD Image" mode |
| **balenaEtcher** | Windows / macOS / Linux | Drag and drop the `.img.gz` |
| **dd** | Linux | `zcat ramtech-sqm-*.img.gz \| sudo dd of=/dev/sdX bs=4M status=progress` |

> **Warning:** The image overwrites the entire target drive. Back up data first.

---

## Hardware Requirements

| Component | Minimum |
|-----------|---------|
| CPU | x86/64 (Intel N100, N5105, J4125, etc.) |
| RAM | 2 GB (4 GB recommended for 1 Gbps SQM) |
| Storage | 8 GB eMMC / SSD / USB drive |
| NICs | **2 × Ethernet** (WAN = `eth1`, LAN = `eth0`) |

---

## Post-Flash Setup

1. Connect a PC to the LAN port
2. Open **http://192.168.1.1/** → RAMTECH SQM Dashboard
3. In **SQM & Branding Settings**:
   - Set your actual ISP Download / Upload speed (Mbps)
   - Choose the correct WAN interface
   - Check **Enable SQM / CAKE** → **SAVE & APPLY**
4. LuCI (advanced) is at **http://192.168.1.1/cgi-bin/luci**
5. SSH: `ssh root@192.168.1.1` — **no password by default, set one immediately!**

---

## SQM / CAKE Notes

- CAKE shapes traffic to your ISP limit, dramatically reducing bufferbloat
- Flow offloading is **disabled** by default (required — it bypasses CAKE)
- Packet steering is **enabled** for better multi-core performance
- Verify CAKE is active after boot:
  ```
  ssh root@192.168.1.1 "tc -s qdisc show dev eth1"
  ```

---

## Default Credentials (change after flash!)

| Service | User | Password |
|---------|------|----------|
| SSH / LuCI | root | *(none)* |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cgi-bin/traffic` | GET | `{"rx":bytes,"tx":bytes}` |
| `/cgi-bin/sqm-status` | GET | CPU, RAM, uptime, WAN IP, SQM state |
| `/cgi-bin/sqm-settings` | GET | Current settings (Mbps) |
| `/cgi-bin/sqm-settings` | POST | Apply new settings + restart SQM |
