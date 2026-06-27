# MiMo Claude Code Integration — Full Documentation Reference

Source: https://platform.xiaomimimo.com/docs/en-US/integration/claudecode
Captured: 2026-06-10

## Prerequisites — Credential Acquisition

| Method | Description | BASE_URL | API Key |
|--------|-------------|----------|---------|
| Pay-as-you-go | Per-token billing | `https://api.xiaomimimo.com/anthropic` | `sk-xxxxx` from API Keys page |
| Token Plan | Fixed subscription | `https://token-plan-cn.xiaomimimo.com/anthropic` (China) or `https://token-plan-sgp.xiaomimimo.com/anthropic` (Singapore) | `tp-xxxxx` from Subscription page |

## Installation

```bash
npm install -g @anthropic-ai/claude-code
claude --version  # verify
```

Requires Node.js 18+. Linux/macOS default OK. Windows needs WSL or Git for Windows.

## Configuration — CLI

**File 1:** `~/.claude/settings.json`
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "BASE_URL",
    "ANTHROPIC_AUTH_TOKEN": "MIMO_API_KEY",
    "ANTHROPIC_MODEL": "mimo-v2.5-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "mimo-v2.5-pro",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "mimo-v2.5-pro",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "mimo-v2.5-pro"
  }
}
```

**File 2:** `~/.claude.json`
```json
{
  "hasCompletedOnboarding": true
}
```

Clear `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_BASE_URL` env vars before setup to avoid API conflicts.

## 1M Context Support

Append `[1m]` suffix to model ID: `mimo-v2.5-pro[1m]`
After configuration, restart Claude Code and run `/context` to verify.

## VS Code Plugin

Install "Claude Code for VS Code" from marketplace.

Settings → Claude Code: Environment Variables → settings.json:
```json
{
  "claudeCode.preferredLocation": "panel",
  "claudeCode.selectedModel": "mimo-v2.5-pro",
  "claudeCode.environmentVariables": [
    { "name": "ANTHROPIC_BASE_URL", "value": "BASE_URL" },
    { "name": "ANTHROPIC_AUTH_TOKEN", "value": "MIMO_API_KEY" },
    { "name": "ANTHROPIC_DEFAULT_SONNET_MODEL", "value": "mimo-v2.5-pro" },
    { "name": "ANTHROPIC_DEFAULT_OPUS_MODEL", "value": "mimo-v2.5-pro" },
    { "name": "ANTHROPIC_DEFAULT_HAIKU_MODEL", "value": "mimo-v2.5-pro" }
  ]
}
```

If CLI is already configured, VS Code plugin automatically reuses CLI config.

## FAQ

- Windows install fails → ensure Node.js 18+ and Git for Windows installed
- npm permission errors → run terminal as admin or use nvm
- Model deprecation notice: MiMo-V2-Pro/Omni auto-routes to V2.5 (with V2.5 pricing) as of June 1, 2026. Fully deprecated June 30.
