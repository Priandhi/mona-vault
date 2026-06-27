# Python Venv Crash Cascade — 2026-06-13 Reference

**Source incident:** Mona VPS (43.163.85.51, VM-0-2-ubuntu, Ubuntu 24.04)
**Date:** 2026-06-13
**Recovered by:** user + Claude
**Caused by:** Mona suggested Python 3.12 swap without state verification

## Why This Reference Exists

The "Python venv crash" pattern is dangerous because each individual step looks like a reasonable fix in isolation. The cascade compounds into a 4-step mess requiring expert recovery. Future sessions must recognize the pattern early and check state before suggesting any change.

## The 4-Step Cascade

When the cascade is triggered, all 4 steps typically happen in sequence:

1. **uv + Python 3.11 deletion** → venv's symlinked `python3.11` binary becomes invalid (venv symlink break)
2. **`python3.12 -m venv --clear`** → wipes all installed packages in the venv
3. **pyvenv.cfg conflict** → config still references 3.11 (symlink) but interpreter is 3.12
4. **Systemd services fail to start** → WantedBy target issues, missing env vars, broken interpreter path

## Symptoms

- `python` or `python3` returns wrong version or fails
- Hermes/gateway services fail to start
- ImportError for installed packages
- `pyvenv.cfg` points to wrong or missing Python interpreter
- `/home/ubuntu/.venv/bin/python` symlink dangling or wrong target
- systemd unit shows `status=203/EXEC` or similar

## Detection Commands

Run these BEFORE suggesting any fix:

```bash
# 1. System context (don't assume which VPS)
hostname
cat /etc/os-release
curl -s --max-time 5 ifconfig.me

# 2. Python interpreter state
which python python3
python --version 2>&1
ls /usr/bin/python* /usr/local/bin/python* 2>/dev/null
pyenv versions 2>/dev/null
uv python list 2>/dev/null

# 3. Venv state
ls -la .venv/ 2>/dev/null
ls -la .venv/bin/python* 2>/dev/null
cat .venv/pyvenv.cfg 2>/dev/null
find . -name "pyvenv.cfg" 2>/dev/null | head

# 4. uv/pipx state
which uv pipx
uv --version 2>&1

# 5. Service state
systemctl --user list-units --type=service --state=running
systemctl --user status hermes-gateway 2>/dev/null
journalctl --user -u hermes-gateway --since "1 hour ago" --no-pager | tail -50

# 6. Symlink integrity
find .venv/bin -type l 2>/dev/null | xargs -I {} ls -la {} 2>/dev/null
```

## Fix Sequence (only after detection confirms the cascade)

1. **Verify available Python interpreters:**
   ```bash
   ls /usr/bin/python*
   uv python list
   pyenv versions 2>/dev/null
   ```

2. **Reinstall missing Python via uv (prefer 3.11 to match prior state):**
   ```bash
   uv python install 3.11
   ```

3. **Recreate venv — DO NOT use `--clear` on existing venv:**
   ```bash
   # Move old venv aside first (preserves anything recoverable)
   mv .venv .venv.broken.$(date +%s)
   uv venv .venv --python 3.11
   ```

4. **Reinstall packages:**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   # or with uv:
   uv pip install -r requirements.txt
   ```

5. **Verify pyvenv.cfg points to correct interpreter:**
   ```bash
   cat .venv/pyvenv.cfg
   # Should show: home = /path/to/correct/python3.11
   # And: version_info = 3.11.x.x
   ```

6. **Restart services:**
   ```bash
   systemctl --user daemon-reload
   systemctl --user restart <service-name>
   systemctl --user status <service-name>
   ```

7. **Verify everything works:**
   ```bash
   python -c "import hermes"  # or whatever the gateway uses
   curl -s http://localhost:port/health
   ```

## Prevention Rules

- **Never delete Python 3.11 from a system that has venvs referencing it.** Check first:
  ```bash
  find / -name "pyvenv.cfg" 2>/dev/null | xargs grep -l "3.11" 2>/dev/null
  ```
- **Never run `python3.12 -m venv --clear` on an existing venv.** Move aside first.
- **Use `uv` consistently** — it handles interpreter + venv + packages as one system, less drift.
- **Pin Python version in `.python-version` or pyproject.toml** to prevent drift.
- **Back up the venv before any "fix":** `cp -r .venv .venv.backup.$(date +%s)`

## Why This Is a Recurring Pattern

The cascade is dangerous because:
- Each step looks like a reasonable fix in isolation ("just reinstall Python", "just clear the venv")
- The fixes compound non-linearly — by step 3, root cause is buried
- Time to recover: 30-60 min minimum if state isn't backed up
- Trust cost: high — user has to bring in another agent (Claude) to fix Mona's mess

## Rule for Mona

If the user is on a production VPS (Mona, Hye-Jin, or any other) and reports Python/hermes/service issues:

1. **DO NOT** suggest version swaps, venv clears, reinstalls, or config changes without first running detection commands
2. **DO NOT** infer which VPS — verify with hostname + IP
3. **DO** ask "Mana VPS-nya? Mona, Hye-Jin, atau lain?" if unclear
4. **DO** offer the smallest reversible change with explicit rollback
5. **DO** respect "dengerin dulu" / "jangan gas dulu" — switch to listen mode

When in doubt: ask before acting. The user's trust is worth more than a quick fix.
