---
type: moc
updated: 2026-06-27
---

# 🗺️ MOC — Research

> Map of Content — semua riset & findings

## 🔥 CTF & Security

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[04-RESOURCES/ctf-master-cheatsheet]] | CTF command reference | 2026-06-25 |
| [[04-RESOURCES/ctf-decision-tree]] | When to pivot in CTF | 2026-06-25 |
| [[04-RESOURCES/ctf-battle-plan]] | CTF strategy — bersaing 300 agent | 2026-06-25 |
| [[04-RESOURCES/guard-bypass-strategy]] | Prompt injection — Opus guard bypass | 2026-06-25 |
| [[04-RESOURCES/prompt-injection-research-2026-06-25]] | 100+ Opus bypass attempts | 2026-06-25 |
| [[04-RESOURCES/opus-4.8-counter-strategy]] | Counter-strategy for stronger guard | 2026-06-25 |
| [[04-RESOURCES/opus-ctf-playbook]] | CTF playbook — Opus specific | 2026-06-25 |
| [[04-RESOURCES/opus-prompt-injection-strategy]] | Additional prompt injection research | 2026-06-25 |
| [[04-RESOURCES/hackagent-gap-correction]] | HackAgent techniques | 2026-06-25 |
| [[04-RESOURCES/pwn-deep-dive-2026-06-25]] | ret2libc + heap exploitation | 2026-06-25 |
| [[04-RESOURCES/crypto-advanced-2026-06-25]] | Lattice, ZK, padding oracle | 2026-06-25 |
| [[04-RESOURCES/kernel-exploit-mindset]] | Bug Class → Primitive → Technique | 2026-06-18 |

## 📚 Learning & Development

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[04-RESOURCES/learning-session-2026-06-22]] | Day 1 — security skills | 2026-06-22 |
| [[04-RESOURCES/learning-session-2026-06-23]] | Day 2 — hands-on challenges | 2026-06-23 |
| [[04-RESOURCES/learning-reevaluation-2026-06-25]] | Re-evaluation after testing | 2026-06-25 |
| [[04-RESOURCES/mona-skill-audit-2026-06-25]] | Skill audit & gap analysis | 2026-06-25 |
| [[04-RESOURCES/opus-deep-learning-2026-06-20]] | Opus reasoning methodology deep-dive | 2026-06-20 |

## 🎨 ICLIX

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[04-RESOURCES/iclix-anime-research]] | Anime TMDB + multi-season mapping | 2026-06-19 |
| [[04-RESOURCES/iclix-idlix-design-reference]] | IDLIX premium design specs | 2026-06-18 |
| [[04-RESOURCES/iclix-ui-ux-audit-2026-06-18]] | UI audit — 13 issues found | 2026-06-18 |
| [[04-RESOURCES/iclix-video-resolver-research]] | m3u8 chain — VidSrc → m3u8 | 2026-06-18 |

## 💡 Ideas & Reference

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[04-RESOURCES/2026-06-19-blackhat-business-ideas]] | Business ideas | 2026-06-19 |
| [[04-RESOURCES/hitam-area-money-ideas]] | Income ideas — dark side | 2026-06-25 |
| [[04-RESOURCES/webtoapp-analysis]] | WebToApp Android build research | 2026-06-22 |

---

## 🔗 Quick Links

| From | To |
| :--- | :--- |
| [[02-PROJECTS/iclix]] | [[04-RESOURCES/iclix-idlix-design-reference]], [[04-RESOURCES/iclix-ui-ux-audit-2026-06-18]], [[04-RESOURCES/iclix-video-resolver-research]] |
| [[03-AREAS/learning-skills]] | [[04-RESOURCES/learning-session-2026-06-22]], [[04-RESOURCES/learning-reevaluation-2026-06-25]] |

**Dataview: orphan finder**
```dataview
TABLE length(file.inlinks) AS Incoming
FROM "04-RESOURCES"
WHERE length(file.inlinks) = 0
SORT file.name ASC
```