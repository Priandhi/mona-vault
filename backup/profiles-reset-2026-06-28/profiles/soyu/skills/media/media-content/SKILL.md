---
name: "media-content"
description: "Hermes media toolset: GIFs, music generation, audio analysis, Spotify control, X article extraction, YouTube transcripts. One entry point for any media task."
tags:
  - media
  - gif
  - music
  - audio
  - spotify
  - youtube
  - x-twitter
  - transcript
---
# Media Content Tools

> Umbrella for all Hermes media skills: GIFs, music generation, audio analysis, social-media text, streaming.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "gif", "send a gif", "react with a gif" | `references/gif-search/` |
| "song", "lyrics", "heartmula", "generate music" | `references/heartmula/` |
| "spectrogram", "audio features", "mel", "mfcc" | `references/songsee/` |
| "spotify", "play", "queue", "playlist" | `references/spotify/` |
| "X article", "twitter article", "long-form post" | `references/x-article-content/` |
| "youtube transcript", "summarize video", "youtube thread" | `references/youtube-content/` |

## Topic Pages

- `references/gif-search/SKILL.md`
- `references/heartmula/SKILL.md`
- `references/songsee/SKILL.md`
- `references/spotify/SKILL.md`
- `references/x-article-content/SKILL.md`
- `references/youtube-content/SKILL.md`


## When NOT to Use Any of These

- For image generation (not GIFs), use the `ai-image-generation` skill.
- For Discord media bots, use the `telegram-bot-management` patterns adapted for Discord.
- For TTS / voice, use the `text_to_speech` tool directly, no skill needed.
