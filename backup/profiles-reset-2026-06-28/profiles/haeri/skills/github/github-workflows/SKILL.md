---
name: github-workflows
description: "GitHub workflow skill umbrella — auth setup, PR lifecycle, code review, issue management, repo management, and codebase inspection. Covers gh CLI + git + curl fallback patterns for working with GitHub without sudo. Trigger on any GitHub-related task: open PR, review PR, create issue, clone repo, fork, create release, configure secrets, check LOC, or set up GitHub auth."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, gh-cli, git, PR, issues, code-review, repo-management, authentication]
    replaces: [github-auth, github-code-review, github-issues, github-pr-workflow, github-repo-management, codebase-inspection]
---

# GitHub Workflows

Class-level skill for working with GitHub. Covers the major workflows an agent needs: authenticating, opening PRs, reviewing code, managing issues, working with repos, and inspecting codebases.

## Loading the right reference

| Task | Open this reference |
|---|---|
| Set up auth (HTTPS token, SSH, `gh` login) | `references/auth.md` |
| PR lifecycle (branch → commit → open → CI → merge) | `references/pr-workflow.md` |
| Review PRs (local diff or remote PR) | `references/code-review.md` |
| Create/triage issues (with bug + feature templates) | `references/issues.md` |
| Repo management (clone, fork, releases, secrets) | `references/repo-management.md` |
| Codebase metrics (LOC, language breakdown) | `references/codebase-inspection.md` |

The SKILL.md below is the workflow index — each numbered section points into the references above.

## 1. Authentication

**Decision tree:**
1. `gh auth status` succeeds → use `gh` for everything
2. `gh` installed but not authenticated → run `gh auth login`
3. No `gh` → use git-only with HTTPS token or SSH key

**Quick check:**

```bash
git --version
gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no credential helper"
```

**HTTPS token path** (portable, no SSH config):
- Create PAT at https://github.com/settings/tokens
- Select scopes: `repo`, `workflow`, `read:org` (for org repos)
- Set as env var `GITHUB_TOKEN` or use credential helper

**SSH path** (for `git@github.com:` remotes):
- `ssh-keygen -t ed25519 -C "agent@host"`
- Add public key to https://github.com/settings/keys
- `git remote set-url origin git@github.com:owner/repo.git`

**`gh` CLI path** (richer API access):
- `gh auth login` (HTTPS recommended)
- Or `GH_TOKEN=*** gh auth login --with-token`

For full detail and the env-loading helper: `references/auth.md`.

## 2. PR Lifecycle (branch → commit → open → CI → merge)

Most-used GitHub task. Read `references/pr-workflow.md` for the full guide. Quick version:

```bash
# Branch
git fetch origin && git checkout main && git pull
git checkout -b feat/add-user-auth

# Commit + push
git add -A
git commit -m "feat(auth): add OAuth2 PKCE flow"
git push -u origin feat/add-user-auth

# Open PR (gh) or curl fallback
gh pr create --title "Add OAuth2 PKCE" --body-file .github/pr-body.md
# curl fallback documented in references/pr-workflow.md

# Watch CI
gh pr checks --watch

# Merge
gh pr merge --squash --delete-branch
```

**Templates** (in `templates/`): `pr-body-feature.md`, `pr-body-bugfix.md`
**CI troubleshooting**: `references/ci-troubleshooting.md`
**Commit message format**: `references/conventional-commits.md`

## 3. Code Review

Read `references/code-review.md`. Two modes:

**Local pre-push review:**
```bash
git diff main...HEAD --stat
git diff main...HEAD  # full diff
git log main..HEAD --oneline
```

**Reviewing open PRs:**
```bash
gh pr diff 42
gh pr view 42 --comments
gh api repos/owner/repo/pulls/42/comments
```

Output template: `references/review-output-template.md`

## 4. Issues

Read `references/issues.md`. Common ops:

```bash
gh issue list --label bug --assignee @me
gh issue create --title "..." --body-file templates/bug-report.md
gh issue close 42 --comment "Fixed in #99"
```

Templates (in `templates/`): `bug-report.md`, `feature-request.md`

## 5. Repository Management

Read `references/repo-management.md`. Covers cloning, forking, releases, secrets, webhooks.

```bash
gh repo clone owner/repo
gh repo create my-repo --public --source=. --remote=upstream
gh release create v1.0.0 --generate-notes
```

API cheatsheet: `references/github-api-cheatsheet.md`

## 6. Codebase Inspection (pygount)

Read `references/codebase-inspection.md`. LOC analysis:

```bash
pip install pygount
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,dist,build" \
  .
```

**IMPORTANT**: Always use `--folders-to-skip` to exclude dependency/build dirs — otherwise pygount crawls them and hangs.

## Cross-cutting helper

`scripts/gh-env.sh` — Loads `GITHUB_TOKEN` from `~/.hermes/.env` or `~/.git-credentials`. Returns `gh` (using gh CLI) or `curl` (with bearer token) for use in subsequent commands.

```bash
source scripts/gh-env.sh
echo "Using: $AUTH"  # "gh" or "curl"
```

## Safety rules

- Never log or print raw `GITHUB_TOKEN` values
- Use `--body-file` for PR/issue bodies with secrets, never `--body "secret=$X"`
- Don't `gh repo delete` without explicit user confirmation
- For org repos, confirm user has admin rights before destructive ops
- When opening PRs on behalf of users, show the title + body first and wait for approval

## Absorbed Skills (consolidated June 2026)

- `github-auth` → merged into §1 + `references/auth.md` + `scripts/gh-env.sh`
- `github-pr-workflow` → merged into §2 + `references/pr-workflow.md` + `references/ci-troubleshooting.md` + `references/conventional-commits.md` + `templates/pr-body-feature.md` + `templates/pr-body-bugfix.md`
- `github-code-review` → merged into §3 + `references/code-review.md` + `references/review-output-template.md`
- `github-issues` → merged into §4 + `references/issues.md` + `templates/bug-report.md` + `templates/feature-request.md`
- `github-repo-management` → merged into §5 + `references/repo-management.md` + `references/github-api-cheatsheet.md`
- `codebase-inspection` → merged into §6 + `references/codebase-inspection.md`
