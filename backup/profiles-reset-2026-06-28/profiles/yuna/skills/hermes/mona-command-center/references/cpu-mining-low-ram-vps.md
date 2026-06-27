# CPU Mining on Low-RAM VPS — Juno Cash Pattern

## Problem

Mining RandomX-based coins (Juno Cash, Monero) requires ~2GB RAM per thread. Most budget VPS have only 1.9-4GB total RAM, causing OOM crashes.

## Solution: Swap File + Limited Threads

### Step 1: Add Swap File

```bash
# Check existing swap
free -h
swapon --show

# Create additional swap (2-4GB)
sudo dd if=/dev/zero of=/swapfile2 bs=1M count=4096
sudo chmod 600 /swapfile2
sudo mkswap /swapfile2
sudo swapon /swapfile2

# Verify
free -h
```

**Note:** Swap is much slower than RAM. Expect reduced hashrate. 1 thread is recommended for low-RAM VPS.

### Step 2: Download Miner

```bash
# Juno Cash example
cd /tmp
curl -sL "https://github.com/juno-cash/junocash/releases/download/v0.9.12/junocash-0.9.12-linux64.tar.gz" -o junocash.tar.gz
tar xzf junocash.tar.gz
sudo mkdir -p /opt/mining
sudo cp -r junocash-0.9.12 /opt/mining/
sudo ln -sf /opt/mining/junocash-0.9.12/bin/junocashd /usr/local/bin/junocashd
```

### Step 3: Mining Script

```bash
#!/bin/bash
# /opt/mining/mining.sh
J1_ADDRESS="j1x6wxsdvnuv8dg4w5jewqpedkc62gsmzk86ljxgue7z5g0vxpu6e8x63yewspwpanpzaum75tans46uudsh5ksew38v30u796zc5dpldk"
POOL="stratum+tcp://juno.suprnova.cc:3333"
THREADS=1  # Keep at 1 for low-RAM VPS
LOG="/home/ubuntu/.hermes/logs/mining.log"

mkdir -p "$(dirname "$LOG")"

while true; do
    echo "[$(date)] Starting miner (threads=$THREADS)..." | tee -a "$LOG"
    junocashd -gen=1 -genproclimit=$THREADS 2>&1 | tee -a "$LOG"
    echo "[$(date)] Miner exited. Restarting in 10s..." | tee -a "$LOG"
    sleep 10
done
```

### Step 4: PM2 Service

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'mining',
    script: '/opt/mining/mining.sh',
    interpreter: 'bash',
    max_restarts: 999,
    restart_delay: 10000,
    max_memory_restart: '1G',
  }]
}
```

```bash
pm2 start /opt/mining/ecosystem.config.js
```

### Step 5: Monitoring to Telegram Topic

```bash
#!/bin/bash
# /opt/mining/monitor.sh — run via cron every 5 min
STATUS=$(pm2 list | grep "mining.*online" && echo "🟢 ONLINE" || echo "🔴 STOPPED")
MEM_PCT=$(free -m | awk '/^Mem:/{printf "%.0f", $3/$2*100}')
HASHRATE=$(grep -oP 'hashrate[:\s]+\K[0-9.]+' /home/ubuntu/.hermes/logs/mining.log | tail -1)
HASHRATE=${HASHRATE:-"syncing..."}

MSG="⛏️ MINING STATUS

📊 Status: $STATUS
⚡ Hashrate: $HASHRATE H/s
💾 RAM: ${MEM_PCT}%"

curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "message_thread_id=${TOPIC_ID}" \
    -d "text=${MSG}"
```

### Cleanup (When Done)

```bash
pm2 stop mining
pm2 delete mining
sudo rm -rf /opt/mining
sudo swapoff /swapfile2
sudo rm /swapfile2
crontab -l | grep -v mining-monitor | crontab -
```

## VPS Suitability Check

| Spec | Minimum | Recommended |
|---|---|---|
| RAM | 2GB + swap | 4GB+ native |
| CPU cores | 1 | 2+ |
| Disk | 20GB free | 40GB+ |
| Hashrate (2 core + swap) | ~100-200 H/s | ~500-1000 H/s |

**Profitability warning:** Low-RAM VPS mining produces very small returns. Calculate: (hashrate × coin_price × 86400) / network_difficulty. Often less than VPS cost.
