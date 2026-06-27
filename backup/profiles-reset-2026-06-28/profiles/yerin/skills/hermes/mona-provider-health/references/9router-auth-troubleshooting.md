# 9Router Authentication Troubleshooting

## Auth Architecture
9Router has its own auth layer INDEPENDENT of provider API keys:
- **Dashboard auth**: Password-based (`POST /api/auth/login` → session cookie)
- **v1 API auth**: Bearer token = content of `~/.9router/auth/cli-secret`
- **Provider routing**: 9Router forwards requests to providers using keys stored in its SQLite DB

**Key distinction**: The API key in Hermes `custom_providers` for "9router" is the **9Router CLI secret**, NOT a provider API key. The actual provider keys (Kimchi, MiMo, etc.) are stored inside 9Router's DB.

## Common Failure: "Missing API key" / "Invalid API key"

### Symptom
```
curl -X POST http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"kimchi/minimax-m2.7","messages":[...]}'

→ HTTP 401: {"error":{"message":"Missing API key","type":"authentication_error","code":"invalid_api_key"}}
```

### Root Cause
The `/v1/chat/completions` endpoint requires `Authorization: Bearer <cli-secret>` header. Without it, 9Router returns 401.

### Diagnosis Steps
```bash
# 1. Check 9Router is running
pgrep -a 9router
curl -s http://localhost:20128/api/health  # should return {"ok":true}

# 2. Read the CLI secret
cat ~/.9router/auth/cli-secret

# 3. Test with correct auth
CLI_KEY=$(cat ~/.9router/auth/cli-secret)
curl -s -X POST http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CLI_KEY" \
  -d '{"model":"kimchi/minimax-m2.7","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# 4. Verify Hermes config has matching key
grep -A5 "9router" ~/.hermes/config.yaml | grep api_key
# Key should match ~/.9router/auth/cli-secret
```

### If Key Mismatch
Update Hermes config:
```yaml
custom_providers:
- name: 9router
  api_key: <paste from ~/.9router/auth/cli-secret>
  base_url: http://localhost:20128/v1
  model: kimchi/minimax-m2.7
```

## Common Failure: Provider Key Works Directly but Fails via 9Router

### Symptom
```bash
# Direct to provider → ✅
curl -s -X POST https://llm.kimchi.dev/openai/v1/chat/completions \
  -H "Authorization: Bearer castai_v1_xxx" -d '...'  # HTTP 200

# Via 9Router → ❌
curl -s -X POST http://localhost:20128/v1/chat/completions \
  -H "Authorization: Bearer $CLI_KEY" \
  -d '{"model":"kimchi/minimax-m2.7",...}'  # HTTP 401 or 500
```

### Diagnosis
```bash
DB="/home/ubuntu/.9router/db/data.sqlite"

# 1. Check provider node exists
sqlite3 "$DB" "SELECT id, name, json_extract(data,'$.prefix') FROM providerNodes;"

# 2. Check connection exists and is active
sqlite3 -header "$DB" "SELECT name, isActive, json_extract(data,'$.testStatus'), json_extract(data,'$.lastError') FROM providerConnections;"

# 3. Check node-connection linkage
sqlite3 "$DB" "
SELECT pc.name, pc.provider, 
       CASE WHEN pn.id IS NULL THEN 'MISSING' ELSE 'OK' END
FROM providerConnections pc LEFT JOIN providerNodes pn ON pc.provider = pn.id;
"

# 4. Test provider key directly
KEY=$(sqlite3 "$DB" "SELECT json_extract(data,'$.apiKey') FROM providerConnections WHERE name='Kimchi-01';")
curl -s -X POST "https://llm.kimchi.dev/openai/v1/chat/completions" \
  -H "Authorization: Bearer $KEY" -d '...' 
```

### Common Fixes
- **Connection marked `unavailable`**: 9Router backs off after errors. Restart: `sudo systemctl restart 9router`
- **Provider node missing**: Re-add via dashboard or DB insert
- **Key expired in DB**: Update key: `sqlite3 db "UPDATE providerConnections SET data=json_set(data,'$.apiKey','NEW_KEY') WHERE name='Kimchi-01';"`

## Testing Workflow
```bash
# Full test script
CLI_KEY=$(cat ~/.9router/auth/cli-secret)
echo "9Router CLI key: ${CLI_KEY:0:10}..."

# Health
curl -s http://localhost:20128/api/health

# Test each model prefix
for model in "kimchi/minimax-m2.7" "tokenrouter/MiniMax-M3"; do
  echo -n "$model: "
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:20128/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $CLI_KEY" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"OK\"}],\"max_tokens\":3}" \
    --max-time 15)
  echo "HTTP $HTTP"
done
```

## 9Router Service Management
```bash
# 9Router runs as systemd service (NOT pm2!)
sudo systemctl status 9router
sudo systemctl restart 9router

# Logs
journalctl --user -u 9router -f --no-pager

# Process check
pgrep -a 9router
```
