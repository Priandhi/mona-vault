# Discovery Recipe — Before You Scaffold

Run these BEFORE creating any directories. The point is to avoid producing a second/parallel workspace root when the operator already has one from a prior session.

## 1. Re-read injected memory

The persistent memory store is injected every turn. Scan it for any line that mentions:
- `workspace`, `-ops`, `home`, `root`
- The operator's name or handle
- Paths that begin with `~/` or `/home/`

If a workspace root is named there, treat it as authoritative until the operator says otherwise.

## 2. Probe the filesystem

```bash
# Top-level candidates in $HOME
ls -la ~/ 2>/dev/null | grep -iE "(workspace|ops|projects|work|build|sandbox)"

# Wider sweep — depth 2, common names
find ~ -maxdepth 2 -type d \
  \( -iname "*workspace*" -o -iname "*-ops" -o -iname "ops" \
     -o -iname "projects" -o -iname "builds" \) \
  2>/dev/null | head -20

# Any README at depth ≤ 2 that looks workspace-shaped
find ~ -maxdepth 2 -iname "README*" 2>/dev/null | head -10
```

## 3. Resolve conflict (memory says one thing, FS says another)

Common case: memory has `~/foo-ops/` but the FS has `~/foo-workspace/` too — usually because a prior session scaffolded a fresh tree without discovering.

Present BOTH to the operator and offer:
1. Keep the older one, retire the newer (rm or archive).
2. Keep the newer, migrate contents from the older.
3. Keep both — they serve different purposes (rare).

Do NOT pick silently. The operator decides which root is canonical, and you update memory accordingly (use `replace`, not `add`).

## 4. After resolution

Update memory in ONE entry with the canonical root + structure summary. If a competing entry exists, `replace` it. Never leave two parallel workspace entries in memory.
