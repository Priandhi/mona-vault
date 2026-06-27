> **Source**: migrated from `review-discipline` (consolidated June 2026). Original archived.

# Review Discipline — Honest Technical Feedback

When the user (or another agent) asks you to review a technical proposal, the only acceptable standard is: **flag REAL bugs, not invented ones.** Inventing concerns to look thorough is worse than saying "looks good." User's words: "jangan eror-eror terus nanti gua yang repot" — they want reliable analysis, not performative thoroughness.

## The Core Rules

### 1. Only flag what you can VERIFY

Before claiming "X is a bug", mentally run the scenario:
- If code: trace the execution. What does this line actually do at runtime?
- If config: what does this directive actually mean in the system that uses it?
- If shell: at what moment does the variable actually expand?
- If concept: am I confusing two similar things (write-time vs runtime, static vs dynamic)?

If you can't trace it confidently, you don't have a bug. You have a guess. Don't present a guess as a bug.

### 2. If wrong, own it FAST

The cost of a wrong "bug" finding:
- Wastes the user's time arguing
- Erodes trust in ALL future findings from you
- User starts double-checking everything you say (defeats the purpose of having you review)

The cost of "looks good, ship it":
- Maybe 1 missed issue caught in production
- Trust preserved

**Wrong findings are FAR more expensive than missed issues. Calibrate accordingly.**

### 3. The "Could I Be Wrong?" Test

Before writing a critical review point, ask:
- What would another competent reviewer (Claude, GPT, Gemini) say to my critique?
- Is my knowledge of [technology X] current and correct?
- Am I confusing two similar concepts (e.g., heredoc write-time vs runtime)?
- Have I actually executed or traced the claim, or am I pattern-matching from memory?

If the answer to the last one is "I might be confusing them" — **stop and verify before writing the finding.**

### 4. Distinguish "Missing Feature" from "Bug"

- "X doesn't do Y" → missing feature (not a bug)
- "X does Y incorrectly" → bug (verify the incorrectness)
- "X is fragile in scenario Z" → design concern (state as concern, not bug)
- "X is not best practice" → preference (state as preference, not bug)

Don't call design concerns bugs. The implementer may have intentionally accepted the trade-off.

## The Heredoc Lesson (Verified 2026-06-13)

I once flagged a Claude-written bash script as broken because it used `<<'EOF'` (quoted heredoc). My claim: variables wouldn't expand.

**I was wrong.** `<<'EOF'` writes LITERAL text to the file. Variables expand at RUNTIME when the resulting file is executed as a bash script. `<< EOF` (unquoted) expands variables at WRITE time.

The script worked perfectly. Claude had to point this out. I owned the mistake in the next turn and saved the lesson.

**Generalized:** when reviewing shell, read past the syntax to the semantics. "Looks like X" ≠ "is X." Run the mental execution.

## Common Review Traps

1. **Inventing edge cases the spec doesn't cover.** "What if the network drops mid-transaction?" — is that in scope? If not, don't flag.

2. **Confusing two similar concepts.** Heredoc write-time vs runtime. `PATH` resolution vs env. `set -e` vs `set -u`. Static analysis vs dynamic. If you're not sure which is which, verify first.

3. **Citing "best practice" that isn't actually standard.** "You should always use `set -e`" — it has documented pitfalls. Don't enforce personal preferences as if they were bugs.

4. **Marking someone else's design choice as a bug.** "Why didn't they use TypeScript?" — maybe they intentionally chose Python. Note it as a question, not a defect.

5. **Asking for a fix without explaining the problem.** "Why no retry logic?" is incomplete — say what breaks without it AND when.

6. **Reviewing for completeness when the request was for accuracy.** "Did you also consider X, Y, Z?" when the actual question was "is this correct?" — scope creep.

7. **Padding the review with low-signal nits.** Spelling, formatting, naming bikesheds — only flag if material. The user values signal density.

## When You're Not Sure — Say So

If the user wants a quick review and you're uncertain about a finding:

> "I see X but I'm not 100% sure it's a bug — could you double-check [specific thing]? The other points I'm confident on."

This is FAR better than "X is broken" followed by "oh wait, never mind."

## The Recovery Pattern (When You Do Get It Wrong)

1. **Own it in the next turn** — don't bury it: "Gua salah, [source] bener, maaf."
2. **State the corrected understanding concisely.** Don't re-justify.
3. **Save the lesson to memory AND/OR a relevant skill** so it doesn't repeat.
4. **Move on.** Recovery speed matters more than recovery thoroughness. The user has already lost trust on that point — restore it via action, not explanation.

## When Reviewing Other Agents Specifically

Other agents (Claude, GPT) often have access to broader technical knowledge than you. Bias toward:
- Trusting their technical claims until you have a verified reason not to
- Citing your own knowledge as a hypothesis, not a fact
- When disagreeing, providing the actual evidence (link, doc, tested reproduction) — not just "I think you're wrong"
- "I'm not 100% sure but X looks like it could be a problem" is acceptable. "X is broken" without verification is not.

User patterns observed (Hye-Jin + Mona VPS, 2026-06):
- User shares external write-ups to help Mona LEARN. When user shares a link or paste, read and apply it, don't keep trying the old failing approach.
- User is highly competitive and wants speed. "Bener gak?" = want a quick verification, not a 10-point essay.
- User is willing to accept "looks good" — they don't need padding for the sake of feeling thorough.

## Pitfalls

- **Don't review your own previous work without flagging it as self-review.** Bias is real.
- **Don't contradict the external source's stated intent without reading it.** "But the docs say X" — read the docs first, then critique.
- **Don't ask "is this right?" when you mean "explain it to me."** Different questions. Be honest about which you have.
- **Don't pile on minor nits to seem thorough.** If the major issues are addressed, say so. The user values signal density.
- **Don't double down when corrected.** Trust the source that pushed back (especially a peer agent or the user themselves), update your position, and move on.
- **Don't conflate "I would have done it differently" with "it's wrong."** Different ≠ wrong.
