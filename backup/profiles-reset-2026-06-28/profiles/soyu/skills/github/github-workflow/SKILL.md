---
name: github-workflow
description: "Complete GitHub workflow from auth setup through PR lifecycle. Covers authentication, repository management, issues, pull requests, code review, and codebase inspection via gh CLI and git+curl fallbacks. Use when asked to do anything with GitHub: clone/create repos, manage issues, open/merge PRs, review code, or check repo stats."
tags: [GitHub, Git, gh-cli, Pull-Requests, Issues, Code-Review, Repositories, SSH, Authentication]
---

# GitHub Workflow — Class-Level Umbrella

> One entry point for **every** GitHub operation Hermes agents do. The six topic pages below carry the full detail; this index orients you to which one to load.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "set up GitHub", "auth", "gh auth", "ssh key" | `references/auth/` |
| "clone repo", "create repo", "fork", "releases", "secrets" | `references/repository-management/` |
| "create issue", "triage issues", "label issues" | `references/issues/` |
| "open PR", "merge PR", "CI", "fix CI", "conventional commit" | `references/pull-requests/` |
| "review PR", "review code", "leave comments", "approve" | `references/code-review/` |
| "how big is this repo", "LOC", "language breakdown" | `references/codebase-inspection/` |

## Universal Auth Detection (run first)

Every GitHub workflow needs to know which auth method is available. Run this once and reuse AUTH, GITHUB_TOKEN, OWNER, REPO for the rest of the session:

```bash
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"

REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -n "$REMOTE_URL" ]; then
  OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
  OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
  REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
fi
```

`scripts/gh-env.sh` (under `references/auth/`) exports the same variables. Source it at the top of any long workflow.

## Topic Pages

### `auth/` — Authentication
HTTPS tokens, SSH keys, gh CLI login. Auth detection for everything else.
Full content at `references/auth/SKILL.md`.

### `repository-management/` — Repository Management
Clone, create, fork repos; manage remotes, branches, releases, secrets, Actions.
Full content at `references/repository-management/SKILL.md`.

### `issues/` — Issues
Create, triage, label, assign, comment on issues; bulk operations and issue-PR linking.
Full content at `references/issues/SKILL.md`.

### `pull-requests/` — Pull Requests
Branch - commit - push - open PR - CI - merge, plus auto-fix loop for failed CI.
Full content at `references/pull-requests/SKILL.md`.

### `code-review/` — Code Review
Pre-push local review and post-PR review (diff inspection, inline comments, formal approval).
Full content at `references/code-review/SKILL.md`.

### `codebase-inspection/` — Codebase Inspection
Pygount-based LOC, language breakdown, and code-vs-comment ratios.
Full content at `references/codebase-inspection/SKILL.md`.

## Cross-Cutting Patterns

**`gh` first, `git` + `curl` fallback.** Every topic page shows both paths because not every machine has `gh` installed (CI containers, headless VPS, fresh user setups). The fallback for API calls is always `curl -H "Authorization: token $GITHUB_TOKEN"`.

**Owner/repo from git remote.** Every API call needs `owner/repo`. Extract once via `git remote get-url origin` and the sed pipeline above; reuse throughout the session.

**PR and issue share the same `issues` endpoint.** GitHub's API returns PRs in `GET /repos/{o}/{r}/issues` — always filter with `if 'pull_request' not in i:` to get just issues.

**PITFALL: HTTP 401 / "Bad credentials".** Token expired or missing scope. Re-check `gh auth status` and the `GITHUB_TOKEN` env var before retrying.

**PITFALL: HTTP 403 / rate limit.** Authenticated requests get 5000/hr; unauthenticated get 60/hr. Add `sleep` between bulk calls.

## Verification

After loading any topic page, smoke-test the auth detection block above. If AUTH=gh and GITHUB_TOKEN is unset, fix that first — every subsequent API call will fail.

## Related Skills

- `autonomous-ai-agents/claude-code`, `codex`, `opencode` — for delegating complex PR work to external coding agents
- `hermes/mona-command-center` — for cron-driven GitHub monitoring patterns
