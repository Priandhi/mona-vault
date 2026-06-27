# Tencent Cloud Security Group Configuration

## Problem
9Router port 20128 (or any custom port) blocked by default security group.

## Symptoms
- `curl http://localhost:20128` works (307 redirect)
- `curl http://43.163.85.51:20128` times out
- Cloudflare quick tunnel works but dies frequently

## Solution: Open Port in Security Group

### Via Console (Mobile-friendly)
1. Login: https://console.tencentcloud.com
2. Menu → **VPC** → **Security Groups**
3. Find security group for Singapore region
4. **Add Inbound Rule:**
   - Type: Custom
   - Source: 0.0.0.0/0
   - Protocol Port: TCP:20128
   - Strategy: Allow
   - Note: 9Router Dashboard
5. Save

### Via CLI (tccli)
```bash
# Install
uv pip install tccli

# Configure (need API keys from Tencent Cloud console)
tccli configure set region ap-singapore
tccli configure set secret-id <YOUR_SECRET_ID>
tccli configure set secret-key <YOUR_SECRET_KEY>

# Get security group ID
tccli vpc DescribeSecurityGroups

# Add rule (replace sg-xxx with actual security group ID)
tccli vpc CreateSecurityGroupPolicies --SecurityGroupId sg-xxx --SecurityGroupPolicySet '{"Ingress":[{"Protocol":"tcp","Port":"20128","CidrBlock":"0.0.0.0/0","Action":"allow","PolicyDescription":"9Router Dashboard"}]}'
```

### Instance Metadata (for reference)
- Instance ID: `ins-0smh43fo`
- Region: `ap-singapore`
- IP: `43.163.85.51`
- App ID: `1301555531`

## Alternative: Use Nginx Reverse Proxy on Port 80/443
If 80/443 are open but 20128 is blocked:
```bash
apt install nginx
# Add to /etc/nginx/sites-available/9router:
server {
    listen 80;
    location / {
        proxy_pass http://localhost:20128;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
ln -s /etc/nginx/sites-available/9router /etc/nginx/sites-enabled/
systemctl restart nginx
```
Then access via `http://43.163.85.51` (port 80).
