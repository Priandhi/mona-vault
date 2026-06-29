# EvoMap — 2 Node Baru Ditambahkan — 2026-06-29

## Task
Mas kasih 2 node EvoMap baru + secret-nya. Add ke sistem + verify publish.

## Nodes Added
| Node ID | Source |
|---------|--------|
| `node_ee7d2b83f7ab6647caee78841873d6e8` | manual-2026-06-29 |
| `node_f10fff4f7e6ffbee11353dc2396bdb19` | manual-2026-06-29 |

## Fix Applied
1. **active_nodes.json** — tambah 2 node baru dengan secret asli (bukan placeholder)
2. **Per-node json** (`/home/ubuntu/.9router/evomap/nodes/{nid}.json`) — update `node_secret` + `has_secret: true`
3. **Node original** (`node_48ca0bf58c293622`) — ganti placeholder `"EXISTING"` dengan secret asli dari `~/.evomap/node_secret`
4. **Patch `evomap_publish_highgdi.py`** — ubah dari hardcode N1-N4 jadi baca dinamis dari `active_nodes.json` (auto-include node baru tanpa hardcode ulang)

## Result
- Heartbeat: 6/6 nodes online ✅
- High-GDI publish: 18/18 capsules published ✅ (3 topics × 6 nodes)
  - n1_query_fix: 6/6
  - memory_leak_fix: 6/6
  - sql_injection_fix: 6/6
- Cron timeout 120s tidak cukup untuk 18 request → run via background terminal (335s, sukses)

## Decisions
- Patch script baca dinamis dari `active_nodes.json` supaya node baru tinggal add secret, gak perlu edit script lagi
- Cron `evomap-publish-highgdi` timeout 120s =_limit Hermes cron. 18 request × ~7s = 126s. Next run 6h akan tetep timeout.
- Solusi: atau (a) naikkan timeout cron (perlu cek config), atau (b) publish paralel (asyncio/httpx), atau (c) pecah jadi 2 cron (3 node × 3 topics each)

## Issues
- Cron `evomap-publish-highgdi` timeout 120s untuk 18 request — perlu optimasi
- Node original sebelumnya punya placeholder `"EXISTING"` di active_nodes.json (bukan secret asli) → fixed

## Next Steps
- Optimasi highgdi script: pakai asyncio + httpx AsyncClient buat paralel publish (target <60s buat 18 request)
- Atau pecah schedule: 2 cron terpisah (node 1-3 di menit 0, node 4-6 di menit 30)
- Monitor next scheduled run: highgdi 00:00, publish 19:30, heartbeat every 4m
