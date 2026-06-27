---
name: coding-agent-delegation
description: "Delegate coding tasks to autonomous CLI agents — Claude Code (Anthropic), Codex (OpenAI), OpenCode (provider-agnostic), or Hermes Agent itself. Covers install, auth, one-shot tasks, print mode, interactive PTY mode, PR workflows, parallel worktree execution. Trigger on user request to use Claude Code, run Codex, delegate to OpenCode, spawn subagents, run coding agents in worktrees, or use Hermes Agent for implementation tasks."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Claude-Code, Codex, OpenCode, Hermes-Agent, coding-agent, CLI, delegation, subagent, worktree, PTY]
    replaces: [claude-code, codex, opencode, hermes-agent]
---

# Coding Agent Delegation

Class-level skill for delegating coding tasks to autonomous CLI agents. Each tool has its own install flow, auth model, command shape, and orchestration mode. This umbrella loads the right reference based on which agent the user names.

## Loading the right reference

| Tool | Section | Reference file |
|---|---|---|
| Claude Code (Anthropic) | §1 | `references/claude-code.md` |
| Codex (OpenAI) | §2 | `references/codex.md` |
| OpenCode (provider-agnostic) | §3 | `references/opencode.md` |
| Hermes Agent (self) | §4 | `references/hermes-agent.md` |

If the user didn't name a tool, default to **Claude Code** (most feature-rich, best Hermes integration).

## §1. Claude Code (Anthropic)

**Install:** `npm install -g @anthropic-ai/claude-code`
**Auth:** `claude` once for browser OAuth, or `ANTHROPIC_API_KEY=*** claude`. Console: `claude auth login --console`. SSO: `claude auth login --sso`.
**Status:** `claude auth status --text` (human-readable) or JSON with `--text` flag omitted.
**Health:** `claude doctor`. Version: `claude --version` (requires v2.x+).

**Two orchestration modes:**

**Mode A — Print mode (`-p`)** — non-interactive, preferred for one-shot tasks:
```
terminal(command="claude -p 'Add user authentication to the API'", pty=true)
```
Returns final result, no back-and-forth. Best for batch work.

**Mode B — Interactive PTY mode** — needed for long-running sessions, debugging, or when you need to see intermediate output. Use `pty=true` in `terminal()` calls.

**PR workflow:**
1. Branch + commit: standard git
2. Open PR: `claude` can auto-generate PR bodies
3. CI: `claude` can watch GitHub Actions and fix failures

**Common flags:** `--model`, `--dangerously-skip-permissions` (sandboxed env only), `--verbose`.

For full detail: `references/claude-code.md`

## §2. Codex (OpenAI)

**Install:** `npm install -g @openai/codex`
**Auth:** `OPENAI_API_KEY` env var OR `codex` interactive login. For Hermes itself, `model.provider: openai-codex` uses Hermes-managed OAuth from `~/.hermes/auth.json` after `hermes auth add openai-codex`. The standalone CLI may store OAuth at `~/.codex/auth.json`.

**Constraint:** Codex REFUSES to run outside a git repo. For scratch work, create a temp repo first:
```
cd $(mktemp -d) && git init && codex exec 'Build a snake game'
```

**PTY required:** Codex is an interactive terminal app. Always use `pty=true` in `terminal()` calls.

**One-shot:**
```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For full detail: `references/codex.md`

## §3. OpenCode (provider-agnostic)

**Install:** `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
**Auth:** `opencode auth login` or set provider env vars (`OPENROUTER_API_KEY`, etc.). Verify: `opencode auth list`.

**When to use:** User explicitly asks for OpenCode, or you want a provider-agnostic agent that runs against OpenRouter/local models.

**Binary resolution gotcha:** Different shells may resolve different `opencode` binaries. Check with `which -a opencode` and `opencode --version`. Pin with `$HOME/.opencode/bin/opencode run '...'` if needed.

**PTY required:** Use `pty=true` for interactive TUI.

For full detail: `references/opencode.md`

## §4. Hermes Agent (self-config)

When the user asks to **configure, extend, or contribute to Hermes Agent itself** — not delegate to it as a worker. This is the meta-skill: it's the same skill that built the umbrella you're reading now.

**Hermes' distinguishing features:**
- Self-improving through skills (each successful task can save as a reusable skill)
- Persistent memory across sessions (Honcho, Mem0 backends)
- Multi-agent orchestration (Kanban, subagent delegation)
- 15+ LLM provider support out of the box

For config, setup, contribution: `references/hermes-agent.md`

## Cross-cutting patterns

### PTY mode for interactive tools
Claude Code, Codex, OpenCode are interactive TUIs. Use `pty=true` in `terminal()` calls or Hermes can't drive them. Without PTY, the CLI may hang waiting for input.

### One-shot vs interactive
- **One-shot** (preferred for batch): `-p` flag (Claude) or `exec` subcommand (Codex, OpenCode). Returns final result.
- **Interactive PTY**: needed for debugging sessions, multi-step agentic loops, or when the agent asks clarifying questions.

### Parallel worktree execution
For multi-PR work, run multiple Claude/Codex instances in separate git worktrees. Pattern:
```bash
git worktree add ../repo-feat-a feat/branch-a
cd ../repo-feat-a
claude -p "implement feature A" > /tmp/a.log 2>&1 &
```

### Subagent delegation from Hermes
Use `delegate_task(goal="...", toolsets=["terminal", "file"])` to spawn a Hermes subagent for parallel work. The subagent gets its own context.

## Absorbed Skills (consolidated June 2026)

- `claude-code` → §1 + `references/claude-code.md` + `references/kiro-api-investigation.md`
- `codex` → §2 + `references/codex.md`
- `opencode` → §3 + `references/opencode.md`
- `hermes-agent` → §4 + `references/hermes-agent.md` + 3 reference files (`gemini-vision-setup.md`, `provider-diagnostics.md`, `provider-cleanup.md`)
