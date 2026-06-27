"""
Clean Alpha Alert Formatter - Reference implementation.
See crypto-alert-bot SKILL.md section 0 for format spec.
See references/alpha-alert-template-design.md for design decisions.

Usage:
    from mona_alpha_alert_clean import format_clean_alert, format_multi_whale_clean, format_sell_alert_clean
"""

def fmt_mc(val):
    if not val: return "-"
    if val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if val >= 1_000: return f"${val/1_000:.0f}K"
    return f"${val:.0f}"

def fmt_vol(val):
    if not val: return "-"
    if val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if val >= 1_000: return f"${val/1_000:.0f}K"
    return f"${val:.0f}"

def fmt_pct(val):
    if val is None: return "-"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"

def fmt_age(hours):
    if not hours: return "-"
    if hours < 1: return f"{int(hours*60)}m"
    if hours < 24: return f"{int(hours)}h"
    return f"{int(hours/24)}d"

def shorten_addr(addr, chars=4):
    if not addr: return ""
    return f"{addr[:6]}...{addr[-chars:]}"

def format_clean_alert(token_data, whale_info=None, security=None, social=None):
    t = token_data
    symbol = t.get("symbol", "???")
    chain = t.get("chain", "BASE").upper()
    mc = fmt_mc(t.get("market_cap", 0))
    vol = fmt_vol(t.get("volume_24h", 0))
    txns = t.get("txns_1h", 0) or t.get("txns_buys_1h", 0) + t.get("txns_sells_1h", 0)
    pct_24h = fmt_pct(t.get("price_change_24h", 0))
    age = fmt_age(t.get("age_hours", 0) or t.get("pair_created_hours", 0))
    safe = "Safe" if security and not security.get("is_honeypot") else "Check"
    verified = "Verified" if security and security.get("is_open_source") else "Unverified"
    tax = security.get("sell_tax", 0) if security else 0
    ca = t.get("contract", "")
    lines = [f"diamond ${symbol} - {chain}", ""]
    lines.append(f"rocket {t.get('launchpad', 'Unknown')}")
    lines.append(f"chart MC {mc} - VOL {vol} - {txns}tx/1h")
    lines.append(f"up 24h {pct_24h} - hourglass {age}")
    lines.append(f"shield OK {safe} - OK {verified} - {tax}% Tax")
    lines.append("")
    if ca: lines.append(f"CA: {shorten_addr(ca)}")
    if whale_info:
        addr = whale_info.get("address", "")
        lines.append(f"Dev: {shorten_addr(addr)}")
        social = social or {}
        if social.get("twitter"): lines.append(f"   bird {social['twitter']}")
        if social.get("debank"): lines.append(f"   globe {social['debank']}")
        elif addr: lines.append(f"   globe https://debank.com/profile/{addr}")
    links = []
    if t.get("dex_url"): links.append("link Chart")
    if t.get("twitter"): links.append("bird X")
    if links: lines.append(" - ".join(links))
    return "\n".join(lines)
