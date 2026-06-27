#!/usr/bin/env python3
"""
Kimchi.dev Bulk Add API Keys to 9Router (DB Insert)
=====================================================
Usage: python3 kimchi_bulk_add.py
Edit API_KEYS list below with your keys.

Tested working: Jun 11, 2026 — 11 keys added successfully
"""

import json
import sys
import time
import sqlite3
import uuid
import os
from datetime import datetime, timezone

# ============ CONFIGURATION ============
DB_PATH = os.path.expanduser("~/.9router/db/data.sqlite")
PROVIDER_NODE_ID = "openai-compatible-chat-e5bae896-88ab-4689-b132-c3c20bef91e3"

# Paste your Kimchi API keys here (one per line)
API_KEYS_FILE = os.path.expanduser("~/kimchi_keys.txt")
# Or paste directly:
API_KEYS = [
    # "castai_v1_xxxxxxxxxxxx...",
]

DEFAULT_MODEL = "minimax-m2.7"
KIMCHI_BASE_URL = "https://llm.kimchi.dev/openai/v1"
# =========================================


def load_keys():
    """Load keys from file or list"""
    keys = [k.strip() for k in API_KEYS if k.strip() and not k.startswith("#")]
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE) as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 3:
                    keys.append(parts[2])  # apikey is 3rd field
    return list(set(keys))  # deduplicate


def add_key_db(conn, name, api_key, email=""):
    """Insert connection into 9Router DB with CORRECT format"""
    conn_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    # MUST include ALL these fields or connection will fail validation
    data = json.dumps({
        "apiKey": api_key,
        "testStatus": "pending",
        "providerSpecificData": {
            "baseUrl": KIMCHI_BASE_URL,      # CRITICAL — missing = "Missing base URL"
            "prefix": "kimchi",               # CRITICAL — missing = pattern validation error
            "apiType": "chat",                # CRITICAL
            "nodeName": name,                 # Match connection name
            "connectionProxyEnabled": False,
            "connectionProxyUrl": "",
            "connectionNoProxy": ""
        },
        "defaultModel": DEFAULT_MODEL,        # CRITICAL — missing = routing issues
        "backoffLevel": 0,
        "lastError": None,
        "lastErrorAt": None
    })
    
    try:
        conn.execute(
            "INSERT INTO providerConnections (id,provider,authType,name,email,priority,isActive,data,createdAt,updatedAt) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (conn_id, PROVIDER_NODE_ID, "apikey", name, email, 0, 1, data, now, now)
        )
        return conn_id
    except Exception as e:
        print(f"  ❌ DB error: {e}")
        return None


def main():
    print("=" * 50)
    print("🔑 Kimchi Bulk Add to 9Router")
    print("=" * 50)

    keys = load_keys()
    if not keys:
        print("\n❌ No API keys! Edit API_KEYS or create ~/kimchi_keys.txt")
        sys.exit(1)

    print(f"\n📋 {len(keys)} key(s) to process")
    
    # Get existing connections to avoid duplicates
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT json_extract(data, '$.apiKey') FROM providerConnections WHERE name LIKE 'Kimchi%'")
    existing = {r[0] for r in cur.fetchall() if r[0]}
    print(f"📡 Existing: {len(existing)} connections")

    success = 0
    for i, key in enumerate(keys, 1):
        if key in existing:
            print(f"[{i}] Skip (exists): ...{key[-16:]}")
            continue
        
        # Get next name
        cur.execute("SELECT COUNT(*) FROM providerConnections WHERE name LIKE 'Kimchi%'")
        count = cur.fetchone()[0] + 1
        name = f"Kimchi-{count:02d}"
        
        short = f"...{key[-16:]}"
        print(f"[{i}] Adding {name} | {short}")

        cid = add_key_db(db, name, key)
        if cid:
            success += 1
            print(f"  ✅ Added")
        time.sleep(0.1)

    db.commit()
    db.close()

    print(f"\n{'='*50}")
    print(f"📊 {success}/{len(keys)} added")

    if success:
        import subprocess
        subprocess.run(["sudo", "systemctl", "restart", "9router"], capture_output=True)
        print("🔄 9Router restarted")
        print(f"\n🎯 Route: kimchi/{DEFAULT_MODEL}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
