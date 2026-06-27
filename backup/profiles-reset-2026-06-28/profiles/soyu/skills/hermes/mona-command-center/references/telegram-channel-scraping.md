# Telegram Channel Scraping via Browser

## When to Use

Scrape public Telegram channels for: airdrop monitoring, alpha signals, news aggregation, KOL tracking. No API key needed — uses public web preview.

## URL Pattern

```
https://t.me/s/<channel_username>
```

Examples:
- `https://t.me/s/airdropfind` — Airdrop Finder (593K subs)
- `https://t.me/s/airdropindo` — Indonesian airdrop channel
- `https://t.me/s/cryptohunter` — Crypto alpha channel

## Extraction Script

Use `browser_console` with this JavaScript to extract structured post data:

```javascript
const posts = document.querySelectorAll('.tgme_widget_message_wrap');
const results = [];
posts.forEach((post) => {
  const textEl = post.querySelector('.tgme_widget_message_text');
  const linkEls = post.querySelectorAll('.tgme_widget_message_text a');
  const dateEl = post.querySelector('.tgme_widget_message_date time');
  const viewsEl = post.querySelector('.tgme_widget_message_views');
  if (textEl) {
    const links = Array.from(linkEls).map(a => ({text: a.textContent, href: a.href}));
    results.push({
      date: dateEl ? dateEl.textContent : 'N/A',
      views: viewsEl ? viewsEl.textContent : 'N/A',
      text: textEl.textContent.substring(0, 400),
      links: links
    });
  }
});
JSON.stringify({total: results.length, posts: results.slice(0, 20)}, null, 2);
```

## DOM Selectors Reference

| Element | Selector |
|---------|----------|
| Post container | `.tgme_widget_message_wrap` |
| Message text | `.tgme_widget_message_text` |
| Links in text | `.tgme_widget_message_text a` |
| Post date | `.tgme_widget_message_date time` |
| View count | `.tgme_widget_message_views` |
| Author name | `.tgme_widget_message_author_name` |
| Post link | `.tgme_widget_message_date` (parent `a` href = post URL) |
| Image | `.tgme_widget_message_photo_wrap img` |

## Filtering Patterns

### Airdrop keywords (Indonesian)
```
airdrop, whitelist, claim, eligible, register, early access, quest, 
reward, free mint, garapan, daftar, gabung, selesai, done
```

### Skip patterns
```
news, berita, artikel, meme, joke, "akhirnya JP", admin, iklan, 
advertisement, sponsored
```

## Pitfalls

1. **`web_extract` fails** on `t.me/s/` URLs — always use browser tools
2. **`browser_snapshot(full=True)` truncates** large pages — use `browser_console` JS extraction instead
3. **Lazy loading** — page only loads ~20 posts initially. Scroll + re-extract for more
4. **Rate limiting** — don't scrape too frequently. Every 1-5 hours is safe
5. **Channel must be public** — private channels don't have `/s/` preview
6. **View counts** may not be immediately visible — they load asynchronously
7. **Text truncation** — `textEl.textContent` may include emoji/special chars. Use `.substring(0, 400)` to cap

## Cron Job Template

```yaml
action: create
schedule: "every 5h"  # adjust per channel activity
deliver: "telegram:<chat_id>:<topic_id>"
enabled_toolsets: ["browser"]
name: "Channel Scanner - @<channel>"
prompt: |
  Scan Telegram channel @<channel> for latest [content type].
  
  STEPS:
  1. browser_navigate to https://t.me/s/<channel>
  2. browser_console with JS extraction script
  3. Filter actionable posts only
  4. Format as clean report with:
     - Title with emoji
     - Timestamp
     - Each item with name, reward/steps, links, engagement
     - HOT picks highlighted
  5. Final response = the report (auto-delivered to Telegram)
```

## Example: Airdrop Report Format

```
🪂 AIRDROP UPDATE — @airdropfind
📅 5 Juni 2026, 17:00 WIB

🔥 HOT PICKS:
1. Router Protocol — $10K pool
   🪂 https://www.gatedex.com/...
   Steps: Connect → Trade $10 → Complete Tasks
   👁️ 6.26K views

2. LOST52 — Whitelist
   🪂 https://www.lost52.xyz/
   Steps: Register → Tasks → Submit EVM
   👁️ 12K views

📊 UPDATE:
- Tea Eligibility: https://itn.tea.xyz/
- DSCVR Claim: https://dscvr.one/airdrop-hub
```
