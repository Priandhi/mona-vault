---
name: telegram-bot-management
description: Manage Telegram bots via Bot API — set profile photo, update name/description, manage forum topics, send messages with media. Use when user asks to update bot appearance, configure topics, or send files via Telegram bot.
when_to_use:
  - User wants to change bot profile picture (PFP)
  - User wants to update bot name or description
  - User wants to create/manage forum topics
  - User wants to send files, images, or media via Telegram bot
---

# Telegram Bot Management

## Set Bot Profile Photo (setMyProfilePhoto)

**CRITICAL:** The endpoint is `setMyProfilePhoto`, NOT `setMyPhoto` (which returns 404).

The API expects an `InputProfilePhotoStatic` object, not a raw file upload.

### Correct format (Python httpx):

```python
import base64, os, httpx, json

vault_path = os.path.expanduser('~/mona-workspace/vault/.telegram_bot')
with open(vault_path) as f:
    raw = f.read().strip()
bot_token = base64.b64decode(raw).decode()

with open('image.jpg', 'rb') as f:
    image_data = f.read()

url = f'https://api.telegram.org/bot{bot_token}/setMyProfilePhoto'
# KEY: file field name must DIFFER from 'photo' parameter name
files = {'mona_photo': ('photo.jpg', image_data, 'image/jpeg')}
data = {'photo': json.dumps({"type": "static", "photo": "attach://mona_photo"})}

response = httpx.post(url, files=files, data=data, timeout=30)
```

### Why this works:
- Telegram API expects `photo` parameter to be a JSON object (`InputProfilePhotoStatic`)
- The JSON references the uploaded file via `attach://<field_name>`
- The file field name in `files=` must match the `attach://` reference, NOT the parameter name
- Format: `{"type": "static", "photo": "attach://<file_field_name>"}`

### Verify:
```python
r = httpx.get(f'https://api.telegram.org/bot{bot_token}/getMe').json()
bot_id = r['result']['id']
r2 = httpx.get(f'https://api.telegram.org/bot{bot_token}/getUserProfilePhotos?user_id={bot_id}').json()
print(f"Total photos: {len(r2['result']['photos'])}")
```

## Multi-Bot Pinning in Forum Groups

When you have **multiple bots** in the same Telegram forum group (e.g., Mona @Monaa_Ai_Bot + DinoCantik @DinoCantik_Bot), each bot can ONLY pin messages it sent. The Hermes `send_message` tool always uses the Mona bot.

**Pattern: Send + Pin from a specific bot:**

```bash
# Source the CORRECT bot's .env
source ~/mona-workspace/meridian/.env 2>/dev/null  # DinoCantik token

# Send to specific topic with message_thread_id
RESULT=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"-1003899936547","message_thread_id":947,"text":"🌊 **DASHBOARD**\nhttps://xxx.lhr.life","parse_mode":"Markdown"}')

# Extract message_id
MSG_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['message_id'])")

# Pin it (same bot token!)
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/pinChatMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\":\"-1003899936547\",\"message_id\":${MSG_ID}}"
```

**Bot token locations:**
| Bot | Token Location |
|-----|---------------|
| Mona (@Monaa_Ai_Bot) | `~/.hermes/.env` → `TELEGRAM_BOT_TOKEN` |
| DinoCantik (@DinoCantik_Bot) | `~/mona-workspace/meridian/.env` → `TELEGRAM_BOT_TOKEN` |
| Charon Sniper | `~/mona-workspace/charon-sniper/config.json` → `telegram.botToken` |

**Common mistake:** Sending with Mona bot (via `send_message`) then trying to pin with DinoCantik token → "message to pin not found". Each bot can only pin its OWN messages.

**Dashboard link delivery pattern (user preference):**
User wants dashboard links sent AND PINNED in their respective Telegram topics. Always do send+pin as one atomic operation. Unpinned links get buried in chat history.

## Pitfalls

- **Bot token stored as base64** in vault OR plain text in `.env`. See `references/bot-token-retrieval.md` for both patterns.
- **Shell quoting with JSON** — always use Python for Telegram API calls, not curl with inline JSON. See `references/bot-token-retrieval.md` for pitfalls.
- **setMyPhoto does NOT exist** — always use `setMyProfilePhoto`
- **Telegram auto-crops PFP to circle** — full-body/landscape images get badly cropped. Use square or face-focused images for bot PFP.
- **Replacing PFP** — setMyProfilePhoto replaces the current photo (only 1 at a time on bot accounts)
- **Rate limits** — Telegram allows ~30 requests/second per bot, but PFP changes may be rate-limited more aggressively
- **Multi-bot pin fails silently:** If you send a message with Bot A then pin with Bot B's token, you get "message to pin not found". Always use the SAME bot's token for send+pin.
- **Hermes send_message = Mona bot only:** The `send_message` tool in Hermes always uses the Mona bot. For other bots, use curl/Python with their respective token from .env.

## Send Message with Custom Emoji (Premium)

Bots can send custom emoji from Telegram emoji packs. The emoji render as animated/premium versions.

### Requirements
1. Get emoji pack IDs via `getStickerSet?name={pack_name}`
2. Build `entities` array with `type: "custom_emoji"` entries
3. Send via **JSON body** (NOT form-urlencoded) to include entities

### Implementation
```python
def send_premium_message(topic_id, text, entities=None, parse_mode="HTML"):
    """Send message with custom emoji entities."""
    if parse_mode == "HTML":
        text = _sanitize_html(text)
    if len(text) > 4000:
        text = text[:3990] + "\n\n... <i>(truncated)</i>"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "message_thread_id": topic_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    if entities:
        payload["entities"] = json.dumps(entities)

    # MUST use JSON body for entities support
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    # ... error handling same as send_message
```

### Fetch Pack Emoji IDs
```python
url = f"https://api.telegram.org/bot{token}/getStickerSet?name=CryptachEmoji4"
resp = urllib.request.urlopen(urllib.request.Request(url), timeout=15)
data = json.loads(resp.read())
# Each sticker: {"emoji": "💎", "custom_emoji_id": "5345934...", "type": "custom_emoji"}
```

### Pitfalls
- **form-urlencoded CAN'T encode nested arrays** — `entities` must be sent via JSON body
- **parse_mode + entities coexist** — HTML applies to non-entity text, entities override emoji rendering
- **Variation selectors** — `🛡️` (U+FE0F) vs `🛡` are different codepoints; check which the pack has
- **ZWJ sequences** — `👨‍💻` vs `🧑‍💻` are different; verify which exists in pack

## Forum Topic Creation + Pinned Guide Pattern

When creating a topic that represents a category (e.g., "🔧 DEV & TOOLS"), pin a guide message explaining the topic's purpose and sub-topics:

```bash
TOKEN=$(base64 -d ~/mona-workspace/vault/.telegram_bot 2>/dev/null)
CHAT_ID="-1003899936547"

# 1. Create topic
TOPIC_ID=$(curl -s -X POST "https://api.telegram.org/bot${TOKEN}/createForumTopic" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": \"${CHAT_ID}\", \"name\": \"🔧 DEV & TOOLS\", \"icon_color\": 13338331}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['message_thread_id'])")

# 2. Send guide message
MSG_ID=$(curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"${CHAT_ID}\",
    \"message_thread_id\": ${TOPIC_ID},
    \"text\": \"🔧 **DEV & TOOLS**\\n\\n📌 **Panduan Topic Ini:**\\n\\n🔧 **Dev Discussion** — Tech talk, code\\n🧪 **Testing** — Test results, sandbox\\n📦 **Scripts** — Automation scripts\",
    \"parse_mode\": \"Markdown\"
  }" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['message_id'])")

# 3. Pin the guide
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/pinChatMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": \"${CHAT_ID}\", \"message_id\": ${MSG_ID}, \"disable_notification\": true}"
```

**Telegram Forum Limitation:** Topics are flat (no nesting). "DEV & TOOLS" with sub-topics (Dev Discussion, Testing, Scripts) can only be represented as a pinned guide message, not actual nested topics.

## Forum Topic Creation

Bot must be **admin** with **"Manage Topics"** permission enabled. Just being admin is NOT enough.

```python
import requests
resp = requests.post(
    f'https://api.telegram.org/bot{token}/createForumTopic',
    json={'chat_id': chat_id, 'name': '📈 Futures Trading', 'icon_color': 0x6FB9F0}
)
topic_id = resp.json()['result']['message_thread_id']
```

**Common error: "not enough rights to create a topic"**
- Check bot status: `getChatMember` → must show `status: "administrator"`
- Check `can_manage_chat` and `can_manage_topics` must be True
- If bot shows as `status: "member"` → user promoted wrong bot or didn't enable Manage Topics

**Indonesian UI flow for user:**
1. Open group → Members → Find bot (e.g., @Monaa_Ai_Bot)
2. Promote to Admin
3. Enable "Manage Topics" / "Kelola Topik" permission
4. Then retry topic creation

## Forum Topic Icon Customization

Change a topic's animated icon via `editForumTopic` with `icon_custom_emoji_id`. Requires the bot to be admin with Manage Topics permission.

### Get Available Icons

Telegram provides ~100 animated topic icons via `getForumTopicIconStickers`. Each sticker has an `emoji`, `custom_emoji_id`, and animation metadata.

```bash
curl -s "https://api.telegram.org/bot${TOKEN}/getForumTopicIconStickers" | \
  python3 -c "
import json, sys
for s in json.load(sys.stdin)['result']:
    print(f\"{s['emoji']}  →  {s['custom_emoji_id']}\")
"
```

### Edit Topic Icon

```bash
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/editForumTopic" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "-100XXXXXXXXXX",
    "message_thread_id": 947,
    "icon_custom_emoji_id": "5350305691942788490"
  }'
```

### Common Icon Mappings (good for crypto/trading bots)
| Emoji | ID | Best For |
|-------|-----|----------|
| 📈 | 5350305691942788490 | Trading, charts |
| 💎 | 5309958691854754293 | Alpha, sniping |
| 🔥 | 5312241539987020022 | Hot signals |
| ⚡️ | 5312016608254762256 | Fast execution |
| 💰 | 5350452584119279096 | PnL, money |
| 🤖 | 5309832892262654231 | Bots, automation |
| 🧠 | 5237889595894414384 | AI, analysis |
| 🏆 | 5312315739842026755 | Leaderboard |
| 🔮 | 5350367161514732241 | Predictions |
| 📰 | 5434144690511290129 | News, feeds |
| 📝 | 5373251851074415873 | Notes, logs |
| 🔎 | 5309965701241379366 | Research |
| 📣 | 5309984423003823246 | Announcements |
| 💬 | 5417915203100613993 | Chat, discussion |
| ✍️ | 5238156910363950406 | Writing, drafts |
| ✅ | 5237699328843200968 | Tasks, done |

### Pitfalls
- **Only custom emoji IDs work** — regular Unicode emoji can't be set via API; use `icon_custom_emoji_id`, not `icon_emoji`
- **Bot must have Manage Topics** — same permission as creating topics
- **Silent failure possible** — if the emoji ID doesn't exist, API may return `ok:true` but icon stays unchanged
- **Premium animated icons** — all icons from `getForumTopicIconStickers` are animated; they render as static for non-premium users

## Send Message Best Practices

```python
def _sanitize_html(text):
    """Clean HTML to prevent Telegram parse errors."""
    import re
    # Fix unclosed tags
    for tag in ['b', 'i', 'code', 'pre', 'a']:
        opens = len(re.findall(f'<{tag}[ >]', text))
        closes = len(re.findall(f'</{tag}>', text))
        if opens > closes:
            text += f'</{tag}>' * (opens - closes)
    # Remove broken entities
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    # Fix angle brackets in non-tag contexts
    text = re.sub(r'<(?!/?(b|i|code|pre|a|em|strong|u|s|strike|del|ins|u)[ >])', '&lt;', text)
    return text

def send_message(topic_id, text, parse_mode="HTML"):
    ## Send Message Best Practices

    4-layer defense against HTTP 400 errors. See `references/send-message-robust.md` for full implementation.

    ```python
    def send_message(topic_id, text, parse_mode="HTML"):
        # 1. HTML sanitization (PREVENT errors) — fix unclosed tags, stray <, broken &
        if parse_mode == "HTML":
            text = _sanitize_html(text)
        # 2. Auto-truncate (Telegram limit = 4096)
        if len(text) > 4000:
            text = text[:3990] + "\n\n... <i>(truncated)</i>"
        # 3. Disable web preview (clutters alerts)
        payload["disable_web_page_preview"] = True
        # 4. HTML fallback on parse errors (RECOVER)
        try:
            # send with HTML
        except Exception as e:
            error_body = ''
            if hasattr(e, 'read'):
                try: error_body = e.read().decode()[:200]
                except: pass
            print(f"[ERROR] send_message: {e} | body: {error_body}")
            payload["parse_mode"] = ""
            # retry without HTML
    ```

    **HTML parse errors** happen when token names contain `<`, `>`, `&` or unmatched tags. The `_sanitize_html()` function prevents most of these — the fallback catches the rest. Always log the error body for debugging.
        print(f"[ERROR] send_message: {e} | body: {error_body}", file=sys.stderr)
        payload["parse_mode"] = ""
        # retry without HTML
```

**HTML parse errors** happen when:
- Token names contain `<`, `>`, `&` or unmatched tags
- Chinese/Unicode characters in token names (e.g., `锄头`)
- Unclosed `<b>`, `<i>`, `<code>` tags from dynamic content

Always sanitize BEFORE sending, not just retry on failure.
