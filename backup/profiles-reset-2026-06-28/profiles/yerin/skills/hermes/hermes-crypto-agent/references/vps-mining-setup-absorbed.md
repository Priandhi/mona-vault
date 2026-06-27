---
name: vps-mining-setup
description: >
  Setup CPU mining (RandomX/Juno Cash) on VPS — swap mining, pool configuration,
  Telegram monitoring, and cleanup. Triggered when user wants to mine crypto on VPS,
  setup swap mining, or configure mining monitoring.
triggers:
  - mine juno
  - setup mining
  - cpu mining vps
  - swap mining
  - mining monitor telegram
  - juno mining
---

# VPS Mining Setup

Setup and manage CPU mining on VPS with Telegram monitoring.

## Pre-Flight Checks

```bash
# Check specs
nproc                          # CPU cores
free -h                        # RAM (need 2GB free per thread)
df -h /                        # Disk (need 20GB+ for full node)
```

## Juno Cash (RandomX) — Quick Setup

### 1. Swap File (if RAM < 4GB)

```bash
# Check existing swap
swapon --show

# Create swap (size = 4GB or RAM deficit + 2GB)
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Verify
free -h
```

### 2. Download Miner

```bash
cd /tmp
JUNO_VERSION="0.9.12"
curl -sL "https://github.com/juno-cash/junocash/releases/download/v${JUNO_VERSION}/junocash-${JUNO_VERSION}-linux64.tar.gz" -o junocash.tar.gz
tar xzf junocash.tar.gz

# Install
sudo mkdir -p /opt/juno-mining
sudo cp -r junocash-${JUNO_VERSION} /opt/juno-mining/
sudo ln -sf /opt/juno-mining/junocash-${JUNO_VERSION}/bin/junocashd /usr/local/bin/junocashd
```

### 3. Pool Mining Script

```bash
cat > /opt/juno-mining/juno-mining.sh << 'SCRIPT'
#!/bin/bash
J1_ADDRESS="YOUR_J1_ADDRESS"
POOL="stratum+tcp://juno.suprnova.cc:3333"
THREADS=1
LOG="/home/ubuntu/.hermes/logs/juno-mining.log"
mkdir -p "$(dirname "$LOG")"

while true; do
    echo "[$(date)] Starting miner..." | tee -a "$LOG"
    junocashd -gen=1 -genproclimit=$THREADS 2>&1 | tee -a "$LOG"
    echo "[$(date)] Miner exited. Restarting in 10s..." | tee -a "$LOG"
    sleep 10
done
SCRIPT
chmod +x /opt/juno-mining/juno-mining.sh
```

### 4. PM2 Service

```bash
# Create ecosystem file
cat > /opt/juno-mining/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'juno-mining',
    script: '/opt/juno-mining/juno-mining.sh',
    interpreter: 'bash',
    max_restarts: 999,
    restart_delay: 10000,
    max_memory_restart: '1G'
  }]
}
EOF

# Start
cd /opt/juno-mining
pm2 start ecosystem.config.js
pm2 save
```

### 5. Telegram Monitor

#### Register Bot Commands
```python
import urllib.request, urllib.parse, json

token = "YOUR_BOT_TOKEN"
commands = json.dumps([
    {"command": "juno_sync", "description": "⛏️ Sync status"},
    {"command": "juno_stop", "description": "🔴 Stop mining"},
    {"command": "juno_start", "description": "🟢 Start mining"},
    {"command": "juno_cleanup", "description": "🗑️ Cleanup"}
])

url = f"https://api.telegram.org/bot{token}/setMyCommands"
data = urllib.parse.urlencode({"commands": commands}).encode()
urllib.request.urlopen(url, data=data, timeout=10)
```

#### Monitor Script (cron every 5 min)
```bash
* * * * * /opt/juno-mining/juno-monitor.sh >> /home/ubuntu/.hermes/logs/juno-monitor-cron.log 2>&1
```

#### Command Handler (cron every 1 min)
Poll `getUpdates`, parse `/command`, execute bash, reply via `sendMessage`.

### 6. Easy Cleanup

```bash
pm2 delete juno-mining
sudo rm -rf /opt/juno-mining
sudo rm /usr/local/bin/junocashd /usr/local/bin/junocash-cli
sudo swapoff /swapfile 2>/dev/null
sudo rm /swapfile 2>/dev/null
crontab -l | grep -v juno | crontab -
```

## GPU Mining on Cloud Platforms

For GPU-based mining (not CPU), see **gpu-cloud-mining** skill — covers Modal.com setup, CUDA builds, and GPU cost optimization.

## Hashrate Estimates

| CPU | Cores | RAM | Expected H/s |
|-----|-------|-----|-------------|
| Xeon 8255C @ 2.5GHz | 2 | 1.9GB + swap | ~100-200 |
| Xeon 8255C @ 2.5GHz | 2 | 4GB+ | ~300-500 |
| AMD Ryzen 5 3600 | 6 | 8GB | ~4,000-5,000 |
| AMD Ryzen 9 5950X | 16 | 32GB | ~12,000-14,000 |

## Pitfalls

1. **Always check existing swap first** — `swapon --show` before creating new
2. **1 thread on low RAM** — 2 threads on 1.9GB will OOM
3. **Pool registration** — register at pool website first (worker setup)
4. **Node sync** — first sync takes time; pool mining doesn't need full sync
5. **SSH port** — some VPS use non-standard SSH ports (e.g., Spaceship uses 2022/22022). Check the VM detail page for the correct SSH port
6. **Provider ToS** — check if VPS provider allows mining
7. **Mining script variable escaping** — when writing bash scripts via SSH heredoc, `$VAR` gets expanded by the local shell. Use single-quoted heredoc (`<< 'EOF'`) and escape with `\\$VAR` inside, OR write the file locally first and `scp` it to the remote host. NESTED heredocs (heredoc inside heredoc) WILL break — avoid at all costs. Write locally → scp instead
8. **Telegram token on new VPS** — bot token is NOT auto-available on a fresh VPS. Copy it from the old VPS: `grep TELEGRAM_BOT_TOKEN ~/.hermes/.env` → save to `/etc/environment` on new VPS as `TELEGRAM_BOT_TOKEN=xxx`
9. **npm/Node.js not on fresh Ubuntu** — `apt install -y nodejs npm` or use nodesource setup before installing PM2
10. **Password with special chars** — passwords like `@Tokenabu187` need careful quoting in sshpass: `sshpass -p '@Tokenabu187' ssh ...` (single quotes, not double)
11. **Mining address format** — Juno uses `j1...` addresses (not `juno1...`). Double-check the address format from the wallet app
12. **VPS migration** — when moving mining to a new VPS, fully clean up the old one first: `pm2 delete`, remove `/opt/juno-mining`, remove swap file, remove cron jobs
13. **Cloud provider port blocking** — Spaceship and similar cloud providers often block outbound stratum ports (3333). Test with `nc -zv <pool> <port>` before configuring. If blocked, try: (a) open port in provider firewall/dashboard, (b) use a pool on port 443/80, (c) setup VPN/wireguard on the VPS to bypass restrictions
14. **junocashd doesn't support pool mining** — `junocashd -gen=1` is SOLO mining only (no pool stratum support). For POOL mining, use `xmrig` built from source: `git clone https://github.com/xmrig/xmrig.git`. Build with `cmake .. -DWITH_OPENCL=OFF -DWITH_CUDA=OFF && make -j$(nproc)`
15. **xmrig config write-then-copy pattern** — don't try to create xmrig config JSON through SSH heredoc (too many escaping issues). Write the JSON locally with `write_file`, then `scp` it to the remote host
16. **Seed phrase security** — NEVER ask the user to send their seed phrase. Store it yourself if the user insists, but strongly advise against it. The user's seed phrase should remain offline/private. Use the public J1 address only for mining
17. **User VPS access** — users can access their new VPS via: (a) provider web console/VNC from dashboard, (b) Termius SSH client with IP, port, username, password. Guide them through Termius setup for easy monitoring
18. **Solo mining with junocashd requires wallet** — `junocashd -gen=1` mines to the local wallet's default address. You need to create/import a wallet first with `junocashd-wallet-tool`, or use pool mining (xmrig) which goes directly to any J1 address
19. **Spaceship trial VPS instability** — Spaceship trial accounts can get locked/suspended without warning. VPS becomes completely unreachable (SSH timeout, 100% packet loss). Always backup mining config and wallet address externally. User reported account lock on June 10, 2026 (VPS 104.207.77.55). Recovery requires contacting Spaceship support or creating new account. Do NOT rely on trial VPS for long-term mining
