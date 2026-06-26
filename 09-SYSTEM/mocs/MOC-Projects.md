---
type: moc
updated: 2026-06-27
---

# 🗺️ MOC — Projects

> Map of Content — hub ke semua project aktif

## 🔴 Active

| Project | Priority | Status | Modified |
| :--- | :---: | :---: | :---: |
| [[02-PROJECTS/iclix]] | 🔥 High | 🟢 Active | |
| [[02-PROJECTS/gandalf-operation]] | 🔥 High | 🟡 Pending | |

## 🟡 Standby

| Project | Priority | Status | Modified |
| :--- | :---: | :---: | :---: |
| [[02-PROJECTS/iclix-hosting-upgrade-plan]] | 🟡 Medium | ✅ Done | |
| [[02-PROJECTS/iclix-mega-upgrade-plan]] | 🟡 Medium | ✅ Done | |

## 📦 Archive

| Project | Status | Modified |
| :--- | :---: | :---: |
| [[02-PROJECTS/ctf-commands]] | ✅ Done | |
| [[02-PROJECTS/ctf-quick-paste]] | ✅ Done | |

## 🔗 Ongoing Responsibilities (AREAS)

| Area | Description |
| :--- | :--- |
| [[03-AREAS/learning-skills]] | Learning & skill development (PWN, RE, CTF, Web) |
| [[03-AREAS/vps-infrastructure]] | VPS health, security, services |
| [[03-AREAS/iclix-platform]] | ICLIX platform dev & ops |

## 🔗 Related Resources

| Resource | Links To |
| :--- | :--- |
| [[09-SYSTEM/mocs/MOC-Research]] | All research & reference materials |

---

**Dataview query:**
```dataview
TABLE status, priority, deadline
FROM #project
WHERE status != "complete"
SORT priority DESC
```