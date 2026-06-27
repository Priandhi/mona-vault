# Discord Account Creation Automation

## Overview

Automated Discord account creation for airdrop farming. Uses Playwright CDP to control
Chrome browser + yescaptcha API to solve hCaptcha on signup.

**Script:** `~/.hermes/scripts/discord_creator.py`

## Requirements

- **yescaptcha API key** — stored in `vault/.yescaptcha_key` (JSON format)
- **Email addresses** — user provides pre-created emails
- **Chrome with CDP** — must be running with `--remote-debugging-port=9222`
- **Fluxbox window manager** — required for proper page rendering

## Flow

1. Navigate to `https://discord.com/register`
2. Fill email, display name, username, password
3. Set date of birth (random 18+ year)
4. Solve hCaptcha via yescaptcha API
5. Submit form
6. Check for "verify your email" confirmation
7. Save account data to `.discord_accounts.json`

## hCaptcha Solving Pattern

```python
import urllib.request, json

YCAPTCHA_API = "https://api.yescaptcha.com"
SITE_KEY = "a9b5fb07-92ff-493f-86fe-352a2803b3df"  # Discord's hCaptcha sitekey

# Create task
task_data = {
    "clientKey": API_KEY,
    "task": {
        "type": "HCaptchaTaskProxyless",
        "websiteURL": "https://discord.com/register",
        "websiteKey": SITE_KEY
    }
}
req = urllib.request.Request(
    f"{YCAPTCHA_API}/createTask",
    data=json.dumps(task_data).encode(),
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req, timeout=30)
result = json.loads(resp.read())
task_id = result["taskId"]

# Poll for result (every 3s, max 60 attempts)
for _ in range(60):
    time.sleep(3)
    poll_data = {"clientKey": API_KEY, "taskId": task_id}
    req = urllib.request.Request(
        f"{YCAPTCHA_API}/getTaskResult",
        data=json.dumps(poll_data).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    if result.get("status") == "ready":
        token = result["solution"]["gRecaptchaResponse"]
        break
```

## Token Injection

After solving, inject the token into the page:
```python
await page.evaluate(f"""() => {{
    const textarea = document.querySelector('textarea[name="h-captcha-response"]');
    if (textarea) {{
        textarea.value = '{captcha_token}';
        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
    }}
    if (window.hcaptcha) {{
        try {{ window.hcaptcha.execute(); }} catch(e) {{}}
    }}
}}""")
```

## Account Data Format

```json
{
  "email": "user@example.com",
  "username": "crypto1234",
  "password": "randomP@ss16chars",
  "status": "needs_verification",
  "created_at": "2026-06-07 21:00:00"
}
```

## Pitfalls

- **Phone verification trigger:** Discord often requires phone verification from datacenter IPs.
  No easy workaround — user must provide phone numbers or use residential proxies.
- **Rate limiting:** Add 30-60s random delay between account creations.
- **Email verification required:** User must click verification link in inbox before account is usable.
- **hCaptcha vs reCAPTCHA:** Discord uses hCaptcha, NOT reCAPTCHA. yescaptcha supports both
  but task type must be `HCaptchaTaskProxyless` (not `RecaptchaV2TaskProxyless`).
- **One tab per account:** Each signup should use a fresh page/tab to avoid cookie/state leakage.
- **Password generation:** Use 16+ chars with letters, digits, and special chars. Store in accounts JSON.
- **yescaptcha credits:** Each hCaptcha solve costs ~$0.002. Budget accordingly for bulk creation.

## Bulk Creation Pattern

```bash
# Create emails file
echo -e "email1@x.com\nemail2@x.com\nemail3@x.com" > /tmp/emails.txt

# Run creator
python3 ~/.hermes/scripts/discord_creator.py --file /tmp/emails.txt

# Check results
cat ~/.hermes/scripts/.discord_accounts.json
```

## Alternative: Single Discord + Multi-Server

For Galxe social tasks, often ONE Discord account joining multiple servers is sufficient.
This avoids the phone verification problem entirely:

1. Create or use existing Discord account
2. Join required servers via invite links
3. Complete "join Discord" tasks on Galxe with the single account
4. Use different EMAIL accounts for different Galxe profiles (not Discord)
