"""
Bulk Ethereum Wallet Generator
Generates N Ethereum wallets and saves to JSON.
Usage: python3 wallet_gen.py <count> <output_file>
"""
import json
import secrets
import sys
from eth_account import Account

def generate_wallets(count, output_path):
    wallets = []
    for i in range(count):
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        wallets.append({
            "index": i + 1,
            "address": account.address,
            "private_key": private_key,
        })
        if (i + 1) % 100 == 0:
            print(f"Generated {i+1}/{count}...")

    with open(output_path, "w") as f:
        json.dump(wallets, f, indent=2)

    print(f"\n✅ {count} wallets saved to {output_path}")
    for w in wallets[:3]:
        print(f"  [{w['index']}] {w['address']}")
    if count > 3:
        print(f"  ... and {count-3} more")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    output = sys.argv[2] if len(sys.argv) > 2 else "/home/ubuntu/.hermes/farm/wallets.json"
    generate_wallets(count, output)
