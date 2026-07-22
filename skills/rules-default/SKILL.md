---
name: rules-default
description: Audit, fix, and create Cursor rules (.cursor/rules/*.mdc). Use when the user asks to review rule formatting, standardize rules, or create a new rule. Reads every existing rule first; if a requested rule already exists or its content is spread across other rules, raises an Open Question instead of creating a duplicate.
---

# Rules Default — Audit & Create

Procedure for keeping `.cursor/rules/` correct, consistent, and free of duplicates.
Always read ALL `.cursor/rules/*.mdc` files before auditing or creating anything.

## Mode A — Audit existing rules
Check every rule against this checklist and fix violations with targeted edits:

1. **File format**: `.mdc` extension (plain `.md` in `.cursor/rules/` is ignored by Cursor);
   valid YAML frontmatter delimited by `---`; body in Markdown.
2. **Frontmatter coherence** (exactly one activation strategy per rule):
   - `alwaysApply: true` → universal rule; `globs`/`description` are ignored by Cursor,
     so remove misleading values that suggest scoping.
   - `globs` set → auto-attached rule; must NOT also have `alwaysApply: true`.
   - `description` only → agent-requested rule; description must state what it does AND when to use it.
   - Nothing → manual rule (@-mention); confirm that is intentional.
3. **Naming**: `NNN-topic.mdc` — 000-099 foundational, 100-899 domain/stack, 900+ meta.
   Lowercase, hyphens, descriptive topic.
4. **Writing quality**: imperative voice ("Never rewrite...", "Use..."); concrete and
   verifiable directives, no vague advice ("write good code"); one concern per rule;
   bullet points over prose; under ~200 words if `alwaysApply: true`, under 500 lines always.
5. **Cross-rule consistency**: no directive repeated in two rules; no contradictions
   (if found, raise an Open Question — do not silently pick a side).

Report: table of files → issues found → fix applied or Open Question raised.

## Mode B — Create a new rule
1. Read all existing rules and build a map of every directive already covered.
2. **Duplicate gate** — compare the requested rule against the map:
   - Fully covered by an existing rule → do NOT create. Raise an Open Question.
   - Partially covered / spread across separate items of other rules → do NOT create yet.
     Raise an Open Question listing each overlapping item and its source rule.
   - Genuinely new → create following the checklist from Mode A (format, naming,
     activation strategy, writing quality).
3. Choose activation intent explicitly: always / globs / agent-requested / manual.
   Default to the narrowest scope that satisfies the user's request; use
   `alwaysApply: true` only for behavior that must hold on every prompt.
4. After creating, re-run the cross-rule consistency check (Mode A, item 5).

## Open Questions — format
When a duplicate, overlap, or contradiction is found, stop and present:

```
## Open Question
Requested: <what the user asked for>
Found:
- <rule-file.mdc> · "<existing directive quoted>" — <overlaps how>
- <rule-file.mdc> · "<existing directive quoted>" — <overlaps how>
Options:
1. Merge into <rule-file.mdc> (extend the existing rule)
2. Create the new rule and remove the overlapping items from the rules above
3. Keep as is (no change)
Awaiting decision.
```

Never resolve an Open Question unilaterally. Wait for the user's choice, then apply it
with targeted edits and confirm the final state of `.cursor/rules/`.
