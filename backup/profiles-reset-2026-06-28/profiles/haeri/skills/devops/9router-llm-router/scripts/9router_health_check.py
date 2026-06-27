#!/usr/bin/env python3
"""
9Router connection health check script.

Tests ALL providerConnections in 9Router by:
1. Calling the test endpoint (/api/providers/{id}/test) for each
2. Verifying the stored errorCode matches the test result
3. Flagging STALE errors (errorCode non-zero but test says valid)
4. Identifying connections that are likely broken (test fails)

Usage:
    python3 9router_health_check.py
    python3 9router_health_check.py --test-chat  # also runs real /v1/chat calls
    python3 9router_health_check.py --json       # output as JSON

The script auto-detects:
- 9Router port (default 20128)
- Machine ID (from ~/.9router/machine-id)
- Dashboard password (hardcoded "Mona187" — change in source if needed)
- CLI secret (from ~/.9router/auth/cli-secret)

This is a READ-ONLY diagnostic. It does NOT modify any 9Router state.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Auto-detect 9Router paths
ROUTER_URL = os.environ.get("ROUTER_URL", "http://localhost:20128")
MACHINE_ID_PATH = Path.home() / ".9router" / "machine-id"
CLI_SECRET_PATH=*** / ".9router" / "auth" / "cli-secret"
DASHBOARD_PASSWORD=os.env...D", "Mona187")


def login() -> str:
    """Login to 9Router dashboard API. Returns auth_token cookie value."""
    if not MACHINE_ID_PATH.exists():
        sys.exit(f"❌ Machine ID not found: {MACHINE_ID_PATH}")
    machine_id = MACHINE_ID_PATH.read_text().strip()
    req = urllib.request.Request(
        f"{ROUTER_URL}/api/auth/login",
        data=json.dumps({"password": DASHBOARD_PASSWORD, "machineId": machine_id}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            for c in r.headers.get_all("Set-Cookie") or []:
                if c.startswith("auth_token="):
                    return c.split(";")[0]
        sys.exit("❌ Login succeeded but no auth_token cookie returned")
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ Login failed: HTTP {e.code}: {e.read().decode()[:200]}")


def get_connections(cookie: str) -> list:
    """List all provider connections."""
    req = urllib.request.Request(f"{ROUTER_URL}/api/providers", headers={"Cookie": cookie})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode()).get("connections", [])


def test_connection(cookie: str, conn_id: str) -> dict:
    """Call /api/providers/{id}/test and return result."""
    req = urllib.request.Request(
        f"{ROUTER_URL}/api/providers/{conn_id}/test",
        method="POST",
        headers={"Cookie": cookie, "Content-Type": "application/json"},
        data=b"{}",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"valid": False, "error": str(e)}


def test_chat(model: str, cli_secret: str) -> dict:
    """Real /v1/chat/completions test."""
    auth = "Bearer " + cli_secret
    req = urllib.request.Request(
        f"{ROUTER_URL}/v1/chat/completions",
        data=json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
            "stream": False,
        }).encode(),
        headers={"Content-Type": "application/json", "Authorization": auth},
    )
    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
            if "choices" in d:
                return {"ok": True, "elapsed": time.time() - start}
            return {"ok": False, "error": str(d)[:200]}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.read().decode()[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def derive_default_model(conn: dict) -> str:
    """Build the 9Router model ID for a connection: {prefix}/{defaultModel}."""
    data = conn.get("data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    prefix = data.get("providerSpecificData", {}).get("prefix", "")
    default = data.get("defaultModel") or conn.get("defaultModel") or ""
    if prefix and default:
        return f"{prefix}/{default}"
    return ""


def main():
    parser = argparse.ArgumentParser(description="9Router connection health check")
    parser.add_argument("--test-chat", action="store_true", help="Also test real /v1/chat calls")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not CLI_SECRET_PATH.exists():
        sys.exit(f"❌ CLI secret not found: {CLI_SECRET_PATH}")
    cli_secret = CLI_SECRET_PATH.read_text().strip()

    cookie = login()
    conns = get_connections(cookie)

    results = []
    for c in conns:
        cid = c["id"]
        name = c.get("name", "?")
        data = c.get("data", {})
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}
        stored_error = data.get("errorCode")
        test_result = test_connection(cookie, cid)
        test_valid = test_result.get("valid", False)

        # Flag stale errors
        stale = (stored_error and stored_error != 0) and test_valid
        result = {
            "name": name,
            "id": cid,
            "prefix": data.get("providerSpecificData", {}).get("prefix", ""),
            "baseUrl": data.get("providerSpecificData", {}).get("baseUrl", ""),
            "defaultModel": data.get("defaultModel", ""),
            "isActive": c.get("isActive"),
            "stored_errorCode": stored_error,
            "test_valid": test_valid,
            "test_error": test_result.get("error"),
            "stale_error": stale,
        }

        if args.test_chat:
            model = derive_default_model(c)
            if model:
                chat = test_chat(model, cli_secret)
                result["chat_model"] = model
                result["chat_ok"] = chat.get("ok", False)
                result["chat_elapsed"] = round(chat.get("elapsed", 0), 2)
                result["chat_error"] = chat.get("error", "")

        results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    # Pretty print
    print(f"\n🔍 9Router Health Check — {len(results)} connections\n")
    print(f"{'NAME':<25} {'PREFIX':<15} {'STORED':<8} {'TEST':<6} {'STALE':<6} STATUS")
    print("─" * 100)

    healthy = stale_errs = broken = 0
    for r in results:
        stored = r["stored_errorCode"] if r["stored_errorCode"] is not None else "—"
        test = "✅" if r["test_valid"] else "❌"
        stale_mark = "⚠️" if r["stale_error"] else "—"
        prefix = (r.get("prefix") or "?")[:14]
        name = (r.get("name") or "?")[:24]
        print(f"{name:<25} {prefix:<15} {str(stored):<8} {test:<6} {stale_mark:<6}", end="")

        if r.get("chat_ok"):
            print(f"✅ OK ({r.get('chat_elapsed')}s)")
            healthy += 1
        elif r["test_valid"] and not args.test_chat:
            print(f"✅ test says valid")
            healthy += 1
        elif r["stale_error"]:
            print(f"⚠️  STALE — test passes despite errorCode={r['stored_errorCode']}")
            stale_errs += 1
        else:
            err = r.get("test_error") or r.get("chat_error") or "?"
            print(f"❌ BROKEN: {str(err)[:60]}")
            broken += 1

    print("─" * 100)
    print(f"Summary: {healthy} healthy, {stale_errs} stale (test OK but errorCode set), {broken} broken\n")

    if stale_errs:
        print("💡 Stale errors are non-critical — the test endpoint says valid, so the")
        print("   connection is actually working. The stored errorCode is from a")
        print("   previous transient failure. Safe to ignore.\n")
    if broken:
        print("⚠️  Broken connections: investigate test_error or chat_error above.\n")


if __name__ == "__main__":
    main()
