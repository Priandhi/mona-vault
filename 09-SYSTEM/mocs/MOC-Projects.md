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

---

**Dataview query:**
```dataview
TABLE status, priority, deadline
FROM #project
WHERE status != "complete"
SORT priority DESC
```