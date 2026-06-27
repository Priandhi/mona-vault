---
name: "browser-automation"
description: "Hermes browser automation stack: stealth CloakBrowser orchestration, headless VPS setup, captcha bypass, and extension configuration. Use when scraping, clicking, navigating, or running JS in a real browser."
tags:
  - browser
  - automation
  - scraping
  - playwright
  - selenium
  - captcha
  - headless
---
# Browser Automation

> Umbrella for Hermes browser tools: stealth CloakBrowser orchestration, headless VPS setup, captcha bypass, and CloakBrowser extension setup.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "browser", "scrape JS", "navigate", "click", "extract" | `references/browser-agent/` |
| "VPS browser", "headless browser", "Xvfb" | `references/browser-automation-vps/` |
| "captcha", "bypass captcha", "YesCaptcha" | `references/captcha/` |
| "cloakbrowser", "MetaMask in browser", "extension setup" | `references/cloakbrowser-setup/` |

## Topic Pages

- `references/browser-agent/SKILL.md` — Stealth-first browser automation using CloakBrowser
- `references/browser-automation-vps/SKILL.md` — CloakBrowser + Xvfb on headless VPS
- `references/captcha/SKILL.md` — YesCaptcha bypass for browser automation
- `references/cloakbrowser-setup/SKILL.md` — CloakBrowser + extensions (MetaMask, Rabby)

## Cross-Cutting Patterns

**Always start with `browser_navigate`** before any other browser action. The other tools (browser_click, browser_type, browser_snapshot) all require an initialized page.

**Use `browser_console(expression=...)` for data extraction** when the page DOM is too large for a snapshot (Telegram channels, GitHub tables, infinite-scroll feeds).

**Captcha shows up on browser navigations:** If the page redirects to a captcha challenge, load `references/captcha/` for the YesCaptcha bypass pattern.

**PITFALL: Headless detection on VPS.** Default Chromium gets blocked. Use CloakBrowser's stealth mode. If on a headless VPS, use the `browser-automation-vps` setup (Xvfb + x11vnc fallback).
