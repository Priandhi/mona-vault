# MiMo UltraSpeed — Reference (June 2026)

## Source
- Tweet: https://x.com/xiaomimimo/status/2063993790587904362
- Platform: https://platform.xiaomimimo.com/ultraspeed
- Apply: https://platform.xiaomimimo.com/ultraspeed (Xiaomi account login required)
- Deadline: June 23, 2026 (PDT)

## Specs
- **Model:** MiMo-V2.5-Pro UltraSpeed
- **Params:** 1 Trillion (MoE)
- **Speed:** 1,000+ tokens/s output
- **Hardware:** Standard 8-GPU node (no Cerebras/Groq specialized chips)
- **Collaboration:** Xiaomi MiMo × TileRT joint release

## Pricing
- Chat experience: FREE (limited time, pay-as-you-go phase)
- API: 3x normal MiMo price for ~10x speed boost
- Enterprise: business-mimo@xiaomi.com

## Apply Process
1. Login at platform.xiaomimimo.com (Xiaomi account required)
2. Navigate to /ultraspeed
3. Fill application form
4. Wait for approval
5. Once approved: new API key + endpoint provided

## Current Token Plan vs UltraSpeed
| | Token Plan (Current) | UltraSpeed (Pending) |
|---|---|---|
| Base URL | https://token-plan-sgp.xiaomimimo.com/v1 | TBD (new endpoint) |
| Model | mimo-v2.5-pro | mimo-v2.5-pro-ultraspeed (?) |
| Key type | tp-xxxxx (Token Plan) | TBD (likely sk-xxxxx or new tp-xxxxx) |
| Speed | Normal (~25 tok/s) | 1,000+ tok/s |
| Cost | Free (subscription) | 3x price |
| Status | ✅ Active | ⏳ Apply by Jun 23 |

## After Approval — Config Update Steps
1. Get new API key + base URL from platform console
2. Add to `~/.hermes/config.yaml` under `custom_providers:`
3. Set as primary or keep as optional high-speed provider
4. Update `model.default` if switching primary
5. NEVER mix Token Plan key with UltraSpeed key
6. Test latency before/after: `curl ... -d '{"model":"...","messages":[...],"max_tokens":10}'`

## Notes
- Agent CANNOT apply on behalf of user (requires Xiaomi account login)
- UltraSpeed is SEPARATE from current Token Plan — different credentials
- Do not assume UltraSpeed model ID — wait for official docs after approval
- platform.xiaomimimo.com/ultraspeed is JS-rendered SPA — cannot be scraped headless from VPS
