---
name: forever-clean
description: Enforces edit-over-create discipline and clean-code file/function limits across any stack. Runs a phased protocol - locate the concept, decide create-vs-edit, audit size/complexity, refactor only if it earns its cost, execute via targeted diffs, verify integrity. Use when the user asks to add/change code and file sprawl or file bloat is a risk, when reviewing/cleaning up code, or whenever the agent is about to create a new file.
metadata:
  version: 1.0.0
  type: procedure
---

# Forever Clean

Keeps a codebase from growing uncontrolled file count or file size while an
AI agent iterates on it. Complements the `000-context-discipline` and
`010-file-lifecycle-policy` / `020-code-shape-limits` rules if those are
loaded in this project; this skill is the explicit, attachable version of the
same discipline for when rules aren't active or the user wants the full
procedure invoked deliberately.

**Invariant, all phases**: external behavior never changes as a side effect
of organization work. If a proposed change could alter behavior, flag it and
skip it rather than applying it.

**Precedence**: if the `keep` skill (strict task-isolation) is also active,
`keep` wins on scope - any refactor suggestion this skill would normally
apply becomes a note in the final report instead of an action.

## Phase 0 - Budget and inventory

State before doing anything else:
- Net new files allowed this task: 2, unless the user specified otherwise.
- Files already touched: 0.

## Phase 1 - Locate the concept

Before writing anything, search for where this concept already lives:
1. Search the codebase under >= 3 name variations (synonyms, singular/
   plural, abbreviation).
2. If a repo index/architecture doc exists (see project rule
   `010-file-lifecycle-policy` or look for `ARCHITECTURE.md`/`README.md`),
   check it first - it's cheaper than grepping blind.
3. Identify the file(s) that most plausibly already own this concept.

## Phase 2 - Create-or-edit gate

Decide, and say which:
- **Edit**: an existing file owns this concept or the directly adjacent one.
  Default outcome - proceed to Phase 3 on that file.
- **Create**: only if the new code encapsulates a genuinely new secret (a
  design decision, data shape, or algorithm likely to change independently
  of everything else - see `references/refactor-playbook.md` for the full
  test) AND it doesn't fit any existing owner without distorting that
  owner's responsibility.

If create: state `create: <path> - <secret it encapsulates>` and check it
against the budget from Phase 0 and the hard-block list (version-suffixed
names, shallow wrappers, unsolicited doc files - see
`references/thresholds.md`). If it's on the hard-block list, stop and ask
the user instead of creating it.

## Phase 3 - Size/complexity audit of the target

Before editing, check the target file against the limits in
`references/thresholds.md` (language-specific) or the defaults: soft 300 /
hard 500 lines, function soft 50 lines, cyclomatic complexity 10, max 4
params, max 3 nesting levels.

- Under soft limit: edit directly, skip to Phase 5.
- Over soft, under hard: edit directly, but flag it in the final report as a
  refactor candidate.
- Over hard limit: proceed to Phase 4 before or alongside the edit - don't
  let the edit make an already-oversized file worse without addressing it.

## Phase 4 - Refactor decision (only when Phase 3 flags hard-limit breach)

1. Pick the matching recipe from `references/refactor-playbook.md` (god-file,
   long function, duplicated logic, shallow wrapper, too many parameters).
2. Before extracting into a new file, verify the **net-neutral rule**: the
   source file must shrink by at least as many lines as the new file gains,
   minus ~10% glue. If it doesn't clear that bar, the split isn't a real
   reduction - find a different seam or don't split.
3. Run the **depth test**: the new file's public surface should be small
   relative to its implementation (deep module), not a near-1:1 wrapper
   (shallow module). Shallow splits are net negative - don't do them.
4. If no recipe produces a net-neutral, sufficiently-deep split, don't force
   one. Do the requested edit in place, flag the file, and leave the
   structural call to the user.

## Phase 5 - Execute

- Targeted diffs only - never rewrite an untouched file wholesale to change
  one part.
- Strict scope - only the change the task requires; no unsolicited style,
  rename, or "improvement" edits elsewhere in the file.
- If Phase 4 produced a merge/split plan, execute it in small steps and fix
  every import/reference before moving to the next step.

## Phase 6 - Verify integrity

1. Confirm every import/reference to any moved, merged, or deleted code is
   updated.
2. Run the project's build/typecheck/lint/test command if available and
   report the result. If none is available, trace call sites manually and
   state exactly what was checked.
3. Confirm the invariant held: public API, outputs, and side effects
   unchanged (unless the task explicitly asked to change them).

## Phase 7 - Final report

```
files: <created> new (list), <edited> edited (list)
lines: <file>: <before> -> <after>  (repeat per touched file)
budget: <used>/<allowed> new files
flags: <files now over soft/hard limit, with one-line reason, or "none">
integrity: <what was checked - build/test run, or manual trace summary>
```

## Additional resources

- `references/thresholds.md` - full per-language size/complexity table and
  the hard-block naming patterns.
- `references/refactor-playbook.md` - the five refactor recipes in detail,
  the net-neutral and depth tests, and anti-pattern examples.
- `references/context-map.md` - how to build/use a repo index and glossary
  to make Phase 1 search cheap, plus the context-radius heuristic for
  catching under-scoped changes.
