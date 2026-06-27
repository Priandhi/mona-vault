# External Portfolio Tracker Integration Pattern

## The Problem

User wants PnL analytics from external trackers (fabriq.trade, Birdeye, Step Finance, etc.) integrated into bot dashboards. Ideally via deep links that open directly to the wallet's portfolio page.

## Reality (Jun8 discovery)

ALL major Solana portfolio trackers are behind Cloudflare and are SPAs (Single Page Applications). They do NOT support URL-based wallet deep linking from server-side:

| Tracker | Deep Link | Status |
|---------|-----------|--------|
| fabriq.trade | `/portfolio/WALLET` | ❌ Returns 404 (SPA) |
| Birdeye | `/address/WALLET` | ❌ Cloudflare challenge |
| Step Finance | `/portfolio?wallet=WALLET` | ❌ Cloudflare challenge |
| Solana FM | `/address/WALLET` | ❌ Empty page (SPA) |
| Sonar Watch | Unknown | ❌ Not tested |

**Root cause:** These are SPAs where wallet search happens client-side via JavaScript. The server only serves the app shell — any URL path that isn't a known route returns 404 or the shell.

## Practical Solution

1. Link to the **base portfolio page** (e.g., `https://fabriq.trade/portfolio`)
2. Embed wallet address in `title` attribute for easy copy-paste
3. User searches manually in-app

```html
<a href="https://fabriq.trade/portfolio" target="_blank"
   title="Search wallet: 9XJUJJ9YTq6Vrj7ZRRWAariysQrgkB8hm7QMPzMxLZ3X"
   style="background:#FF4500;color:#fff;padding:4px 12px;border-radius:6px;font-size:12px;text-decoration:none;font-weight:600;">
  📊 Fabriq PnL
</a>
```

## User Reaction

User was disappointed: "yahh manual gak profesional". This is a real limitation — there's no way around it without:
1. Browser extension that auto-fills wallet on page load
2. Running a proxy that intercepts and redirects
3. Waiting for these apps to add URL-based deep linking

## fabriq.trade Specific Notes

- **Docs:** https://docs.fabriq.trade (Mintlify, accessible without Cloudflare)
- **App:** https://fabriq.trade/portfolio (Cloudflare-protected)
- **API:** None (OpenAPI spec is placeholder "Plant Store")
- **Indexer:** In-house Meteora DLMM indexer (their competitive advantage)
- **PnL features:** Net PnL, Position Win %, Profit Factor, Day Win %, realized PnL calendar, cumulative/daily charts, HawkFi integration
- **Wallet search:** Client-side — "search a wallet" in the UI
