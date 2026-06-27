> Migrated from `claude-code-mimo-setup` (consolidated June 2026).

# Claude Code + MiMo API Setup

Use Claude Code interface with MiMo API backend — same powerful coding agent, much cheaper.

## Two Usage Methods

| Method | Description | BASE_URL | API Key Format |
|--------|-------------|----------|----------------|
| Pay-as-you-go | Charged per token | `https://api.xiaomimimo.com/anthropic` | `sk-xxxxx` |
| Token Plan (China) | Fixed subscription | `https://token-plan-cn.xiaomimimo.com/anthropic` | `tp-xxxxx` |
| Token Plan (Singapore) | Fixed subscription | `https://token-plan-sgp.xiaomimimo.com/anthropic` | `tp-xxxxx` |

**⚠️ Regional endpoints matter!** Token Plan keys are region-specific. A Singapore key (`tp-xxxxx`) MUST use `token-plan-sgp.xiaomimimo.com`, NOT `token-plan-cn`. Using the wrong region returns 401 or empty responses. Check your MiMo console → Subscription page for your region's BASE_URL. Pay-as-you-go keys (`sk-xxxxx`) use the global endpoint regardless of region.

## Quick Setup

```bash
# 1. Install Claude Code (may need sudo on Linux)
sudo npm install -g @anthropic-ai/claude-code

# 2. Create settings
mkdir -p ~/.claude
cat > ~/.claude/settings.json << 'EOF'
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.xiaomimimo.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_MIMO_API_KEY",
    "ANTHROPIC_MODEL": "mimo-v2.5-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "mimo-v2.5-pro",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "mimo-v2.5-pro",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "mimo-v2.5-pro"
  }
}
EOF

# For Token Plan Singapore, use:
# "ANTHROPIC_BASE_URL": "https://token-plan-sgp.xiaomimimo.com/anthropic"

# 3. Mark onboarding complete
echo '{"hasCompletedOnboarding": true}' > ~/.claude.json

# 4. Verify installation
claude --version

# 5. Test connection
claude -p "Say hello"
```

## 1M Context Support

Append `[1m]` suffix to model ID:
```json
"ANTHROPIC_MODEL": "mimo-v2.5-pro[1m]"
```

## VS Code Plugin

Install "Claude Code for VS Code" from marketplace, then configure environment variables in settings.json:

```json
{
  "claudeCode.preferredLocation": "panel",
  "claudeCode.selectedModel": "mimo-v2.5-pro",
  "claudeCode.environmentVariables": [
    {
      "name": "ANTHROPIC_BASE_URL",
      "value": "https://api.xiaomimimo.com/anthropic"
    },
    {
      "name": "ANTHROPIC_AUTH_TOKEN",
      "value": "YOUR_MIMO_API_KEY"
    },
    {
      "name": "ANTHROPIC_DEFAULT_SONNET_MODEL",
      "value": "mimo-v2.5-pro"
    },
    {
      "name": "ANTHROPIC_DEFAULT_OPUS_MODEL",
      "value": "mimo-v2.5-pro"
    },
    {
      "name": "ANTHROPIC_DEFAULT_HAIKU_MODEL",
      "value": "mimo-v2.5-pro"
    }
  ]
}
```

**Note:** If Claude Code CLI is already configured, the VS Code plugin automatically reuses CLI configuration.

## Pitfalls

See also: `references/mimo-claudecode-docs.md` for full upstream documentation.

- Clear `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_BASE_URL` env vars before setup to avoid conflicts
- Requires Node.js 18+
- On Windows: need WSL or Git for Windows
- **npm permission error on Linux:** If `npm install -g` fails with EACCES, use `sudo npm install -g @anthropic-ai/claude-code`
- **Regional endpoint mismatch:** Token Plan keys are region-specific. Singapore keys (`tp-xxxxx`) MUST use `https://token-plan-sgp.xiaomimimo.com/anthropic`. China keys use `https://token-plan-cn.xiaomimimo.com/anthropic`. Wrong region = 401 or empty responses. Check your MiMo Subscription page for the correct endpoint.
- **Verify with test command:** After setup, run `claude -p "Say hello"` to confirm the API connection works. A successful response proves BASE_URL + API_KEY + model are all correct.
- **1M context requires restart:** After changing model to `mimo-v2.5-pro[1m]`, restart Claude Code and run `/context` to verify extended context is active.
- **Timeout for longer responses:** When using `claude -p` for complex tasks (code generation, test generation), the default timeout may not be enough. Use `timeout 120 claude -p "task"` or set a generous timeout in Hermes terminal. Short tasks (< 30 words) complete in 5-10s; longer tasks (full test suites, multi-file refactors) can take 30-90s.
- **Testing feature works great:** Claude Code + MiMo API successfully generates unit tests, code reviews, and refactoring suggestions. Tested Jun 2026: generated 18 pytest test cases for trading functions in ~10s.
- **Code analysis pattern:** For analyzing existing codebases, use SHORT focused queries instead of broad analysis. Example: "Apa masalah di token-filter.js?" works better than "Analisis semua kode di folder ini". Broad queries timeout; focused queries return detailed analysis.
- **Incremental analysis strategy:** Instead of asking Claude to analyze everything at once, break it down: (1) List files and their purposes, (2) Ask about specific files, (3) Ask about specific issues. This avoids timeouts and gets better results.
- **Bug hunting workflow:** Claude Code excels at finding bugs when given specific files. It identified 5 critical issues in token-filter.js and screening.js in Jun 2026 session. Pattern: read file → ask Claude about specific concerns → apply fixes.
