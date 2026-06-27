---
name: "web3-recon"
description: "Reconnaissance and bypass methodology for indie web3 games behind token gates, captchas, or anti-bot protections. Use when a user is investigating a web3 game, looking for the in-game token's contract, or trying to bypass an in-game gate."
tags:
  - "web3"
  - "game"
  - "recon"
  - "bypass"
  - "exploit"
  - "airdrop"
---
# Web3 Game Recon

> Reconnaissance and bypass methodology for indie web3 games behind token gates, captchas, or anti-bot protections. The class of "look at this game and figure out the moves" workflows.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "web3 game", "indie game", "recon", "find exploit" | `references/web3-game-bypass-recon/` |

## Topic Pages

- `references/web3-game-bypass-recon/SKILL.md` — Recon + bypass methodology for indie web3 games behind token gates

## Cross-Cutting Patterns

1. **Map the surface first:** game state, on-chain interactions, server endpoints, anti-bot protections.
2. **Test from layer 1 to layer N+1** before declaring "no path." User expects exhaustive testing.
3. **Report data, not predictions.** "Tried X, result Y" is better than "this won't work because Z."

## Related

- `ctf-attack` (in hermes/) — sister class for general CTF and prompt-injection work
- `crypto-alpha-sniper` (in crypto/) — for sniping the in-game token
- `web-streaming-platform` (in streaming-platform/) — for the public-facing side of the game
