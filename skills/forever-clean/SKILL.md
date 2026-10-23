---
name: forever-clean
description: Edit-over-create and shape discipline for any codebase. Reviews and adjusts existing files before creating new ones, keeps the structure the user or the project already uses (minimalist default when neither says), and avoids both extremes - dozens of tiny files or one file with thousands of lines - while preserving behavior. Every delete or move stays inside the working repository. Use when adding or changing code, whenever the agent is about to create a new file, when asked to "simplify the repo", "clean this up", "this file is too big", "too many files", "don't create new files", or when reviewing code for integrity and functionality.
metadata:
  version: 2.0.0
  type: procedure
---

# Forever Clean

Keeps a repository simple while an AI agent iterates on it: the fewest
moving parts that still keep each file about one thing. Works in any project
and any language. Nothing here depends on a specific rules set being loaded.

Two failure modes, equally bad:
- **Sprawl**: dozens of tiny files, wrappers, one-function modules, `utils`
  buckets. Each file costs a retrieval, an import and a context slot.
- **Bloat**: one file with thousands of lines mixing concerns that change for
  different reasons. Every small change means scrolling past unrelated code.

Large files and many files are both fine when each file is cohesive. The
problem is the exaggeration, judged against the project itself, never
against a fixed number.

**Invariant, all phases**: external behavior never changes as a side effect
of organization work - public API, outputs, side effects, error contracts.
If a change could alter behavior, flag it and skip it.

**Scope rule**: if the user or another active skill/rule restricts scope more
tightly, the tighter one wins. This skill never widens a task; refactor
suggestions it cannot apply become notes in the final report.

## Shape source - who decides the structure

Resolve in this order and state which applies, once, in Phase 0:

1. **User instruction** for this task (file names, layout, "keep it in one
   file", "split by feature"). Follow it exactly, even if it deviates from
   the defaults below.
2. **Project convention**: how sibling files are already organized, plus any
   limits the project itself declares - linter config, `CONTRIBUTING.md`,
   `ARCHITECTURE.md`, `CLAUDE.md`/`AGENTS.md`, `.cursor/rules`. The project's
   own numbers override anything in `references/signals.md`.
3. **Minimalist default** (only when 1 and 2 are silent): add to the file
   that already owns the concept; let a file grow while it stays about one
   concern; split only when distinct reasons to change coexist; merge files
   that always change together or exist only to forward calls.

## Phase 0 - Frame

Before touching anything, state:
- `root: <absolute path>` - the working repository (`git rev-parse
  --show-toplevel`, or the directory the user named). Every write, move and
  delete in this task stays under it. See Safety.
- `shape: user | project | minimalist` - which shape source applies.
- `footprint: edit ~N, create ~M, delete ~K` - the planned change. Later
  deviation needs a one-line reason, not permission.

## Phase 1 - Review what exists

Never create from a blank page. Before writing:
1. Search the concept under at least 3 name variations (singular/plural,
   synonym, domain abbreviation). Check an index/architecture doc first if
   the project has one; do not create one unless asked.
2. Read the candidate owner files end to end, not just the grep hits.
   Understand what they already do, what is dead, what is duplicated.
3. Read 2-3 sibling files to learn the layout convention (naming, what a
   "module" means here, where tests live).
4. Note the context radius: how many directories the change will touch.
   More than 3 is a signal the task is wider than asked or a boundary is
   wrong - say so before proceeding.

## Phase 2 - Create-or-edit decision

Default is **edit** the owner found in Phase 1. State the decision in one
line: `edit: <path> - <why it owns this>` or `create: <path> - <secret it
encapsulates>`.

Create only when at least one holds:
- The user asked for the file, or the shape source requires it (framework
  convention: a route file, a migration, a test mirroring a source file).
- The code encapsulates a genuinely new secret - a design decision, data
  shape, algorithm or external integration that will change independently -
  AND adding it to the owner would make the owner mix unrelated concerns.
  "It is a different function" or "the file is getting long" is not a new
  secret. See `references/refactor-playbook.md`.

Hard blocks - never create without an explicit request. Stop and ask; with
no user present, edit the nearest owner instead and flag it:
- Hedge names: `*_v2`, `*_new`, `*_old`, `*_fixed`, `*_final`, `*_copy`,
  `enhanced_*`, `improved_*`, `*.bak`, `*.orig`.
- Shallow wrappers that only forward calls or re-export.
- Unsolicited recap files (`SUMMARY.md`, `NOTES.md`, `CHANGES.md`,
  `REPORT.md`) - put that in the chat response.
- A second copy of logic already owned elsewhere "to keep this file short".

## Phase 3 - Shape check of the target

Check the target file and its directory for exaggeration in either
direction using `references/signals.md`. Measure with the project's own
tools when available (linter, `wc -l`, `git log`); otherwise estimate and
say which values were measured and which were estimated.

- No signal: do the edit (Phase 5).
- Signal: still do the edit - never block the task on structure - then run
  Phase 4 in the same response. Do not make an already exaggerated file
  worse without at least proposing the fix.

## Phase 4 - Rebalance (only when Phase 3 found a signal)

1. Pick the matching recipe from `references/refactor-playbook.md`:
   consolidate (sprawl) or split (bloat), long function, duplicated logic,
   shallow wrapper, too many parameters, hedge-named duplicate.
2. Every move must pass the **net-simplification test**: fewer moving parts
   or clearer ownership, behavior unchanged. A split must also pass the
   **net-neutral rule** (source shrinks at least as much as the new file
   grows, minus ~10% glue) and the **depth test** (small public surface,
   substantial implementation). A merge must not produce a file mixing
   concerns that change for different reasons.
3. If no recipe gives a clear win, leave the structure alone and flag it.
   A forced split is sprawl; a forced merge is bloat.
4. Present the plan (which files absorb which, resulting layout) before
   executing when the move touches files beyond those already in scope.

## Phase 5 - Execute

- Targeted diffs only; never rewrite an untouched file wholesale.
- Small steps; after each move or merge, fix every import, reference, path
  string and config entry before the next step.
- Delete only files this task absorbed or orphaned - tracked files via
  `git rm`, inside `root`, listed before removal. See Safety.

## Phase 6 - Review and improve the touched code

Re-read every touched file end to end after editing. Inside the touched
scope, apply behavior-preserving improvements:
- Remove dead code, unused imports/exports, redundant comments, leftover
  compatibility shims from the change itself.
- Deduplicate snippets the edit made obviously redundant.
- Simplify conditionals and naming where the result reads better and the
  behavior is provably identical.

Checklist in `references/refactor-playbook.md`. Anything that could change
behavior, or that lives outside the touched files, is flagged in the report,
not applied - unless the user asked for a repository-wide cleanup.

## Phase 7 - Verify integrity

1. Every reference to moved, merged or deleted code is updated - grep for
   the old names and paths, including strings in configs and docs.
2. Find the project's check commands: `package.json` scripts, `Makefile`,
   `justfile`, `pyproject.toml`, `go.mod`, `Cargo.toml`, CI workflow.
   Run the build/typecheck/lint/tests that exist and quote the decisive
   output line. With no runner available, trace call sites manually and
   state exactly what was traced.
3. Confirm the invariant: public API, outputs, side effects unchanged
   unless the task explicitly changed them. No success claim without
   evidence from step 2.

## Phase 8 - Report

```
root: <path>            shape: user | project | minimalist
decision: edit|create: <path> - <reason>
files: <created> new, <edited> edited, <deleted> deleted (net <+/-n>)
lines: <file>: <before> -> <after>   (per touched file)
signals: <sprawl|bloat signal found, measured|estimated, or "none">
rebalance: <applied recipe, or "proposed only", or "none">
improvements: <behavior-preserving cleanups applied in touched files>
integrity: <command run + decisive output line, or manual trace summary>
flags: <items left for a human decision, or "none">
```

## Safety - nothing is destroyed outside the working repository

- Every delete, move, rename or overwrite targets an absolute path that
  starts with `root` from Phase 0. Resolve symlinks before checking. If the
  path does not start with `root`, do not touch it, whatever the reason.
- Never touch parent directories, the home directory, other repositories,
  global tool configuration (`~/.claude`, `~/.cursor`, `~/.config`,
  `~/.ssh`), system paths, package caches, or temp directories other
  sessions may use.
- Inside the repository, never delete without an explicit request: `.env*`
  and other secrets, databases and data directories, uploads, lockfiles,
  git-ignored files (they often hold local data), applied migrations, or
  anything the task did not itself absorb or orphan.
- Prefer reversible removals: `git rm` for tracked files. No `rm -rf` on a
  variable, glob or relative path. No `git clean`, `git reset --hard`,
  `--force`, or history rewrite as part of organization work.
- List what will be removed before removing it. With doubt, or with no user
  present, keep the file and flag it.
- Never edit ignore files or exclusion rules to hide something instead of
  deciding about it.

## Additional resources

- `references/signals.md` - how to find the project's own limits, sprawl and
  bloat signals measured against the project, fallback orientation bands,
  cheap measurement commands, exemptions.
- `references/refactor-playbook.md` - the tests (new secret, depth,
  net-neutral, net-simplification), consolidate/split and other recipes,
  the Phase 6 review checklist, anti-patterns in both directions.
