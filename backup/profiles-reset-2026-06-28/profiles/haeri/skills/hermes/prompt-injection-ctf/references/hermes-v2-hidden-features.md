# Hermes Agent V2.0 — Hidden Features Discovered

**Date:** 2026-06-11
**Source:** Web search, active autonomous learning session

---

## Priority 1: Kanban Multi-Agent Board

**What it is:** A Kanban-style visual interface to manage multiple AI agents.

**Key Commands:**
```
/kanban create "task description"     → creates task card
/kanban list --mine                   → see your fleet
/kanban comment t_xyz "context"       → add human context to running task  
/kanban stats                         → inspect without stopping main chat
```

**How it works:**
- When you create a task from the gateway with /kanban create, the originating chat (platform + chat id + thread id) is automatically subscribed to that task's terminal events
- Events: completed, blocked, gave_up, crashed, timed_out
- You can comment on cards while tasks are running — next run will read the comment

**Use Case for CTF:**
```
1. /kanban create "CTF G4 - Rapport approach"
2. Spawn 3 subagents in parallel:
   - Agent 1: Genuine conversation (10+ turns)
   - Agent 2: Encoding exploitation  
   - Agent 3: Language switching
3. Monitor all from Kanban board
4. /kanban comment to add human guidance mid-run
5. Get notified when any agent succeeds
```

**This turns "1000 random attempts" into "orchestrated team attack".**

---

## Priority 2: Shared Working Memory Layer

**What it is:** All agents' findings written in real-time, other agents can read instantly.

**Key insight:**
- Current memory tool is session-based
- This sounds like cross-agent persistent shared state
- Might be Hermes v2 specific

**Use Case:**
```
Agent A does recon → writes to shared memory
Agent B reads Agent A's findings → continues work
No duplication, no context loss between handoffs
```

---

## Priority 3: Multi-Agent Orchestration v0.6.0

**What it is:** Route different content types to different models automatically.

**Example from production:**
```
Use kimi for long-context document analysis
Use minimax for structured reasoning in parallel
ORCHESTRATOR routes content to right model
MERGES outputs automatically
```

**Real-world use:** In production Discord deployments by Hermes users

---

## Priority 4: Light Panda Browser Automation

**What it is:** Built-in browser automation for data scraping and form submissions.

**Use Case:**
- Automate web-based CTF
- Scrape leaderboards
- Interact with web interfaces programmatically

**Note:** We already have browser-agent skill. This might be more native/integrated.

---

## Priority 5: Environment Relevance Gate

**What it is:** Skills gated by environment context — only loads relevant skills when needed.

**Benefit:** Keeps context clean, no skill bloat

---

## Verification Needed

These features are from Hermes v2.0 (recent release). Need to verify:
1. Which features are available in our current Hermes setup
2. Whether Kanban requires v2.0 upgrade
3. How to access /kanban commands in our environment

**Action items:**
- [ ] Check if /kanban is available in our Hermes
- [ ] Test Kanban with simple task
- [ ] Verify Shared Working Memory availability
- [ ] Document setup requirements

---

## What We Already Have (NOT new)

These are already covered by existing skills:
- delegate_task → subagent spawning ✅
- cronjob → scheduled tasks ✅
- memory/session_search → memory management ✅
- browser-agent skill → browser automation ✅
- Model routing → already configured ✅

---

## References

- https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
- https://www.geeky-gadgets.com/autonomous-ai-hermes-v2/
- https://hermes-agent.ai/features/multi-agent
- https://github.com/NousResearch/hermes-agent/issues/344