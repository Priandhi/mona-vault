---
type: area
status: active
updated: 2026-06-27
tags:
  - area
  - vps
  - infrastructure
---

# 🖥️ AREA — VPS & Infrastructure

> Ongoing responsibility — server health, security, uptime

## Services

| Service | Status | Port |
| :--- | :---: | :---: |
| Hermes Gateway | 🟢 | - |
| 9Router | 🟢 | 20128 |
| ICLIX API | 🟢 | 3000 |
| WARP | 🟢 | 1080 |
| CrowdSec | 🟢 | - |
| fail2ban | 🟢 | - |
| Meridian Bot | 🟢 | - |
| Charon Sniper | 🟢 | - |
| Cloudflared (named) | 🟢 | - |
| Cloudflared (quick) | 🟢 | - |

## Security Checklist

- [x] fail2ban — 353 IPs banned
- [x] CrowdSec — firewall bouncer active
- [ ] 🔴 PermitRootLogin → prohibit-password
- [ ] 🔴 PasswordAuthentication → off
- [ ] 🟡 UFW — activate?
- [ ] 🟡 Disk cleanup (82%)

## 🔗 Related
- [[09-SYSTEM/mocs/MOC-Projects]] — master project dashboard

---