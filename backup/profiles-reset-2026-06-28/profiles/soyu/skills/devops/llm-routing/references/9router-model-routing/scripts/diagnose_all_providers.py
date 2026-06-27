#!/usr/bin/env python3
"""Quick diagnostic: test all providers (Kimchi direct, 9Router models) in one go.
Usage: python3 diagnose_all_providers.py [--9router-url URL] [--kimchi-key KEY]
"""
import requests
import json
import sys
import time

def test_endpoint(name, url, headers, body, timeout=15):
    """Test an endpoint and return status + response."""
    try:
        start = time.time()
        r = requests.post(url, headers=headers, json=body, timeout=timeout)
        elapsed = time.time() - start
        status = r.status_code
        try:
            resp = r.json()
        except:
            resp = {"raw": r.text[:200]}
        
        if status == 200:
            # Extract content
            choices = resp.get("choices", [{}])
            msg = choices[0].get("message", {}) if choices else {}
            content = msg.get("content") or msg.get("reasoning_content", "")
            return {"name": name, "status": "✅", "code": status, "speed": f"{elapsed:.1f}s", "preview": content[:80] if content else "(empty)"}
        elif status == 401:
            return {"name": name, "status": "❌ INVALID KEY", "code": status, "speed": f"{elapsed:.1f}s", "detail": resp.get("message", resp.get("error", "")[:80])}
        elif status == 402:
            return {"name": name, "status": "❌ CREDITS EXHAUSTED", "code": status, "speed": f"{elapsed:.1f}s", "detail": resp.get("error", "")[:80]}
        elif status == 403:
            return {"name": name, "status": "❌ IP BLOCKED", "code": status, "speed": f"{elapsed:.1f}s", "detail": r.text[:80]}
        else:
            return {"name": name, "status": f"❌ HTTP {status}", "code": status, "speed": f"{elapsed:.1f}s", "detail": str(resp)[:80]}
    except requests.exceptions.Timeout:
        return {"name": name, "status": "❌ TIMEOUT", "code": 0, "speed": f">{timeout}s", "detail": "Connection timed out"}
    except Exception as e:
        return {"name": name, "status": "❌ ERROR", "code": 0, "speed": "-", "detail": str(e)[:80]}

def main():
    router_url = "http://localhost:20128"
    kimchi_key = None
    router_key = None
    
    # Parse args
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--9router-url" and i < len(sys.argv) - 1:
            router_url = sys.argv[i + 1]
        elif arg == "--kimchi-key" and i < len(sys.argv) - 1:
            kimchi_key = sys.argv[i + 1]
    
    # Read 9Router CLI secret
    import os
    cli_secret_path = os.path.expanduser("~/.9router/auth/cli-secret")
    if os.path.exists(cli_secret_path):
        with open(cli_secret_path) as f:
            router_key = f.read().strip()
    
    # Read Kimchi key from 9Router DB if not provided
    if not kimchi_key:
        db_path = os.path.expanduser("~/.9router/db/data.sqlite")
        if os.path.exists(db_path):
            import sqlite3
            conn = sqlite3.connect(db_path)
            row = conn.execute(
                "SELECT json_extract(data, '$.apiKey') FROM providerConnections WHERE name LIKE 'Kimchi%' AND isActive = 1 LIMIT 1"
            ).fetchone()
            if row:
                kimchi_key = row[0]
            conn.close()
    
    test_body = {"model": "test", "messages": [{"role": "user", "content": "Reply with only: OK"}], "max_tokens": 5}
    results = []
    
    print("=" * 60)
    print("🔍 PROVIDER DIAGNOSTIC")
    print("=" * 60)
    
    # Test 9Router health
    if router_key:
        print("\n--- 9Router Health ---")
        r = test_endpoint(
            "9Router Auth",
            f"{router_url}/v1/models",
            {"Authorization": f"Bearer {router_key}"},
            {},
            timeout=5
        )
        # This is GET, not POST — override
        try:
            resp = requests.get(f"{router_url}/v1/models", headers={"Authorization": f"Bearer {router_key}"}, timeout=5)
            if resp.status_code == 200:
                r = {"name": "9Router Auth", "status": "✅", "code": 200, "speed": "-", "detail": "API key valid"}
            else:
                r = {"name": "9Router Auth", "status": "❌ INVALID KEY", "code": resp.status_code, "speed": "-", "detail": resp.text[:80]}
        except Exception as e:
            r = {"name": "9Router Auth", "status": "❌ ERROR", "code": 0, "speed": "-", "detail": str(e)[:80]}
        results.append(r)
        print(f"  {r['status']} ({r['code']}) {r.get('detail', '')}")
    
    # Test 9Router models
    if router_key:
        models = [
            ("9Router→Kimchi m2.7", "kimchi/minimax-m2.7"),
            ("9Router→MiMo v2.5", "xmtp/mimo-v2.5-pro"),
        ]
        print("\n--- 9Router Models ---")
        for name, model in models:
            body = {**test_body, "model": model}
            r = test_endpoint(name, f"{router_url}/v1/chat/completions",
                            {"Content-Type": "application/json", "Authorization": f"Bearer {router_key}"}, body)
            results.append(r)
            print(f"  {r['status']} {name} ({r.get('speed', '-')}) {r.get('preview', r.get('detail', ''))}")
    
    # Test Kimchi direct
    if kimchi_key:
        print("\n--- Kimchi Direct ---")
        body = {**test_body, "model": "minimax-m2.7"}
        r = test_endpoint("Kimchi Direct", "https://llm.kimchi.dev/openai/v1/chat/completions",
                        {"Content-Type": "application/json", "Authorization": f"Bearer {kimchi_key}",
                         "User-Agent": "curl/8.5.0"}, body)
        results.append(r)
        print(f"  {r['status']} ({r.get('speed', '-')}) {r.get('preview', r.get('detail', ''))}")
    
    # Summary
    print("\n" + "=" * 60)
    working = sum(1 for r in results if r["status"].startswith("✅"))
    total = len(results)
    print(f"📊 {working}/{total} providers working")
    
    if working == 0:
        print("\n⚠️  ALL PROVIDERS DOWN!")
        print("  → Check Kimchi credits: https://app.kimchi.dev")
        print("  → Check 9Router status: sudo systemctl status 9router")
        print("  → Check 9Router API key: cat ~/.9router/auth/cli-secret")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
