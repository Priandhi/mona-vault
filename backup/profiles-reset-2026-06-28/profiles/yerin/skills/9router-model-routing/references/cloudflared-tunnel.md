# Cloudflare Tunnel Setup for 9Router

## Quick Tunnel (Temporary)
```bash
cloudflared tunnel --url http://localhost:20128
```
- URL changes every restart
- No persistence
- Good for testing

## Systemd Service (Auto-Restart)

### Create Service
```bash
sudo tee /etc/systemd/system/cloudflared-9router.service > /dev/null << 'EOF'
[Unit]
Description=Cloudflare Tunnel for 9Router
After=network.target 9router.service
Wants=9router.service

[Service]
Type=simple
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:20128
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### Enable & Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflared-9router
sudo systemctl start cloudflared-9router
```

### Get Current URL
```bash
sudo journalctl -u cloudflared-9router --no-pager -n 30 | grep -o 'https://[a-z0-9-]*.trycloudflare.com' | head -1
```

### Check Status
```bash
sudo systemctl status cloudflared-9router
```

### Restart
```bash
sudo systemctl restart cloudflared-9router
```

## Troubleshooting

### Tunnel dies frequently
- Service auto-restarts within 5 seconds
- URL changes on each restart
- Consider direct IP access instead

### 530 error
- Tunnel connection lost
- `sudo systemctl restart cloudflared-9router`

### New URL each restart
- Expected behavior for quick tunnels
- Use direct IP access for stable URL
- Or use named tunnel with Cloudflare account

## Direct IP Access (Best)

Open port in cloud provider firewall:
```bash
# Tencent Cloud: Security Group → Add Rule → TCP:20128 → Allow → 0.0.0.0/0
# Then access: http://43.163.85.51:20128
```

**Advantages:**
- Never dies
- No URL changes
- No tunnel overhead
- Works even if Cloudflare is down
