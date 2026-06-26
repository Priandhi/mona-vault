---
updated: 2026-06-27
---

# 📊 Dataview Dashboard

> Query-query berguna buat monitor vault

## 🔥 Active Projects

```dataview
TABLE priority, status, deadline
FROM #project
WHERE status != "complete"
SORT priority DESC
```

---

## 🗑️ Orphan Notes (0 incoming links)

```dataview
TABLE length(file.inlinks) AS Incoming
WHERE length(file.inlinks) = 0
  AND file.folder != "Templates"
  AND file.name != "README"
  AND file.name != "AGENTS"
  AND file.name != "MOC-Projects"
  AND file.name != "MOC-Research"
  AND file.name != "Dataview-Dashboard"
SORT file.name ASC
```

---

## ⏳ Stale Projects (>14d no update)

```dataview
TABLE file.mtime AS LastModified
FROM #project
WHERE date(today) - file.mtime > dur(14 days)
  AND status != "complete"
SORT file.mtime ASC
```

---

## 📁 By Folder

```dataview
TABLE length(rows) AS Count
FROM ""
WHERE file.name != "README" AND file.name != "AGENTS"
GROUP BY file.folder
SORT Count DESC
```

---

## 📝 Recent 10 Notes

```dataview
TABLE file.mtime AS Modified
FROM ""
SORT file.mtime DESC
LIMIT 10
```