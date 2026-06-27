# Rabby Password & Onboarding — State Machine

## Onboarding State Machine

Rabby extension has a strict state machine for first-time setup:

```
State 1: #/welcome ("Access All Dapps")
  → click "Next"
State 2: "Self-custodial"  
  → click "Get Started"
State 3: #/no-address ("Add an Address")
  → this is the MAIN HUB after onboarding
```

## Password Setup

Password page (`#/password`) appears:
- When user navigates directly to `#/password` (can set password before adding address)
- When first wallet import requires password confirmation

**Password page elements:**
- 2 password input fields (type="password")
- Checkbox: "I have read and agree to the Terms of Use and Privacy Policy"
- "Next" button

**Checkbox automation:**
```python
# The checkbox is a custom styled element, not a standard <input type="checkbox">
# Must use JS evaluate to toggle
await page.evaluate("""() => {
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        if (!cb.checked) cb.click();
    });
}""")
# Also click the label text as fallback
await page.click('text=I have read and agree to', timeout=3000)
```

## Import Flow (After Onboarding)

```
#/import → shows 3 options:
  • Import via Private Key
  • Import via Seed Phrase  
  • Import via KeyStore
→ select option → click "Next"
→ shows input form (textarea for PK, textarea for seed, etc.)
→ fill input → click "Confirm"
→ shows "Address Imported" → Rabby closes the page
```

## Key Discovery: #/no-address Import Bug

Clicking "Import Private Key" on `#/no-address` page redirects to `#/welcome` — this is a Rabby routing bug. Always use `#/import` route directly instead of going through `#/no-address`.

## MetaMask Removed (June 2026)

User explicitly requested: "hapus aja yang metamask sisain rabby buat garapan yang butuh"
- Deleted: `~/.hermes/browser-data/extensions/metamask/`
- Deleted: `~/.hermes/browser-data/extensions/metamask.crx`
- Kept: `~/.hermes/browser-data/extensions/rabby/` (v0.93.92)
- Chrome relaunched with ONLY Rabby extension
