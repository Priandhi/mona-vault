# Keystore File Generation — eth_account CLI

## When to Use

User asks to export/backup wallet keys as keystore files (encrypted JSON). 
Keeystore files are compatible with Rabby, MetaMask, MyEtherWallet, TrustWallet, etc.

## Method

Use `eth_account` Python library directly — no browser needed:

```python
from eth_account import Account
import json, os

VAULT = os.path.expanduser("~/mona-workspace/vault")
KEYSTORE_DIR = os.path.join(VAULT, "keystores")
os.makedirs(KEYSTORE_DIR, exist_ok=True)

# Load PK from vault
with open(os.path.join(VAULT, ".galxe_wallet_pk")) as f:
    pk = f.read().strip()

# Generate keystore
acct = Account.from_key(pk)
keystore = acct.encrypt(password="your_password_here")
filename = f"priandhi_eth_{acct.address[:7]}.json"
with open(os.path.join(KEYSTORE_DIR, filename), "w") as f:
    json.dump(keystore, f, indent=2)
os.chmod(os.path.join(KEYSTORE_DIR, filename), 0o600)
```

## For EVM wallet fleet (vault/.wallets_evm)

```python
with open(os.path.join(VAULT, ".wallets_evm")) as f:
    data = json.load(f)
for w in data[" wallets"]:  # NOTE: key has space prefix
    acct = Account.from_key(w["pk"])
    keystore = acct.encrypt(password)
    filename = f"wallet_{w['id']}_{acct.address[:7]}.json"
    # write + chmod 600
```

## For seed phrase wallets (burner)

```python
Account.enable_unaudited_hdwallet_features()
acct = Account.from_mnemonic("word1 word2 ... word12")
keystore = acct.encrypt(password)
```

## Pitfalls

- **JSON key has space prefix:** `data[" wallets"]` not `data["wallets"]`
- **eth_account must be installed:** `pip install eth_account` or use venv
- **Password strength matters:** Keystore encryption is only as strong as the password
- **chmod 600:** Always restrict keystore file permissions
- **Manifest.json:** Create a manifest mapping wallet names → addresses → filenames for easy lookup
