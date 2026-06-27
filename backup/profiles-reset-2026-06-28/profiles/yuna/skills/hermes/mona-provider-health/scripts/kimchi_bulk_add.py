#!/usr/bin/env python3
"""
Kimchi.dev Bulk Add API Keys to 9Router
========================================
Usage: python3 kimchi_bulk_add.py
Edit API_KEYS list below with your keys.

Tested working model: kimchi/kimi-k2.5
Available: kimi-k2.5, kimi-k2.6, minimax-m2.5, minimax-m2.7,
           qwen3-coder-next-fp8, nemotron-3-super-fp4, smollm2-360m, smollm2-135m
"""

import requests
import json
import sys
import time
import sqlite3
import uuid
from datetime import datetime, timezone

ROUTER_URL = "http://localhost:20128"
ROUTER_PASSWORD = "123456"
DB_PATH = "/home/ubuntu/.9router/db/data.sqlite"

# Paste your Kimchi API keys here
API_KEYS = [
    # "castai_v1_xxxxxxxxxx...",
]

DEFAULT_MODEL = "kimi-k2.5"
KIMCHI_BASE_URL = "https://llm.kimchi.dev/openai/v1"


def login_9router(url, password):
    s = requests.Session()
    r = s.post(f"{url}/api/auth/login", json={"password": password})
    if r.status_code == 200 and r.json().get("success"):
        print("Logged in to 9Router")
        return s
    raise Exception(f"Login failed: {r.text}")


def get_kimchi_provider(session, url):
    r = session.get(f"{url}/api/provider-nodes")
    for node in r.json().get("nodes", []):
        if node.get("name") == "Kimchi":
            return node["id"]
    r = session.post(f"{url}/api/provider-nodes", json={
        "name": "Kimchi", "prefix": "kimchi", "apiType": "chat",
        "baseUrl": KIMCHI_BASE_URL, "type": "openai-compatible"
    })
    result = r.json()
    if result.get("node"):
        return result["node"]["id"]
    raise Exception("Failed to create Kimchi provider node")


def test_key(api_key):
    try:
        r = requests.post(f"{KIMCHI_BASE_URL}/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={"model": DEFAULT_MODEL, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
            timeout=15)
        return "choices" in r.json()
    except:
        return False


def add_key_db(provider_id, name, api_key, priority=1):
    conn_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    data = json.dumps({
        "apiKey": api_key, "testStatus": "active",
        "providerSpecificData": {"connectionProxyEnabled": False, "connectionProxyUrl": "", "connectionNoProxy": ""},
        "lastError": None, "lastErrorAt": None
    })
    try:
        db = sqlite3.connect(DB_PATH)
        db.execute(
            "INSERT INTO providerConnections (id,provider,authType,name,priority,isActive,data,createdAt,updatedAt) VALUES (?,'"+provider_id+"','apikey',?,?,1,1,?,?,?)",
            (conn_id, name, priority, data, now, now))
        db.commit()
        db.close()
        return conn_id
    except Exception as e:
        print(f"  DB error: {e}")
        return None


def main():
    print("=" * 50)
    print("Kimchi Bulk Add to 9Router")
    print("=" * 50)

    keys = [k.strip() for k in API_KEYS if k.strip() and not k.startswith("castai_v1_xxx")]
    if not keys:
        print("\nNo API keys! Edit API_KEYS in script.")
        sys.exit(1)

    print(f"\n{len(keys)} key(s) to process")
    session = login_9router(ROUTER_URL, ROUTER_PASSWORD)
    provider_id = get_kimchi_provider(session, ROUTER_URL)
    print(f"Provider: {provider_id}")

    success = 0
    for i, key in enumerate(keys, 1):
        short = f"{key[:15]}...{key[-6:]}"
        print(f"\n[{i}/{len(keys)}] {short}")
        valid = test_key(key)
        print(f"  Test: {'OK' if valid else 'unverified'}")
        cid = add_key_db(provider_id, f"Kimchi-{i:02d}", key, i)
        if cid:
            success += 1
            print(f"  Added: OK")
        time.sleep(0.2)

    print(f"\n{'='*50}")
    print(f"Results: {success}/{len(keys)} added")
    if success:
        import subprocess
        subprocess.run(["sudo", "systemctl", "restart", "9router"], capture_output=True)
        print("9Router restarted")
        print(f"\nRoute: kimchi/{DEFAULT_MODEL}")

    print("\nDone!")


if __name__ == "__main__":
    main()
