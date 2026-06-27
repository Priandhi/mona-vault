---
name: captcha
description: YesCaptcha bypass for browser automation — solve CAPTCHAs via YesCaptcha API.
triggers:
  - captcha
  - yescaptcha
  - recaptcha
  - hcaptcha
---

# Captcha Bypass — YesCaptcha

## Setup

1. Register at [yescaptcha.com](https://yescaptcha.com)
2. Get API key from dashboard
3. Set environment variable: `YESCAPTCHA_API_KEY=your_key_here`

## Usage

### Solve reCAPTCHA v2

```bash
curl -X POST "https://api.yescaptcha.com/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "clientKey": "YOUR_API_KEY",
    "task": {
      "type": "RecaptchaV2TaskProxyLess",
      "websiteURL": "https://example.com",
      "websiteKey": "6Ldxxxxxxxxxxxxxxxxxxxxxxxx"
    }
  }'
```

### Solve reCAPTCHA v3

```bash
curl -X POST "https://api.yescaptcha.com/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "clientKey": "YOUR_API_KEY",
    "task": {
      "type": "RecaptchaV3TaskProxyLess",
      "websiteURL": "https://example.com",
      "websiteKey": "6Ldxxxxxxxxxxxxxxxxxxxxxxxx",
      "minScore": 0.7,
      "pageAction": "verify"
    }
  }'
```

### Solve hCaptcha

```bash
curl -X POST "https://api.yescaptcha.com/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "clientKey": "YOUR_API_KEY",
    "task": {
      "type": "HCaptchaTaskProxyLess",
      "websiteURL": "https://example.com",
      "websiteKey": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
  }'
```

### Get Result (poll)

```bash
curl -X POST "https://api.yescaptcha.com/getTaskResult" \
  -H "Content-Type: application/json" \
  -d '{
    "clientKey": "YOUR_API_KEY",
    "taskId": "TASK_ID_HERE"
  }'
```

Poll every 3-5 seconds until `status: "ready"`. Timeout after 120s.

## Integration with Browser Automation

When browser hits CAPTCHA:

1. Extract `sitekey` from page: `document.querySelector('[data-sitekey]')`
2. Get current page URL
3. Call YesCaptcha API
4. Poll for result
5. Inject token: `document.getElementById("g-recaptcha-response").innerHTML = token`
6. Submit form

## Pricing

- reCAPTCHA v2: ~$0.001/solve
- reCAPTCHA v3: ~$0.001/solve
- hCaptcha: ~$0.001/solve

## Pitfalls

- Always use `RecaptchaV2TaskProxyLess` (no proxy needed)
- `minScore` for v3: use 0.7 for most sites, 0.3 for strict
- Token expires in ~120s — inject immediately
- Some sites use invisible reCAPTCHA — same method works

## ⚠️ Cloudflare Managed Challenge ≠ Turnstile widget (CRITICAL)

These are two **different** challenges. The captcha skill's earlier mention of a `CloudflareChallenge` task type is **wrong** — YesCaptcha has no such task. Empirically verified (Jun 2026, 8 task-type variants tested against `api.yescaptcha.com/createTask`, all returned `ERROR_TASK_NOT_SUPPORTED` or required a missing proxy+sitekey):

| Real challenge | URL pattern | Sitekey in DOM? | YesCaptcha task that works |
|---|---|---|---|
| **Turnstile widget** (visible) | Stays on app page, has `<div class="cf-turnstile" data-sitekey="0x...">` | ✅ yes (in `data-sitekey` or `cf-turnstile-response` hidden input) | `TurnstileTask` — requires `proxy` + `websiteKey` |
| **Cloudflare Managed Challenge** | Redirects to `https://<site>/cdn-cgi/challenge-platform/h/g/orchestrate/chl_page/v1?ray=...` | ❌ no sitekey, no Turnstile widget — JS observes fingerprint/behavior | **None.** No YesCaptcha task type accepts this URL pattern. |

**Managed Challenge detection (run in headless browser):**
- URL contains `/cdn-cgi/challenge-platform/` → Managed Challenge
- `document.body.innerText` contains "Performing security verification" + "Ray ID:" → Managed Challenge
- `document.querySelector('.cf-turnstile')` returns `null` AND URL is on the challenge platform → Managed Challenge
- Page stuck on "Verifying..." spinner forever → Managed Challenge (headless fingerprint failed behavioral check)

**Why it can't be solved headlessly:** Cloudflare's Managed Challenge runs JavaScript in-page that observes canvas/WebGL fingerprint, mouse movement, TLS handshake (JA3/JA4), and HTTP/2 fingerprint. Headless Chromium fails the behavioral check before any Turnstile widget renders — there's no sitekey to extract, so even a paying solver has nothing to feed the API. Free bypasses (WARP proxy, stealth scripts, user-agent spoofing, headless→headful switch) **all fail** because the gate happens before the widget loads.

**Real paths when you hit a Managed Challenge (verified Jun 2026):**
1. **Run the auth/signup in a real browser** — open in user's laptop/phone, complete flow, paste the resulting key/cookie to agent. Cheapest. ~5 min.
2. **Export auth cookies** from a browser where the user is already logged in, inject into Playwright via `context.add_cookies()`. Authed sessions skip the gate. ~3 min.
3. **CapSolver `AntiCloudflareTask`** — the only captcha service known to solve Managed Challenge (purpose-built). Requires a residential proxy + CapSolver API key. We don't have a CapSolver key in env as of Jun 2026.

**Detection script (run before attempting any YesCaptcha task):**
```python
url = page.url
body = page.evaluate("() => document.body.innerText") or ""
has_turnstile_widget = await page.evaluate("() => !!document.querySelector('.cf-turnstile, [data-sitekey]')")
if "/cdn-cgi/challenge-platform/" in url or "Performing security verification" in body:
    if not has_turnstile_widget:
        print("→ MANAGED CHALLENGE — YesCaptcha cannot solve this. Stop.")
        sys.exit(1)
else:
    sitekey = await page.evaluate("() => document.querySelector('[data-sitekey]')?.getAttribute('data-sitekey')")
    print(f"→ Turnstile widget, sitekey={sitekey} — YesCaptcha TurnstileTask may work")
```

Do **not** keep retrying `CloudflareChallenge` / `AntiCloudflareTask` / `AntiTurnstileTaskProxyLess` against YesCaptcha — they all return `ERROR_TASK_NOT_SUPPORTED`. Confirmed against the live API.
- **⚠️ IMPORTANT: Kimchi.dev signup uses Cloudflare TURNSTILE, not a simple image captcha.**

The pitfall at the bottom of this skill describes `ImageToTextTask` for "Kimchi.dev signup captcha (Jun 2026)". That refers to a **different, lower-stakes** Kimchi endpoint (likely account verification on a less-protected subdomain). The MAIN signup flow at `https://app.kimchi.dev/signup` is gated by **Cloudflare Turnstile** (behavioral challenge), which is NOT solvable by image OCR.

**How to detect Turnstile vs image captcha:**

| Signal | Turnstile | Image captcha |
|---|---|---|
| URL redirected to | `login.kimchi.dev/authorize?client_id=...` | Stays on signup page |
| Body text | "Performing security verification" + "Ray ID: ..." | Has an image + text input |
| Hidden input | `<input type="hidden" name="cf-turnstile-response">` | None |
| Visible inputs | 0 | Email + captcha text input |
| Cloudflare Ray ID | Present | Absent |

**If you hit Turnstile on a headless VPS, none of these work free:**
- ❌ WARP / SOCKS5 proxy (clean IP alone won't pass behavioral check)
- ❌ Stealth scripts (`navigator.webdriver`, `plugins`, `chrome.runtime`)
- ❌ Warmup to root page first
- ❌ Realistic User-Agent / locale / timezone
- ❌ Headless → headful switch
- ❌ ImageToTextTask (no image to OCR)

**Working bypass options (ranked cheapest→fastest):**

1. **User does manual signup** (free, 5 min) — open signup URL in user's real browser, complete form, get API key from dashboard, paste to agent.
2. **User runs `kimchi` CLI on local machine** (free, 10 min) — install on laptop, `kimchi login` does OAuth flow with localhost callback, paste resulting API key from `~/.config/kimchi/config.json` to agent.
3. **Export existing browser session cookies** (free, 3 min) — if user has ever logged into Kimchi in Chrome/Firefox, export cookies via DevTools → Network tab or cookie editor extension → agent injects via `context.add_cookies()` to bypass Turnstile (already-authed sessions skip bot check).
4. **YesCaptcha** (~$0.001/solve, ~$1 = 1000 solves) — for sites with a **visible Turnstile widget** in the DOM (not a Managed Challenge). The working task type is `TurnstileTask` — requires `proxy` (proxyType/proxyAddress/proxyPort) and the **sitekey** that is only exposed when a Turnstile widget is actually rendered in the page. See Cloudflare section below — Managed Challenges do not expose a sitekey and are not solvable through YesCaptcha at all.

**Setup step for headless VPS (for option 2):** Install `xdg-utils` so `kimchi login` doesn't crash with `ENOENT spawn xdg-open`:
```bash
sudo apt-get install -y xdg-utils
```
The CLI's OAuth flow opens a local server on `127.0.0.1:<random_port>` and tries to spawn a browser. With xdg-open present (even if no display), the spawn exits 0, the local server stays up, and the auth flow can complete via cloudflared tunnel or SSH port forward.

**Detection script:**
```python
body = page.evaluate("() => document.body.innerText")
if "Performing security verification" in body or "Ray ID:" in body:
    print("→ Cloudflare Turnstile, image OCR won't work")
elif page.query_selector("img[alt*='captcha' i]"):
    print("→ Image captcha, ImageToTextTask will work")
```
