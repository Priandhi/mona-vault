---
name: Card Auto-Fill & Generator
description: Generates a valid card from a BIN using Luhn algorithm, fetches realistic user details from randomuser.me, generates bulk Ethereum wallets, and handles Web3 platform authentication flows.
---

# Card Auto-Fill & Generator (H-Skill)

This skill generates valid credit/debit card numbers from a BIN using the Luhn algorithm, fetches random identity data from `randomuser.me`, generates bulk Ethereum wallets, and documents Web3 platform auth patterns.

## 0. Pitfalls

- **Luhn algorithm gotcha**: The `alt = True/False` alternating approach from right-to-left produces WRONG check digits for generation. Correct approach: double digits at indices `len-1, len-3, len-5...` of the 15-digit prefix, sum all, `check_digit = (10 - (total % 10)) % 10`. For *verification*, start doubling from `len-2`. Mixing these two offsets produces invalid cards.
- **`random.datetime` typo**: `random` module has no `datetime` submodule. Always `import datetime` separately.
- **`enable_unaudited_hd_wallet_features()`**: Correct spelling is `enable_unaudited_hdwallet_features` (no underscore). Only needed for mnemonic HD wallets, not simple key generation.
- **Next.js SPA + Auth.js wallet auth**: Cannot be automated with pure requests. The signing nonce is server-generated and CSRF-tied. Mock `window.ethereum` injection into headless browsers fails because React event handlers bind before injection. See `references/web3-platform-auth.md`.
- **Headless browser + Next.js**: Without residential proxies, Next.js SPAs often render blank. `browser_snapshot` returns empty, `browser_vision` shows white screen. Use `browser_console` JS injection for limited interaction, but don't rely on it for complex flows.

## 1. Card Generation Algorithm (Luhn)

1. Take the BIN prefix (e.g., `6233586370`, `425881`, `515462`)
2. Append random digits until length reaches 15
3. Calculate check digit: double digits at odd positions from right (indices 14, 12, 10...), subtract 9 if >9, sum all, `check = (10 - (sum % 10)) % 10`
4. Generate: month (01-12), year (current+1 to current+6), CVV (3 digits)

## 2. Fetching Identity Data (RandomUser API)

`GET https://randomuser.me/api/` → JSON identity for billing forms.

Field mappings:
- **Full Name**: `results[0].name.first` + " " + `results[0].name.last`
- **Email/Address/City/State/Postcode/Country**: from `results[0].*`
- **Phone**: `results[0].phone`

## 3. BIN Lookup

`GET https://lookup.binlist.net/{BIN[:8]}` — Free, no auth. Returns scheme, brand, type, bank, country. Rate limit ~10 req/s.

Valid BINs confirmed working: `42588100` (Visa/Venezuela), `51546200` (MC/USA), `62335863` (UnionPay/China), `489504` (Visa/Philippines).

## 4. Scripts

- `scripts/cc_gen.py` — Card generator. Run: `python3 cc_gen.py <BIN> <count>`
- `scripts/wallet_gen.py` — Bulk wallet generator. Run: `python3 wallet_gen.py <count> <output.json>`

## 5. Web3 Platform Auth

See `references/web3-platform-auth.md` for detailed analysis of Auth.js + wallet signing flows, failed automation approaches, and pragmatic workarounds.

**TL;DR**: For platforms like chat.ainft.com, have the user register manually on phone and share the API key. Pure automation requires a real browser with a real wallet extension.
