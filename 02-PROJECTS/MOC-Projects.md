---
type: moc
updated: 2026-06-27
---

# 🗺️ MOC — Projects

> Map of Content — hub ke semua project aktif

## 🔴 Active

| Project | Priority | Status | Modified |
| :--- | :---: | :---: | :---: |
| [[iclix]] | 🔥 High | 🟢 Active | |
| [[gandalf-operation]] | 🔥 High | 🟡 Pending | |

## 🟡 Standby

| Project | Priority | Status | Modified |
| :--- | :---: | :---: | :---: |
| [[iclix-hosting-upgrade-plan]] | 🟡 Medium | ✅ Done | |
| [[iclix-mega-upgrade-plan]] | 🟡 Medium | ✅ Done | |

## 📦 Archive

| Project | Status | Modified |
| :--- | :---: | :---: |
| [[ctf-commands]] | ✅ Done | |
| [[ctf-quick-paste]] | ✅ Done | |

---

**Dataview query:**
```dataview
TABLE status, priority, deadline
FROM #project
WHERE status != "complete"
SORT priority DESC
```