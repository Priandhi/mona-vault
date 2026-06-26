# Receipt — Delete duplicate TokenRouter-01 from 9Router

**Date**     : 2026-06-15
**Agent**    : MONA — The Architect
**Task**     : Remove duplicate TokenRouter entry created with wrong provider ID

## Context
User noticed 9Router admin panel showing TokenRouter twice:
- Top: "6 Connected" — the legit group (1 primary + 5 bot-specific keys, all sharing `provider=openai-compatible-chat-56c9661d-9921-4da5-8879-85241edea402`)
- Bottom: "1 Connected" — `TokenRouter-01` I had just added with wrong provider ID (`openai-compatible-chat-tokenrouter-01`), creating a separate provider entry

## Result
✓ **Deleted** row id `577eae69-c003-4ec5-bcb9-2b5fc4f02ccd` (name=`TokenRouter-01`)
✓ **Backup saved**: `/tmp/tokenrouter-01-backup-20260615-105004.json` (apiKey masked)
✓ **Verified gone**: 0 rows remaining with that id
✓ **Original 6 intact** (MiniMax-M3 + MONA/YERIN/YUNA/SOYU/HAERI, all active)

## Decisions
- **Why this happened**: I picked provider ID `openai-compatible-chat-tokenrouter-01` (custom pattern) when adding the new connection, but the existing 6 already use `56c9661d...` provider ID. 9Router groups by `provider` field, so different IDs = different entries in the list view.
- **Why kept the 6 split**: User asked "why not one per provider?" — explained quota isolation. Each of 5 bots has its own key, so 1 bot exhausting rate limit doesn't kill the other 4. Architecture is intentional, not a bug.
- **Why deleted vs edited**: TokenRouter-01 was never used (`lastUsedAt=null`, `consecutiveUseCount=0`, created 2h ago), no other config references it, no in-flight requests. Clean delete is safe.

## Issues
- **Lesson learned**: When adding a new connection under an existing provider, MUST reuse the same `provider` UUID as siblings, otherwise it creates a separate group. Pattern: `openai-compatible-chat-<provider>-<key_suffix>` is the "custom" form. The original 6 were created with the fixed UUID `56c9661d...` which is the "stock" TokenRouter slot.
- Need to verify in next bot-onboarding task: always check existing `provider` UUID before INSERT.

## Next Steps
- None — clean state restored
- If user wants to add a new TokenRouter key in the future, use the same `provider=openai-compatible-chat-56c9661d-9921-4da5-8879-85241edea402` with a unique `name` (e.g. `MiniMax-M3-NEWBOT`)
- Consider adding this gotcha to a skill/memory so I don't repeat it
