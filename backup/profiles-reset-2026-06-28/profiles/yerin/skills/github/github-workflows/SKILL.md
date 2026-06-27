---
name: github-workflows
description: >-
  GitHub operations umbrella: authentication setup, pull request lifecycle (branch→commit→open→CI→merge),
  issue triage/labeling/assignment, code review (diffs + inline comments), and repository management
  (clone/fork/create/releases). Each section shows the `gh` CLI way first, with `git` + `curl` fallbacks
  for machines without `gh`. Trigger when user asks about GitHub operations: auth, PRs, issues, code review,
  repo setup, releases, or general "how do I do X on GitHub?"
triggers:
  - github auth
  - github pr
  - github issue
  - github code review
  - github repo
  - gh cli
  - github actions
  - github release
  - git push
  - pr review
---

# GitHub Workflows

This is the umbrella for GitHub operations. The previous 5 sibling skills
(`github-auth`, `github-pr-workflow`, `github-issues`, `github-code-review`,
`github-repo-management`) have been absorbed as references; this SKILL.md
captures the cross-cutting workflow and links to per-operation detail.

## Class-level capabilities

| Operation | Reference | Key tools |
|-----------|-----------|-----------|
| **Authentication** | `references/github-auth-absorbed.md` | `gh auth login`, HTTPS PAT, SSH keys |
| **PR lifecycle** | `references/github-pr-workflow-absorbed.md` | `gh pr create`, `gh pr merge`, branch + commit + push + CI + merge |
| **Issues** | `references/github-issues-absorbed.md` | `gh issue create`, labels, assignees, milestones |
| **Code review** | `references/github-code-review-absorbed.md` | `gh pr review`, inline comments, diff inspection |
| **Repo management** | `references/github-repo-management-absorbed.md` | `gh repo create/clone/fork`, releases, secrets |

## Shared prerequisites

All GitHub operations require authentication. Before any other operation:

1. Check if `gh` is installed: `gh --version`
2. Check auth status: `gh auth status`
3. If not authenticated:
   - **With `gh`**: `gh auth login` (HTTPS recommended for tokens, SSH for key-based)
   - **Without `gh`**: configure git credentials OR set up SSH keys (see `references/github-auth-absorbed.md`)

The `gh` CLI is strongly preferred — it handles auth, pagination, and edge cases.

## Cross-cutting patterns

### The `gh` first, `git`+`curl` fallback pattern

Every operation in this umbrella follows the same pattern:
1. Show the `gh` command (concise, handles auth, rate limits, pagination)
2. Provide `git` + `curl` fallback for headless/VPS environments without `gh`

This pattern is consistent across all 5 absorbed skills — see the relevant reference for the specific commands.

### Common gotchas

- **`gh` not in PATH on VPS**: install with `apt install gh` or use the `git`+`curl` path
- **Rate limits**: `gh` handles pagination; raw `curl` requires manual `Link` header parsing
- **Auth token scopes**: PAT needs `repo`, `workflow`, `write:packages` depending on operation
- **Branch protection**: PRs to protected branches require review approval + CI pass before merge
- **Fork workflows**: PRs from forks run CI in the upstream; secrets aren't available in fork PRs

### CI integration

PR workflow (see `references/github-pr-workflow-absorbed.md`):
1. Branch off main: `git checkout -b fix/<name>`
2. Commit + push: `git push -u origin fix/<name>`
3. Open PR: `gh pr create --base main --title "..." --body "..."`
4. Wait for CI: `gh pr checks --watch`
5. Address review: `gh pr review` / push new commits
6. Merge: `gh pr merge --squash --delete-branch`

## Absorbed skills (June 2026 consolidation)

The following skills were merged into this umbrella. Their full SKILL.md content is preserved as references.

- `github-auth` → `references/github-auth-absorbed.md`
- `github-pr-workflow` → `references/github-pr-workflow-absorbed.md`
- `github-issues` → `references/github-issues-absorbed.md`
- `github-code-review` → `references/github-code-review-absorbed.md`
- `github-repo-management` → `references/github-repo-management-absorbed.md`
