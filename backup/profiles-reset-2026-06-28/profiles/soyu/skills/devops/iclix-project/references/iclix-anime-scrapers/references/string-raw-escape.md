# String.raw Escape Pattern (Recommended) — ADDENDUM

## The Cleaner Solution

If you find yourself counting backslashes, **stop and use `String.raw\`...\`` instead**. The JS template literal preserves backslashes verbatim, so you write Python code exactly as you would in a `.py` file.

```js
// With String.raw — write Python as you would in a .py file
const PY_SCRAPER = String.raw`
    import re
    m = re.search(r'episode\s*(\d+)', text)              # 1 backslash — DONE
    n = re.search(r'\bfoo\b', text)                      # 1 backslash — DONE
    p = re.search(r'background-image:\s*url\(', html)    # 1 backslash — DONE
`;
```

## Migration Recipe

**Before (counting backslashes, error-prone):**
```js
const PY_SCRAPER = `
    m = re.search(r'episode\\s*(\\d+)', text)
`;
```

**After (no counting):**
```js
const PY_SCRAPER = String.raw`
    m = re.search(r'episode\s*(\d+)', text)
`;
```

Just add `String.raw` before the backtick. Done.

## Two Exceptions That Still Bite

Python raw strings don't allow escaped quotes inside character classes. Replace with hex escapes:

| Want in Python | With String.raw JS | Result in file | Works? |
|---|---|---|---|
| `r'[^"\'<>\s]'` | `r'[^"\'<>\s]'` | `r'[^"\'<>\s]'` | NO: `\'` ends raw string |
| `r'[^"\x27<>\s]'` | `r'[^"\x27<>\s]'` | `r'[^"\x27<>\s]'` | YES: hex escape |
| `r'[^"<>\"]'` | `r'[^"<>\"]'` | `r'[^"<>\"]'` | NO: `\"` ends raw string |
| `r'[^"<>\x22]'` | `r'[^"<>\x22]'` | `r'[^"<>\x22]'` | YES: hex escape |

**Real example (animeunity vixcloud, June 2026):** JS source had `r'vixcloud\.co/embed/\d+[^"\\'<>\\s]*'`. With `String.raw`, that becomes `r'vixcloud\.co/embed/\d+[^"\'<>\s]*'`. In Python raw string, `\'` ends the string → SyntaxError. **Fix:** `r'vixcloud\.co/embed/\d+[^"\x27<>\s]*'` (use `\x27` for `'`, `\x22` for `"`).

## The Third Layer: page.evaluate Backslashes

`page.evaluate(jsBody)` sends the JS body to the browser, which interprets backslashes in string literals AGAIN. So `new RegExp('\\d+')` written in a Python triple-quoted string in a JS template literal goes through 3 layers:

| Layer | What happens |
|---|---|
| 1. JS template literal | `String.raw` preserves; otherwise `\\` → `\` |
| 2. Python `"""..."""` | `\\` → `\` |
| 3. Browser's JS parser | `\\` → `\`; `\d` (1 backslash) is "unknown escape" but kept as `\d` in string. Then `new RegExp('\d')` regex source shows `(d+)` (no backslash) — confusingly broken. |

**Empirical test:**
```bash
node -e "
const re = new RegExp('(\\d+)(?!\\d)');  // 1 backslash (4 chars in source: '\\\\d+')
console.log(re.source);  // (d+)(?!d) — BROKEN
const re2 = new RegExp('(\\\\d+)(?!\\\\d)');  // 2 backslashes (8 chars: '\\\\\\\\d+')
console.log(re2.source); // (\\\\d+)(?!\\\\d) — WORKS
"
```

**Reliable approach:** for `new RegExp()` with strings, always use 2 backslashes in source (4 in JS file with `String.raw`, 8 without). Or use a regex literal `/(\d+)/` directly — no string-literal escape issue.

**Hex-dump verification (fastest debug):**
```bash
sed -n '116p' /tmp/sh_scrape.py | xxd | head -3
# 5c 64 2b       = single backslash + d + +  → JS sees \d+, BROKEN
# 5c 5c 64 2b    = double backslash + d + +  → JS sees \\d+, WORKS
```

## Why Hex-Dump Is the Fastest Debug

When something returns 0 episodes / empty / SyntaxError, hex-dump the regex line in the Python file the browser would receive. Compare with a known-working version. The byte sequence tells you EXACTLY what each layer will see.

```bash
# Diff two versions of the same regex line byte-by-byte
diff <(sed -n '116p' /tmp/sh_scrape.py | xxd) <(sed -n '116p' /tmp/sh_manual.py | xxd)
```

If the bytes differ in the backslash positions, that's your bug.
