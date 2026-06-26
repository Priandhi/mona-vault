---
type: receipt
date: 2026-06-25
tags:
  - receipt
  - learning
  - skill-development
---

# MONA LEARNING REPORT — 2026-06-25

## Progress: FIX Day 1 (3/9 skills)

### Skill 1: security-recon (~65%)
- **Kuat:** eth_blockNumber probe, impostor detection, high-value findings, brain wallet
- **Mas koreksi:** -32601="Method not found" bukan restricted, -32000=restricted. Fingerprint bisa langsung curl tanpa scan tool
- **Bolong:** Belum praktekin nmap/masscan/trufflehog/gitleaks di target nyata

### Skill 2: linux-privilege-escalation (~75%)
- **Kuat:** SUID, GTFObin, capabilities, LD_PRELOAD, cron wildcard, NFS, systemd, kernel exploits
- **Bolong:** Docker escape DARI DALAM container, snap packages, systemd timers, SSH_AUTH_SOCK, belum praktekin
- **1 akar:** Teori semua, gak pernah execute di sistem nyata

### Skill 3: osint-reconnaissance (~70%)
- **Kuat:** crt.sh, maigret/sherlock/holehe, Wayback, Google dork, Shodan, IP recon, HIBP
- **Bolong:** Metadata extraction, CDN headers selain Cloudflare, 25+ tools cuma tau 12, gak pernah praktekin
- **1 akar:** Bisa jelasin konsep, belum pernah nge-run tool OSINT ke target nyata

### Pattern across all 3 skills:
**Teori solid (~80%), Praktek lemah (~35%), Real = ~70%**
Fix universal: perlu execute di target nyata

### Format laporan disetujui Mas ✅
- % penguasaan (jujur, no manipulasi)
- % belum dikuasai + detail gap
- 1 akar masalah kenapa gak bisa 80%+
- Simpan ke vault tiap selesai skill
