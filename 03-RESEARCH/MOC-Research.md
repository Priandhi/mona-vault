---
type: moc
updated: 2026-06-27
---

# 🗺️ MOC — Research

> Map of Content — semua riset & findings

## 🔥 CTF & Security

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[ctf-master-cheatsheet]] | CTF command reference | |
| [[ctf-decision-tree]] | When to pivot | |
| [[ctf-battle-plan]] | CTF strategy | |
| [[guard-bypass-strategy]] | Prompt injection | |
| [[prompt-injection-research-2026-06-25]] | Opus guard bypass | |
| [[opus-4.8-counter-strategy]] | Counter strategy | |
| [[opus-ctf-playbook]] | CTF playbook | |
| [[hackagent-gap-correction]] | HackAgent gaps | |

## 🎯 Crypto & Trading

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[crypto-advanced-2026-06-25]] | Crypto techniques | |

## 🎨 ICLIX

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[iclix-anime-research]] | Anime scraper | |

## 💡 Ideas

| Note | Topic | Date |
| :--- | :--- | :---: |
| [[hitam-area-money-ideas]] | Business ideas | |

---

**Dataview: orphan finder**
```dataview
TABLE length(file.inlinks) AS Incoming
FROM "03-RESEARCH"
WHERE length(file.inlinks) = 0
SORT file.name ASC
```