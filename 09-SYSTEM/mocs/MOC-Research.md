---
type: moc
updated: 2026-06-27
---

# 🗺️ MOC — Research

> Map of Content — semua riset & findings

## 🔥 CTF & Security

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[04-RESOURCES/ctf-master-cheatsheet]] | CTF command reference | |
| [[04-RESOURCES/ctf-decision-tree]] | When to pivot | |
| [[04-RESOURCES/ctf-battle-plan]] | CTF strategy | |
| [[04-RESOURCES/guard-bypass-strategy]] | Prompt injection | |
| [[04-RESOURCES/prompt-injection-research-2026-06-25]] | Opus guard bypass | |
| [[04-RESOURCES/opus-4.8-counter-strategy]] | Counter strategy | |
| [[04-RESOURCES/opus-ctf-playbook]] | CTF playbook | |
| [[04-RESOURCES/hackagent-gap-correction]] | HackAgent gaps | |

## 🎯 Crypto & Trading

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[04-RESOURCES/crypto-advanced-2026-06-25]] | Crypto techniques | |

## 🎨 ICLIX

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[04-RESOURCES/iclix-anime-research]] | Anime scraper | |

## 💡 Ideas

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[04-RESOURCES/hitam-area-money-ideas]] | Business ideas | |

---

**Dataview: orphan finder**
```dataview
TABLE length(file.inlinks) AS Incoming
FROM "04-RESOURCES"
WHERE length(file.inlinks) = 0
SORT file.name ASC
```