---
name: x-article-content
category: media
description: Extract content from X (Twitter) article URLs when login wall blocks direct access. Use when user shares x.com/<user>/status/<id> URL with article content and the body is not visible.
---

# X / Twitter Article Content Extraction

## When to use
User drops `https://x.com/<user>/status/<id>` and you need to read the article body. Direct browser/curl access to x.com returns login wall, OAuth gate, or JS-rendered empty shell. This skill bypasses that.

Trigger phrases from user: "baca ini", "pelajari", "cek tweet ini", "what does this say", "extract this article".

## Extraction pipeline (try in order)

### 1. Syndication API — get preview + cover image (FREE, no auth)
```bash
curl -sL "https://cdn.syndication.twimg.com/tweet-result?id=<STATUS_ID>&token=0" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('Text:', d.get('text'))
art = d.get('article', {})
print('Title:', art.get('title'))
print('Preview:', art.get('preview_text'))
print('Cover media:', art.get('cover_media'))
print('Conversation:', d.get('conversation_id'), 'replies:', d.get('conversation_count'))
"
```

Returns:
- `text` — tweet body (usually just the article URL + author commentary)
- `article.title` — article headline
- `article.preview_text` — first ~280 chars of article body (genuine preview, not the cover)
- `article.cover_media` — URL of the cover/hero image
- `conversation_id` / `conversation_count` — for drilling into replies

### 2. Cover image = often the FULL article as infographic
Most X long-form articles use a **cover image designed as a standalone summary** — author expects people to share the cover without the link. This is your gold mine.

```bash
curl -sL "<cover_media_url>" -o /tmp/cover.jpg
# file /tmp/cover.jpg   # confirm it's a real image, not HTML error
```

Then `vision_analyze` with:
> "Describe this infographic in detail. Extract ALL text, architecture diagrams, module names, principles, and key concepts. Be exhaustive — this IS the article content."

This often gives you 80–100% of the article because authors intentionally design the cover as a shareable standalone summary. In one verified case (Hermes + Obsidian article by @zaimiri), the cover image alone was sufficient to fully understand the article's architecture, modules, and principles.

### 3. Reply thread for additional context
Author sometimes posts the full text as a thread or follow-up. Use `tweet-result` on reply IDs surfaced from `conversation_id`:

```bash
# for each reply_id found in the thread
curl -sL "https://cdn.syndication.twimg.com/tweet-result?id=<REPLY_ID>&token=0"
```

Watch for: full article pasted in replies, author explaining a section, someone else summarizing.

### 4. Fallbacks if still insufficient
- **nitter.net** / **xcancel.com** / **nitter.poast.org** — mirrors, sometimes show full body
- **Wayback Machine**: `https://web.archive.org/web/*/https://x.com/<user>/status/<id>*`
- **Google cache**: `https://webcache.googleusercontent.com/search?q=cache:<url>`
- **Bing/Google index snippet**: search `site:x.com <user> <article-title>` for the indexed excerpt
- **Last resort**: ask user to copy-paste article body — don't pretend you have the full text

## Pitfalls
- **x.com direct (browser/curl)** → login wall, OAuth, JS-rendered. Don't waste time on this.
- **syndication.twimg.com 404** → tweet deleted, private, or shadow-banned. Verify with `curl -I` first.
- **Article body is NEVER in syndication response** — only `preview_text` (~280 chars). The cover image is the only way to get the rest without auth.
- **vision_analyze needs vision-capable model** — if the active model lacks vision, the result comes from an aux vision model and may be lower quality. Verify by reading the response critically.
- **Rate limits**: ~1 req/sec sustained on syndication endpoint. For batched reply extraction, add `sleep 1` between calls.
- **Cover image ≠ full article** — sometimes the cover is just a hero photo, not an infographic. If vision returns a photo with text overlay only, treat it as supplementary, not primary source.
- **Don't fabricate** — if the cover is a chart/diagram and `preview_text` is short, you likely don't have full text. State this honestly to the user.

## Verification checklist
Before reporting back, confirm you have:
- [ ] Article title (from syndication)
- [ ] At least one of: full body text OR comprehensive cover-image summary
- [ ] Source citation for every claim ("From preview: ...", "From cover image: ...", "From reply @...: ...")

## Output format
Always present with explicit sourcing so the user knows what came from where:
```
## 📰 Article: <title>
**Source:** x.com/<user>/status/<id>
**Extraction method:** <syndication preview / cover image / replies / fallback>

### <structured content here>
```

## Related
- `media/youtube-content` — same pattern for video URLs (transcript extraction)
- `hermes-web-search-config` — if you need to escalate to a search backend
