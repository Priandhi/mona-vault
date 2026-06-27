# .gitignore — Obsidian Vault

> Copy this to `/home/ubuntu/obsidian-vault/.gitignore` at vault init.

```gitignore
# 04-WALLET/ — NEVER push. Contains sensitive data (addresses, secrets, keypair refs).
04-WALLET/

# OS / editor noise
.DS_Store
Thumbs.db

# Obsidian internal cache (regenerable, not user content)
.obsidian/workspace.json
.obsidian/cache/

# Trashed vault artifacts
*.swp
*.swo
*~
```

## Verify After Init

```bash
cd /home/ubuntu/obsidian-vault
git check-ignore -v 04-WALLET/
# Expected: .gitignore:2:04-WALLET/   04-WALLET/
```

If 04-WALLET/ ever shows in `git status` (e.g., after force-adding), immediately:
```bash
git rm -rf --cached 04-WALLET/
# Then verify .gitignore line is correct
```

## What NOT to Add

- ❌ Don't add `01-DAILY/` — daily notes are content, must be tracked
- ❌ Don't add `05-HERMES-OUTPUTS/` — receipts are content, must be tracked
- ❌ Don't add `04-WALLET/` to a "safe" list — it MUST stay ignored
- ❌ Don't add `*.log` by default — logs may be useful receipts of agent runs
