# Telegram Bot Profile Photo

## Correct API: setMyProfilePhoto (NOT setMyPhoto)

The `setMyPhoto` endpoint does NOT exist (returns 404). The correct method is `setMyProfilePhoto`.

## Parameter Format

The API expects an `InputProfilePhoto` object, NOT a raw file upload.

For static JPG photos, use `InputProfilePhotoStatic`:
```json
{
  "type": "static",
  "photo": "attach://<file_attach_name>"
}
```

## Working Code

```python
import base64, os, httpx, json

# Read base64-encoded token from vault
with open(os.path.expanduser('~/mona-workspace/vault/.telegram_bot')) as f:
    bot_token = base64.b64decode(f.read().strip()).decode()

# Read image
with open('photo.jpg', 'rb') as f:
    image_data = f.read()

url = f'https://api.telegram.org/bot{bot_token}/setMyProfilePhoto'

# KEY: file under CUSTOM field name, photo parameter references it via attach://
files = {'mona_photo': ('photo.jpg', image_data, 'image/jpeg')}
data = {'photo': json.dumps({"type": "static", "photo": "attach://mona_photo"})}

response = httpx.post(url, files=files, data=data, timeout=30)
print(response.json())  # {'ok': True, 'result': True}
```

## Why Other Approaches FAIL

| Attempt | Result | Why |
|---------|--------|-----|
| `setMyPhoto` | 404 Not Found | Endpoint doesn't exist |
| `setMyProfilePhoto` with `files={'photo': ...}` | 400 "photo isn't specified" | API expects `photo` to be JSON, not a file |
| `setMyProfilePhoto` with `files={'photo': ...}, data={'photo': json_config}` | 400 "photo must be uploaded as a file" | Conflict: `photo` is both file and JSON |
| **Correct**: `files={'custom_name': ...}, data={'photo': json_config}` | ✅ Works | File under different name, `photo` is pure JSON referencing it via `attach://` |

## Verify Photo Was Set

```python
# Get bot ID
r = httpx.get(f'https://api.telegram.org/bot{token}/getMe').json()
bot_id = r['result']['id']

# Check photos
r2 = httpx.get(f'https://api.telegram.org/bot{token}/getUserProfilePhotos?user_id={bot_id}').json()
print(f"Total photos: {len(r2['result']['photos'])}")  # Should be >= 1
```

## python-telegram-bot Library

The `python-telegram-bot` library does NOT have `set_my_photo` or `set_my_profile_photo` method. Available photo-related methods: `send_photo`, `set_chat_photo`, `set_business_account_profile_photo`. For bot profile photo, use raw httpx/requests.

## Telegram Auto-Crop

Telegram crops bot profile photos to a circle (~256px). Detail-heavy images may lose important parts. Use close-up facial shots or simple compositions for best results.
