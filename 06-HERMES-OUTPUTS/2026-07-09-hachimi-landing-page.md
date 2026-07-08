---
date: 2026-07-09
task: Hachimi landing page
---

# Hachimi Landing Page

**Task:** Build professional premium meme coin landing page for Hachimi (哈基米) launching on Robinhood Chain via NOXA Launchpad.

**Result:**
- Project created at `/home/ubuntu/hachimi-landing`
- Delivery archive created at `/home/ubuntu/hachimi-landing.zip`
- Next.js 15.5.20 + React 19.2.7 + TypeScript strict + Tailwind CSS v4 + Framer Motion + Lucide React
- Mobile-first Web3 design with dark background, Robinhood green glow, particles, glassmorphism, hero mascot, gallery assets, SEO metadata, README, deploy guide, env example

**Verification:**
- `npm install` completed
- `npm run lint` PASS
- `npm run typecheck` PASS
- `npm run format:check` PASS
- `npm audit --audit-level=moderate` PASS — 0 vulnerabilities after PostCSS override
- `npm run build` PASS — static route `/`, first load JS 158 kB
- Browser smoke test PASS — title/meta/sections/footer/images render, no horizontal scroll detected
- HTTP smoke test PASS — HTML contains title, description, hero, stats, OG/Twitter metadata, footer

**Decisions:**
- Generated placeholder mascot/gallery locally because no previous Hachimi asset was found on VPS; file names match requested structure so Mas can replace `public/images/hero.png` later without code change.
- Live Stats implemented as future-ready hook (`use-token-stats.ts`) supporting custom API or DexScreener pair URL.
- `postcss` override added to remove moderate npm audit advisory while keeping Next.js 15.
- Used dynamic import for Gallery/FAQ to keep initial rendering lighter.

**Issues:**
- Image generation backend unavailable (`FAL_KEY` missing), so mascot was generated locally with PIL, not AI image backend.
- `npm view` had registry/log noise, but package install succeeded with current latest matching requested major versions.

**Next Steps:**
- Replace social links, contract address, DexScreener link in `.env.local`.
- Replace hero/gallery assets with final brand assets if Mas has final mascot image.
- Deploy to Vercel/Netlify using `DEPLOY.md`.
