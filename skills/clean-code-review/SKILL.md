---
name: clean-code-review
description: Clean-code review that first minimizes the number of files (merging/incorporating them), then shrinks the code inside the resulting files. Scales from simple projects (single pass) to large codebases (staged reading in batches with 'continuar' checkpoints). Use when the user asks to review, clean up, or slim down code with a clean-code focus. Never changes external behavior.
---

# Clean Code Review

Staged review: Phase 0 (read everything, at whatever scale) → Phase 1 (file count)
→ Phase 2 (code size). Phases are strictly ordered. Always state which phase you
are in before proposing changes. No diagnosis, plan, or edit may be based on files
not yet read — reading completeness comes before everything.

## Invariant (applies to both phases)
- External behavior must not change. Public APIs, contracts, side effects, and outputs stay identical.
- After every structural change, update all imports/references and verify integrity (run tests/build if available; otherwise trace call sites manually and report what was checked).
- If a proposed change could alter behavior, flag it and skip it — do not apply.

## Precedence over rules
While this skill is active, its file-consolidation goal OVERRIDES the ~150-200 line
file-size guidance from `000-core-principles.mdc`. A merged file may exceed that limit.
All other always-on rules (targeted diffs, strict scope, no obvious comments) still apply.

## Phase 0 — Scope assessment & complete reading
First, inventory WITHOUT reading contents: list every file in scope with path, line
count, and import/dependency hints (cheap commands: `ls`, `wc -l`, grep of imports).
Then pick the mode:

**Direct mode** — simple/small scope (the whole codebase fits comfortably in one
reading pass, e.g. a handful of files / a few thousand lines total): read everything
now and proceed straight to Phase 1. No extra ceremony for small projects.

**Staged mode** — extensive scope (total size risks exceeding what can be read
reliably in one pass). Reading in batches with persistent notes:
1. Partition files into numbered batches by dependency cluster — files that import
   each other stay in the same batch, so merge candidates are visible within a batch.
2. Create a scratch notes file (`tmp_review_notes.md`) OUTSIDE the review scope.
   It is the review's memory: findings survive there even when earlier files leave
   the context window. Never rely on recalling a file read many steps ago — re-check
   the notes.
3. For each batch: read every file fully; append structured notes per file — role,
   line count, public surface (exports/APIs), merge-candidate hints, waste spotted
   (dead code, duplication); then STOP and post the partial diagnostic:
   `Batch N of M read — <files>. Type 'continuar' to proceed.`
   Do not read the next batch until the user types 'continuar'.
4. After the last batch, compose the COMPLETE diagnostic exclusively from the notes
   file — consolidated map of roles, dependencies, merge candidates, waste — and
   present it. Only then enter Phase 1.

The scratch notes file is ephemeral: delete it after the final report.

## Phase 1 — Reduce FILE COUNT (always first)
Goal: reach the file count the user specified; if none was given, the minimum possible.

1. Map the files in scope using the Phase 0 diagnostic: role, size, dependencies
   between them.
2. Identify merge candidates: files whose content can be incorporated into another
   (small helpers, single-use modules, fragmented utilities, thin wrappers).
3. Propose a consolidation plan: which files absorb which, resulting file list, and
   the final count. Present it before editing.
4. Execute merges with targeted edits; delete absorbed files; fix every import/reference.
5. GATE: confirm the final file structure. Phase 2 must not begin until this count is
   final, and Phase 2 may not reopen it (never re-extract into new files).

Tie-break rule: between shrinking code and shrinking file count, file count ALWAYS wins,
even if the consolidated file becomes longer.

## Phase 2 — Reduce CODE SIZE (only inside the final files from Phase 1)
For each remaining file, in this order:
1. REMOVE what is unnecessary: dead code, unused imports/exports, redundant comments,
   needless boilerplate, premature abstractions.
2. REWRITE more objectively: shorter equivalent constructs, deduplicated logic,
   simplified conditionals — same behavior, fewer lines.
3. FLAG (do not silently change) ambiguity and unnecessary redundancy that requires
   a human decision: unclear names, duplicated business logic with subtle differences,
   contradictory comments.

## Final report
End with a summary: files before → after (with the merge map), lines before → after
per file, integrity checks performed, and the list of flagged items awaiting decision.
In staged mode: confirm all batches were read (N of N) and that the scratch notes
file was deleted.
