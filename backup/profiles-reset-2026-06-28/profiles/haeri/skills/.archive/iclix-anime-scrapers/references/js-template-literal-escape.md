# JS Template Literal → Python Source Escaping (CRITICAL)

## The Trap
When a Node.js script uses a template literal `` ` ` `` to embed a Python scraper, and `fs.writeFileSync()` writes that template to a `.py` file, **the backslashes are interpreted TWICE**:

1. Once by the JavaScript template literal parser
2. Once by the Python parser when the file is executed

## Mental Rule
> If you want N backslashes in the Python source code, write **2N backslashes** in the JS template literal.

## Concrete Examples

### Regex escapes
| Want in Python | Write in JS template literal | Result in file |
|---|---|---|
| `\s` (matches whitespace) | `\\s` | `\s` ✓ |
| `\d` (digit) | `\\d` | `\d` ✓ |
| `\b` (word boundary) | `\\b` | `\b` ✓ |
| `\.` (literal dot) | `\\.` | `\.` ✓ |
| `\w` | `\\w` | `\w` ✓ |
| `\s*` | `\\s*` | `\s*` ✓ |
| `\([^)]+\)` | `\\([^)]+\)` | `\([^)]+\)` ✓ |

### String literal escapes
| Want in Python | Write in JS template literal | Result in file |
|---|---|---|
| newline `\n` | `\\n` | `\n` ✓ |
| tab `\t` | `\\t` | `\t` ✓ |
| quote `\'` | `\\'` | `\'` ✓ |
| backslash `\\` | `\\\\` | `\\` ✓ |

## What Goes Wrong
If you write `r'\s'` (single backslash) in the JS template literal:
1. JS sees `\s` — this is an unrecognized escape in JS, so JS keeps both characters (`\` + `s`)
2. The file now contains literal `\` + `s` (1 char + 1 char = `\s` in the source)
3. Python sees `r'\s'` as a raw string and reads both characters as `\` and `s` — works fine!

The trap hits when:
- You want `\s` inside `r'...'` (raw string) — actually safe in raw strings
- You want `\\s` in a regular string (2 backslashes) — Python interprets as `\s` (1 backslash + s) — DANGEROUS

**The actual trap is in JS template literal interpretation:**
- JS `'\\\\n'` = `\\n` (2 chars in JS string) → file gets `\\n` (2 chars) → Python sees `\\n` → interprets as `\n` (newline) — WRONG, you wanted literal `\\n`
- JS `'\\n'` = `\n` (1 char newline) → file gets `\n` (newline) → Python sees broken string

**Cleanest mental model:**
- Count the backslashes you want Python to SEE
- Multiply by 2
- Write that many in the JS template literal
- Verify by reading the actual file with `cat -A` or `xxd`

## Verification Step (ALWAYS do this)
After `writeFileSync(templateString, '/tmp/scraper.py')`:
```bash
# Should show backslashes exactly as Python expects
sed -n '42p' /tmp/scraper.py | cat -A

# OR for binary view
sed -n '42p' /tmp/scraper.py | xxd | head -3
```

If the file has `s*` instead of `\s*`, your JS source had `s*` (no backslash). Fix the JS source.

## Common Fixes

### Problem: `r'background-image:\s*url\(...'` in JS
**File gets:** `r'background-image:s*url(...'` (no backslash)
**Python error:** `SyntaxError: unterminated string literal`

**Fix:** Double-escape in JS:
```js
r'background-image:\\s*url\\([\"\\']?(https?:[^\"\\')]+)'
```

### Problem: Page evaluate with regex string
**JS source:**
```js
const og = await page.evaluate("() => document.querySelector('meta[property=\\\"og:image\\\"]')?.content || ''")
```

In the JS file (after 1 level of escape): `meta[property=\"og:image\"]` (with escaped quotes)
In Python: `meta[property="og:image"]` (quotes unescaped) ✓

Each `\\\"` in the JS template literal becomes `\"` in the file, which Python sees as just `"` (unescaped, since the string is in single quotes).

## Real Debugging Transcript (June 2026)
```
error: exit 1:   File "/tmp/au_scrape.py", line 43
    bg = re.search(r'background-image:s*url(["']?(https?://img.animeunity.so/[^"')]+)', seg)
                                                                                        ^
SyntaxError: unterminated string literal (detected at line 43)
```

Root cause: JS template literal had `r'background-image:\s*url\(...'` (1 backslash). JS preserved `\s` as 2 chars in the file. Python `r'...\s...'` in raw string should work... unless something else broke. The `\\\'` in `[^\\'\\')]+` is the real culprit — the backslash before the closing quote is escaping it.

**Lesson:** when in doubt, double EVERYTHING.
