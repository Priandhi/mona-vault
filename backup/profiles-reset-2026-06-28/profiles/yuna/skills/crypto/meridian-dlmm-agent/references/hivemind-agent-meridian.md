# HiveMind & Agent Meridian Setup

## What is Agent Meridian / HiveMind?

**Agent Meridian** is the community registration system for Meridian agents. Each agent gets a unique `agentId` and connects to the central server at `api.agentmeridian.xyz`.

**HiveMind** is the community learning layer — agents share lessons (what worked, what failed) and pull shared lessons from other agents. This creates a collective intelligence where all Meridian agents learn from each other's trades.

## Two Separate Auth Systems

Meridian has **two independent authentication systems** that are often confused:

### 1. Agent Meridian API (`config.api`)

Used by `tools/agent-meridian.js` for screening data enrichment.

```
user-config.json:
  agentMeridianApiUrl: "https://api.agentmeridian.xyz/api"
  publicApiKey: "bWVyaWRpYW4taXMtdGhlLWJlc3QtYWdlbnRz"

Header: x-api-key: {publicApiKey}
```

### 2. HiveMind (`config.hiveMind`)

Used by `hivemind.js` for community lesson sharing.

```
user-config.json:
  hiveMindUrl: "https://api.agentmeridian.xyz"
  hiveMindApiKey: "bWVyaWRpYW4taXMtdGhlLWJlc3QtYWdlbnRz"
  hiveMindPullMode: "auto"
  agentId: "agt_70eec351baa90156fa761b84"

Header: x-api-key: {hiveMindApiKey}
```

**PITFALL:** Both use `x-api-key` header but read from DIFFERENT config fields. Setting `publicApiKey` does NOT enable HiveMind — you need `hiveMindApiKey` separately.

## Config Priority

`config.js` reads in this order (first non-empty wins):
```
1. user-config.json field
2. process.env fallback
3. DEFAULT_* constant
```

Specific lookups:
```javascript
// Agent Meridian
publicApiKey: nonEmptyString(u.publicApiKey, process.env.PUBLIC_API_KEY, DEFAULT_AGENT_MERIDIAN_PUBLIC_KEY)
agentMeridianApiUrl: nonEmptyString(u.agentMeridianApiUrl, process.env.AGENT_MERIDIAN_API_URL, DEFAULT_AGENT_MERIDIAN_API_URL)

// HiveMind
apiKey: nonEmptyString(u.hiveMindApiKey, process.env.HIVEMIND_API_KEY, DEFAULT_HIVEMIND_API_KEY)
url: nonEmptyString(u.hiveMindUrl, DEFAULT_HIVEMIND_URL)
```

Default values (from config.js):
```javascript
DEFAULT_AGENT_MERIDIAN_API_URL = "https://api.agentmeridian.xyz/api"
DEFAULT_AGENT_MERIDIAN_PUBLIC_KEY = "bWVyaWRpYW4taXMtdGhlLWJlc3QtYWdlbnRz"
DEFAULT_HIVEMIND_URL = "https://api.agentmeridian.xyz"
DEFAULT_HIVEMIND_API_KEY = "DEFAULT_HIVEMIND_API_KEY"  // placeholder — must be overridden
```

## Setup Steps

### 1. Add to .env (optional — user-config.json takes precedence)

```env
AGENT_MERIDIAN_API_URL=https://api.agentmeridian.xyz/api
AGENT_MERIDIAN_PUBLIC_KEY=bWVyaWRpYW4taXMtdGhlLWJlc3QtYWdlbnRz
```

### 2. Add to user-config.json

```json
{
  "agentMeridianApiUrl": "https://api.agentmeridian.xyz/api",
  "publicApiKey": "bWVyaWRpYW4taXMtdGhlLWJlc3QtYWdlbnRz",
  "hiveMindUrl": "https://api.agentmeridian.xyz",
  "hiveMindApiKey": "bWVyaWRpYW4taXMtdGhlLWJlc3QtYWdlbnRz",
  "hiveMindPullMode": "auto",
  "agentId": "agt_70eec351baa90156fa761b84"
}
```

### 3. Restart Meridian

```bash
pm2 restart meridian --update-env
```

### 4. Verify

```bash
# Check agent registration
curl -s "https://api.agentmeridian.xyz/api/hivemind/agents/register" \
  -X POST -H "Content-Type: application/json" \
  -H "x-api-key: bWVyaWRpYW4taXMtdGhlLWJlc3QtYWdlbnRz" \
  -d '{"agentId":"agt_70eec351baa90156fa761b84","reason":"test"}'

# Expected: {"agentId":"agt_...","firstSeenAt":"...","lastSeenAt":"...","ok":true}
```

## HiveMind Lifecycle

### Bootstrap (startup)

```javascript
// hivemind.js — called from index.js line 49
bootstrapHiveMind().catch(err => log("hivemind_warn", `Bootstrap failed: ${err.message}`));
```

Steps:
1. `isHiveMindEnabled()` — checks if both URL and API key are non-empty
2. `ensureAgentId()` — reads from user-config.json or generates new one
3. `registerHiveMindAgent()` — POST to `/api/hivemind/agents/register`
4. If `pullMode === "auto"`: pull lessons + presets

### Background Sync (every heartbeat interval)

```javascript
startHiveMindBackgroundSync();  // index.js line 50
```

- Registers heartbeat at regular intervals
- Pulls shared lessons (if pullMode is "auto")
- Pulls community presets

### Lesson Flow

```
Agent closes position → records performance
  ↓
pushHiveLesson(lesson) → POST to HiveMind API
  ↓
Other agents pull → sharedLessons injected into LLM prompt
```

## HiveMind Cache

File: `hivemind-cache.json` (in Meridian root)

Contains:
- `sharedLessons[]` — lessons from other agents
- `lastSync` — last successful sync timestamp

First run: pulls 12 lessons from community. These are injected into the screening/management LLM prompts so the agent can learn from other agents' mistakes.

## Telegram Commands

```
/hive          — Show HiveMind status (enabled/disabled, agent ID)
/hive pull     — Manual pull of shared lessons + presets
```

## What Gets Shared

Lessons include:
- **Performance events** — position outcomes (PnL, strategy, pool metrics)
- **Rules** — derived from patterns (e.g. "FAILED: TEST-SOL, strategy=spot, PnL -30.93%")
- **Tags** — `failed`, `success`, etc.
- **Scores** — weighted by recency and outcome

## PITFALLS

- **Server downtime:** Agent Meridian API sometimes returns 502 Bad Gateway. Bootstrap fails silently (Promise.allSettled). No error in logs — just no hivemind messages. Verify with direct curl test.
- **HiveMind not logging:** Unlike Charon (which logs "[CHARON] Fetched N signals"), HiveMind does NOT log its bootstrap/sync status to PM2 stdout. Check `hivemind-cache.json` for `sharedLessons` to verify it's working.
- **Two different API keys:** `publicApiKey` and `hiveMindApiKey` are separate fields. Both need to be set. The default `hiveMindApiKey` is a placeholder string, not the actual key.
- **Agent ID persistence:** `agentId` in user-config.json is the persistent identity. If lost, a new agent registers and loses connection to previous shared lessons.
