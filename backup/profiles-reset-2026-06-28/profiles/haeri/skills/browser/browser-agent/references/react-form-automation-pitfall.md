# React Form Automation Pitfall (June 11, 2026)

## Context

**Task:** Add TokenRouter as custom provider to 9Router dashboard (React SPA)
**Goal:** Fill form with Name, Prefix, Base URL, API Key via browser automation
**Result:** FAILED — form submitted with empty values despite JS console showing values set

## The Problem

React uses **controlled components** where form state lives in React's internal state tree, not DOM values. Setting `input.value` directly only updates the DOM — React's state remains unchanged.

When form submits, React reads from its **own state**, not `input.value`. Result: form submission sends empty/default values.

## Attempted Fixes (All Failed)

### Attempt 1: Direct value assignment
```javascript
document.querySelectorAll('input')[1].value = 'TokenRouter';
document.querySelectorAll('input')[2].value = 'tokenrouter';
document.querySelectorAll('input')[3].value = 'https://api.tokenrouter.com/v1';
document.querySelectorAll('input')[4].value = 'sk-ciJ...M8Z4';
```
**Result:** Values visible in DOM inspector, but form submits empty. React state not updated.

### Attempt 2: Trigger React synthetic events
```javascript
const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
  window.HTMLInputElement.prototype, 'value'
).set;
const input = document.querySelectorAll('input')[1];
nativeInputValueSetter.call(input, 'TokenRouter');
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
```
**Result:** Events fire, but React's `onChange` handler doesn't recognize them as "trusted" user input. State still not updated.

### Attempt 3: Multiple event types
```javascript
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
input.dispatchEvent(new Event('blur', { bubbles: true }));
input.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
```
**Result:** Same issue. React filters out programmatically-triggered events.

### Attempt 4: Focus + type simulation
```javascript
input.focus();
// Attempted to use browser_type via ref ID
// Modal closed before browser_type could execute
```
**Result:** Modal closed between `browser_click` and value population. Timing issue.

## Root Cause

React's controlled input pattern:
```jsx
<input 
  value={state.name} 
  onChange={e => setState({name: e.target.value})}
/>
```

The `onChange` handler is the **only** way to update `state.name`. Setting `input.value` directly bypasses React entirely. When form submits, React reads `state.name` (still empty) not `input.value` (populated by script).

React's synthetic event system **filters out** programmatically-triggered events unless they pass internal "trusted" checks (which vary by React version and are intentionally undocumented to prevent automation).

## Why Playwright Would Work (But Hermes Browser Tools Don't)

**Playwright's approach:**
- Uses Chrome DevTools Protocol (CDP) to inject events at the **browser engine level**
- Events appear as genuine user input to React's event system
- Can trigger `focus()` → `type()` → `blur()` sequence that React recognizes

**Hermes browser tools limitations:**
- `browser_console` runs in page context (user-space JS)
- `browser_type` sends keystrokes but timing/focus issues with modals
- No CDP-level event injection

## The 9Router API Approach (Also Failed)

**Attempted:**
```bash
curl -X POST "http://localhost:20128/api/providers" \
  -H "Content-Type: application/json" \
  -b /tmp/cookies.txt \
  -d '{"provider_type":"openai","name":"TokenRouter",...}'
```

**Result:** `{"error":"Invalid provider"}` — API format undocumented, trial-and-error failed.

## The Solution: Ask User

**Time spent on automation:** ~2 hours (25+ tool calls)
**Time for user to fill form manually:** 1 minute

When React form automation fails AND API is undocumented:
1. Stop after 10-15 attempts
2. Explain the technical blocker briefly (1 sentence: "React forms don't accept scripted input")
3. Ask user to fill manually
4. Provide exact values they need to paste

**User's reaction:** "done bos wkwk" — completed in under 60 seconds.

## When to Use Browser Automation vs API vs Manual

| Scenario | Best Approach |
|----------|---------------|
| Static HTML forms | ✅ Browser automation (Hermes tools work) |
| React/Vue/Angular forms | ⚠️ API first, manual fallback |
| Admin dashboards with docs | ✅ API (documented endpoints) |
| Admin dashboards no docs | 🛑 Manual (trial-and-error > 15 min) |
| One-time setup | 🛑 Manual (automation overhead not worth it) |
| Repeated bulk operations | ✅ API or Playwright (if available) |

## Signals to Stop Automating

1. **10+ failed attempts** with different approaches
2. **React/Vue/Angular SPA** detected (check for `__REACT_DEVTOOLS_GLOBAL_HOOK__`)
3. **API returns "Invalid"** with no error details after 3+ format attempts
4. **User asks "gimana solusinya"** (wants recommendation, not more attempts)
5. **Task is one-time setup** (automation ROI negative)

## Key Takeaway

**Don't fight React state for one-time tasks.** The effort to reverse-engineer React's internal event handling is rarely worth it when:
- User can complete task in < 5 minutes manually
- No API documentation exists
- Task is not repeated/bulk operation

Save browser automation for:
- Static forms
- Documented APIs unavailable
- Bulk repeated tasks (10+ iterations)
- Tasks user explicitly cannot do (CAPTCHA solving, etc.)

## User Feedback Signals from This Session

**"gimana solusinya yang terbaik"** → wants recommendation, not more failed attempts
**"serah kamu dah"** → trusts agent decision (including "ask user to do it")
**"done bos wkwk"** → confirmation that manual was faster

When user says "serah kamu" — that includes the option to say "this is faster if you do it manually, here's exactly what to fill". Don't interpret it as "keep trying automation forever".
