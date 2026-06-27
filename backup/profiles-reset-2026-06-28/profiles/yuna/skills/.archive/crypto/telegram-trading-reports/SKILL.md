---
name: telegram-trading-reports
description: "Format Binance futures positions and PnL as plain-text Telegram reports. NO markdown, NO HTML — Telegram-native style. User-validated layout: per-symbol blocks with Pair, Side, Size, Entry, Mark, Lev, Margin, PnL, ROI. Use for any Yuna trading snapshot destined for Telegram or terminal preview."
triggers:
  - telegram trading report
  - format futures snapshot
  - positions and pnl telegram
  - dozero snapshot
  - project violet snapshot
  - telegram plain text trading
  - telegram crypto format
---

# Telegram Trading Reports — Plain-Text Format

Yuna's user (Hexa) wants trading snapshots delivered to Telegram as **clean plain text** with a **fixed per-symbol block layout**. This is non-negotiable: NO markdown (`**bold**`, `*italic*`, `` `code` ``), NO HTML (`<b>`, `<pre>`, `<i>`), no monospaced code blocks. Telegram renders `**text**` as literal `**text**` when `parse_mode=""` is set, which is ugly and what the user is trying to avoid.

The format was established across 3 correction rounds on 2026-06-16:
1. **Round 1:** "fungsi format_for_telegram() sekarang output plain text (no `<b>`, no `<pre>`)" — strip all markup
2. **Round 2:** show 3-field mini layout (Entry / Mark / PnL)
3. **Round 3:** expand to full-detail block layout (Pair / Side / Size / Entry / Mark / Lev / Margin / PnL / ROI)
4. **Round 4 (project rename):** use "PROJECT VIOLET" instead of "DOZERO" everywhere

> Read this skill before writing any new Telegram trading output. The user will notice deviations.

## Format Spec (user-validated)

### Title line

```
📊 PROJECT VIOLET — POSISI & PNL
```

Single line, emoji + ALL-CAPS name + em-dash (— not -) + description. No box-drawing on title.

### Per-symbol block

For each active position, output one block like this:

```
━━━ ADAUSDT ━━━━━━━━━━━━
  Pair    : ADAUSDT
  Side    : LONG 🟢
  Size    : 42,445
  Entry   : $0.17670
  Mark    : $0.17700
  Lev     : 75x
  Margin  : $100.00
  PnL     : $+12.73 🟢
  ROI     : +12.73%
```

Rules:
- **Header:** `━━━ SYMBOL ━━━` — total width 24 chars including `━━━ `. Pad with `━` so width is consistent regardless of symbol name length.
- **Field labels:** 9 chars wide (incl. spaces), left-aligned, followed by ` : ` then value.
- **Indent:** 2 spaces for the field lines.
- **Blank line** between blocks.
- **Emoji indicator** appears TWICE per block: next to Side and next to PnL. Both must match.
  - 🟢 = profit
  - 🔴 = loss
  - ⚪ = flat (uPnL exactly 0)
- **Pair line shows FULL symbol** (e.g. `ADAUSDT`, not `ADA`). Hexa does NOT want the suffix stripped despite this being common shorthand.

### Summary block (always at end)

```
💰 TOTAL PnL : $+221.23 🟢
📊 TOTAL ROI : +25.27% 🟢

💼 Wallet    : $4,704.74 USDT (avail $2,867.07)
```

The `💰` and `📊` prefix emoji on totals are constant — don't vary them.

### Sort order

Sort by `uPnL` **descending** (winners on top). Within uPnL, larger absolute notional first.

### Number formatting

- **Quantity/Size:** comma-separated, drop `.00` if integer, else 2 decimals
  - `42,445` (integer)
  - `7,307.30` (decimal)
  - `345,987` (integer)
- **Entry/Mark price:** precision adapts to price magnitude
  - `< $1` → 5 decimals: `$0.01048`
  - `< $100` → 4 decimals: `$0.1767`
  - `≥ $100` → 2 decimals: `$100.00`
- **Margin / USD amounts:** `$X.XX` (2 decimals, comma thousands)
- **PnL:** signed, 2 decimals: `$+12.73` / `$-100.47`
- **ROI:** signed percent, 2 decimals: `+12.73%`
- **Lev:** integer + `x` suffix: `75x`

## Project name: PROJECT VIOLET

As of 2026-06-16, the project previously called "DOZERO" is renamed **PROJECT VIOLET** in all user-facing output. The internal code paths, file paths (`/home/ubuntu/dozero/...`), and PM2 process name (`dozero-auto`) keep the original `dozero` namespace — only the **display string** in Telegram output changes.

Always use:
- ✅ `📊 PROJECT VIOLET — POSISI & PNL`
- ❌ `📊 DOZERO.X — POSISI & PNL`

## Why this format (Hexa's reasoning)

- **Vertical per-symbol blocks** read cleanly on mobile Telegram (where horizontal tables wrap badly)
- **`━━━` dividers** are visible without being loud (heavier than `-` but lighter than `# Heading`)
- **Emoji indicators** scan at a glance — Hexa skims to find what's red first
- **No markdown** because Telegram's `parse_mode=""` is what the Yuna notification bot uses (no `parse_mode` parameter passed), so `**text**` would render as raw `**text**`
- **No `code` blocks** because monospace breaks line-wrapping on mobile

## Reusable Scripts

Three scripts are packaged with this skill in `scripts/`. They are the canonical implementations — re-use, don't re-implement.

### 1. `scripts/format_snapshot.py` — Format a snapshot dict to plain text

```bash
python3 scripts/format_snapshot.py              # Live snapshot from testnet
python3 scripts/format_snapshot.py --file snap.json  # From saved JSON
```

**Inputs:** testnet API (or saved JSON).
**Output:** plain-text Telegram-ready message.
**Functions exported:**
- `fetch_testnet_snapshot() -> dict` — pulls positions, today's PnL, balance from Binance testnet
- `format_for_telegram(snapshot: dict) -> str` — formats the dict per spec above
- `icon_for_pnl(pnl: float) -> str` — returns 🟢/🔴/⚪
- `format_qty(qty: float) -> str` — comma-separated, smart decimals
- `format_price(price: float) -> str` — auto-precision price formatter

### 2. `scripts/emergency_sl_placement.py` — Place emergency SL on unprotected positions

```bash
python3 scripts/emergency_sl_placement.py --pct 0.02   # 2% from current mark
python3 scripts/emergency_sl_placement.py --dry-run    # show what would happen
```

Tries to place 1 STOP_MARKET per active position at `-pct` from current mark. Useful for "I just realized SL/TP didn't get placed" recovery. **If testnet returns `-4045` for all positions, switch to script #3** (you cannot recover via SL on testnet).

### 3. `scripts/close_losers.py` — Close all losing positions

```bash
python3 scripts/close_losers.py                # close all uPnL < 0
python3 scripts/close_losers.py --keep POS     # keep a specific position running
```

Market reduceOnly close for positions with `uPnL < 0`. Winners (`uPnL > 0`) are kept running. Last-resort recovery when SL/TP cannot be placed (testnet `-4045` exhaustion).

## Anti-patterns (do NOT do this)

```text
❌ **ADAUSDT**            ← markdown bold renders as literal in plain mode
❌ <b>ADAUSDT</b>         ← HTML tags
❌ `Entry: $0.1767`       ← code block wraps and looks weird on mobile
❌ | ADAUSDT | LONG | ... ← markdown table breaks on narrow screens
❌ -221.23               ← missing $ sign and sign character
❌ ADA                   ← stripped suffix; user wants full symbol
❌ 📊 DOZERO.X — ...     ← old project name; use PROJECT VIOLET
```

## Pitfalls

1. **Don't drop the USDT suffix** — use `ADAUSDT` not `ADA`. Hexa explicitly uses full symbols.
2. **Don't sort alphabetically** — sort by `uPnL` descending. Winners go first.
3. **Don't use markdown headers** (`## Title`) — they don't render in plain-text mode and look broken.
4. **Don't use markdown tables** — they wrap terribly on mobile Telegram.
5. **Don't add explanatory text** between blocks. The format IS the message. No "Berikut posisi aktif Anda:" preamble.
6. **Always include both emojis** on the per-symbol block (Side line + PnL line). Visual scanability depends on the duplication.
7. **If snapshot is empty** (no positions), still output the title + a single line `Tidak ada posisi aktif.` Don't omit the title.

## Reference: When to use this format

- ✅ User asks for "posisi futures" / "snapshot" / "PnL sekarang"
- ✅ Cron job delivering periodic updates to a Telegram topic
- ✅ Post-trade execution notification (combine with `notifier.send_execution`)
- ❌ NOT for ad-hoc analysis in chat — those can use whatever formatting the LLM picks
- ❌ NOT for error/alarm messages — use single-line alert format instead
