# Telegram Alert Group Architecture

## Multi-Channel Routing Pattern

For crypto monitoring, split alerts into separate Telegram channels by type:

```
🐋 Whale Monitor    → whale activity only (DLMM deploy/close, large transfers)
📡 Alpha Signals    → KOL Twitter mentions, validated tokens
📊 Pool Scanner     → trending pools, TVL/volume changes
🔥 High Conviction  → cross-signals (whale + KOL agree on same token)
💬 Command Center   → interactive group (/status /pools /scan commands)
```

## Setup Steps

1. Create private channels/groups in Telegram
2. Add bot as admin to each channel
3. Get chat_id: send a message to the channel, then `GET https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Store chat_ids in `shared/telegram-groups.json`
5. Route cron job output by content type

## Config Structure

```json
{
  "groups": {
    "whale_monitor": {"name": "Whale Monitor", "chat_id": "", "enabled": false},
    "alpha_signals": {"name": "Alpha Signals", "chat_id": "", "enabled": false},
    "pool_scanner": {"name": "Pool Scanner", "chat_id": "", "enabled": false},
    "high_conviction": {"name": "High Conviction", "chat_id": "", "enabled": false},
    "command_center": {"name": "Command Center", "chat_id": "", "enabled": false}
  }
}
```

## User Preference

User is cost-conscious about API key usage. When they say "stop semua" or "pause all", pause ALL cron jobs immediately without asking which ones. They will re-enable individually when ready.
