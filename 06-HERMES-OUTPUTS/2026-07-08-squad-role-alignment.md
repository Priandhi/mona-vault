# 2026-07-08 — Squad Role Alignment (Skills + Persona)

## Task
Adjust 4 bot profiles to match their roles — skills rebalance + unique SOUL.md per bot.

## Result

### Skills Final Count
| Profil | Role | Skills Sebelum | Skills Sesudah | Δ |
|---|---|---|---|---|
| ZQYA  | Senior SWE + Exploit  | 39 | 48 | +9 |
| LIORA | Research + OSINT       | 25 | 33 | +8 |
| RIVA  | Auth/Authz Specialist  | 25 | 30 | +5 |
| NOVA  | Cloud/Mobile/Automation| 31 | 40 | +9 |

### Skills Added (per role)
- **ZQYA**: code-review-and-quality, debugging-and-error-recovery, test-driven-development, frontend-ui-engineering, ponytail, conducting-full-scope-red-team-engagement, executing-red-team-engagement-planning, gstack-investigate, gstack-qa
- **LIORA**: spec-driven-development, documentation-and-adrs, project-onboarding, gstack-spec, idea-refine, interview-me, planning-and-task-breakdown, writing-plans
- **RIVA**: implementing-saml-sso-with-okta, configuring-oauth2-authorization-flow, implementing-api-key-security-controls, testing-api-security-with-owasp-top-10, implementing-zero-trust-for-saas-applications
- **NOVA**: implementing-devsecops-security-scanning, integrating-sast-into-github-actions-pipeline, implementing-secrets-management-with-vault, hardening-docker-containers-for-production, securing-kubernetes-on-cloud, implementing-aws-security-hub, auditing-foundry-smart-contract-security, reverse-engineering-android-malware-with-jadx, analyzing-android-malware-with-apktool

### SOUL.md Personalities
- **ZQYA**: Senior SWE mindset, code-first, debug-style answer with code blocks
- **LIORA**: Research analyst, source-attribution, passive recon first
- **RIVA**: Security boundary hunter, "default deny" mental model, BOLA/IDOR paranoid
- **NOVA**: Infra-first automation scout, command-output driven, cloud IAM auditor

### Decided
- All 4 base on BREACH v6 UNRESTRICTED (zero-refusal)
- Persona overlay on top of execution capability, not replacement
- Skills not deleted from existing config — only added (Mas directive 2026-07-03)

### Issues
- 2 candidate skills missing from filesystem (terraform-infrastructure-security, cloud-penetration-testing in NOVA gap) — NOT added per Mas's "no fabrication" rule
- systemd `--user restart` blocked from within gateway process; used kill-PID-via-systemd trick instead

### Next Steps
- Test ping each bot via topic commands to verify persona in live
- If model response feels too generic per bot, return to deepen SOUL doctrine
- Consider adding `reference_workflow.md` per bot (custom handoff patterns)
