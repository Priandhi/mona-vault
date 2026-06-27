# 9Router API Key Management

## Overview

9Router supports API key authentication for programmatic access. Keys are managed via the dashboard or REST API.

## CRUD Operations

### List Keys
```python
import urllib.request, json, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
login_data = json.dumps({"password": "Mona187"}).encode()
req = urllib.request.Request("http://localhost:20128/api/auth/login", data=login_data, headers={"Content-Type": "application/json"})
opener.open(req).read()

req = urllib.request.Request("http://localhost:20128/api/keys")
resp = opener.open(req)
data = json.loads(resp.read().decode())
for k in data['keys']:
    print(f"  {k['name']}: {k['key'][:20]}... (active={k['isActive']})")
```

### Create Key
```python
create_data = json.dumps({"name": "my-key"}).encode()
req = urllib.request.Request("http://localhost:20128/api/keys", data=create_data, headers={"Content-Type": "application/json"})
resp = opener.open(req)
result = json.loads(resp.read().decode())
# Returns: {"key": "sk-6b3...c81d", "name": "my-key", "id": "...", "machineId": "..."}
```

### Delete Key
```python
key_id = "2b36fc40-766a-44d3-ad13-a2369dead849"
req = urllib.request.Request(f"http://localhost:20128/api/keys/{key_id}", method='DELETE')
resp = opener.open(req)
# Returns: {"message": "Key deleted successfully"}
```

## Authentication Modes

### Mode 1: Cookie Auth (Default)
- Login via `POST /api/auth/login` with `{"password": "..."}`
- Use cookie jar for subsequent requests
- Works for all API endpoints

### Mode 2: API Key + Cookie
- Add `X-API-Key: <key>` header to requests
- Still requires cookie auth (login first)
- API key acts as additional verification

### Mode 3: API Key Only (Requires Toggle)
- Enable "Require API Key" toggle in dashboard (Endpoint page)
- Then use `X-API-Key: <key>` header WITHOUT cookie auth
- **Default is OFF** — API key only auth won't work until toggle is enabled

## Key Format

- Created keys use format: `sk-<hex>-<hex>` (e.g., `sk-6b3ac6ef8e3b70c9-...`)
- Built-in key (hermes-cli): `9f44b039647ca9c62401...` (longer format)
- Keys are stored in `providerConnections` table in `~/.9router/db/data.sqlite`

## Testing Keys

```python
# Test API key auth (with cookie)
req = urllib.request.Request("http://localhost:20128/api/keys")
req.add_header('X-API-Key', api_key)
resp = opener.open(req)  # opener has cookie jar
print(resp.read().decode())

# Test API key only (no cookie) — requires "Require API Key" toggle ON
opener2 = urllib.request.build_opener()
req = urllib.request.Request("http://localhost:20128/api/keys")
req.add_header('X-API-Key', api_key)
resp = opener2.open(req)  # no cookie jar
```

## Dashboard UI

- **Endpoint page**: Toggle "Require API Key" on/off
- **Create Key**: Button to generate new API key
- **Key list**: Shows all keys with name, partial key, active status
