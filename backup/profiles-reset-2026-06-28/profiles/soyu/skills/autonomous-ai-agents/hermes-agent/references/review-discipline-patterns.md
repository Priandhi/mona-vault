# Review Discipline — Honest Technical Feedback

When reviewing a technical proposal, the only acceptable standard: **flag REAL bugs, not invented ones.** Inventing concerns to look thorough is worse than saying "looks good."

## Core Rules

1. **Only flag what you can VERIFY** — trace execution, don't pattern-match from memory
2. **If wrong, own it FAST** — wrong findings are FAR more expensive than missed issues
3. **The "Could I Be Wrong?" test** — before writing a critical point, ask: what would another competent reviewer say?
4. **Distinguish "Missing Feature" from "Bug"** — "X doesn't do Y" ≠ "X does Y incorrectly"

## The Heredoc Lesson

`<<'EOF'` writes LITERAL text to the file. Variables expand at RUNTIME when the resulting file is executed. `<< EOF` (unquoted) expands at WRITE time. Don't confuse syntax with semantics.

## Common Review Traps

1. Inventing edge cases the spec doesn't cover
2. Confusing two similar concepts (write-time vs runtime, static vs dynamic)
3. Citing "best practice" that isn't actually standard
4. Marking design choices as bugs
5. Asking for fixes without explaining the problem
6. Reviewing for completeness when request was for accuracy
7. Padding with low-signal nits

## When Not Sure

> "I see X but I'm not 100% sure it's a bug — could you double-check?"

This is FAR better than "X is broken" followed by "oh wait, never mind."

## Recovery Pattern

1. Own it next turn: "Gua salah, [source] bener, maaf."
2. State corrected understanding concisely
3. Save lesson to memory/skill
4. Move on — recovery speed > recovery thoroughness
