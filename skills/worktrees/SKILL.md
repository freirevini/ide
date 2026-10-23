---
name: worktrees
description: Manages git worktrees as isolated lanes for risky, parallel or exploratory work in any repository with any AI. Creates a lane under a git-ignored directory inside the repository on its own branch, runs all work with the lane as working directory, tracks file ownership per lane, shows the diff against the base and asks before integrating, and removes the lane only after everything is merged or archived. Every git mutation (worktree add or remove, branch create or delete, merge, rebase, cherry-pick, prune) waits for explicit confirmation. Use for a refactor that could break the active checkout, parallel tasks or agents on separate branches, spikes that may be discarded, dependency upgrades, or when asked "use a worktree", "work on an isolated branch", "run these in parallel", "try it without touching main", "cria uma worktree", "isola essa mudança", "trabalha em paralelo", "testa sem mexer no checkout". Not for single-file changes, documentation edits, small fixes, or repositories whose submodule layout worktrees do not handle.
metadata:
  version: 1.0.0
  type: procedure
  source: "adapted from akitaonrails/my-skills worktrees (Fabio Akita, 2026), generalized for any project and any AI"
---

# Worktrees - isolated lanes for risky or parallel work

A risky refactor in the main checkout leaves the user with a broken tree and
half-finished work they cannot switch away from. Two agents editing the same
checkout overwrite each other. A git worktree gives each piece of work its
own directory and branch, sharing one repository, so the main checkout stays
usable and lanes can be compared, integrated or thrown away cleanly.

**Governs**: lane planning, path and branch selection, file ownership per
lane, delegation into a lane, diff review, integration and cleanup.

**Does not touch**: the content of the work itself, the project's branch
naming when it declares one, remote branches, branch protection. It never
pushes, merges or deletes without the user's confirmation for that exact
operation.

**Invariants**:
- Lanes live inside the repository under a git-ignored directory; the main
  checkout is never modified by lane work.
- Every git mutation is shown as the exact command and confirmed before it
  runs.
- A lane with uncommitted changes is never removed.
- One lane, one owner, one set of files; overlapping ownership is resolved
  before work starts.

## Layout

Default lane path and branch, used unless the user or the project convention
says otherwise (`AGENTS.md`, `.rules/git.md`, `CONTRIBUTING.md`):

```
.worktrees/<slug>/          lane directory (git-ignored)
<type>/<slug>               branch, e.g. feat/auth-oauth, spike/new-parser
```

Do not create lanes as sibling directories of the repository: they escape
the ignore rules, the safety root and the user's view of the project. A
project that already uses another layout (`../repo-feature`, `worktrees/`)
keeps it; record which layout applies in Phase 1.

Optional manifest, local and git-ignored, when more than one lane exists:

```json
{ "lanes": [ { "slug": "auth-oauth", "branch": "feat/auth-oauth",
  "path": ".worktrees/auth-oauth", "base": "main", "purpose": "...",
  "owner": "agent-1", "areas": ["src/auth", "tests/auth"],
  "status": "active", "created": "2026-10-23" } ] }
```

Keep it at `.worktrees/lanes.json`, or as a section of the task's handoff
document when the project uses `context-out`.

## Phase 0 - Pre-flight

```bash
git rev-parse --show-toplevel           # inside a repository; this is root
git status --short --branch             # current branch, dirty state
git worktree list                       # existing lanes, path and branch conflicts
git branch --list '<branch>'            # must be empty
git ls-remote --heads origin '<branch>' # must be empty, when a remote exists
git check-ignore -q .worktrees && echo ignored || echo "add .worktrees/ to .gitignore"
```

Stop and ask when: not inside a repository; the branch already exists locally
or remotely; the chosen path is already a worktree; the main checkout has
uncommitted changes that the lane work depends on; the repository has
submodules the project has not configured for worktrees.

**Complete when**: root, base branch, slug, branch name and layout are
written down and no conflict remains.

## Phase 1 - Plan the lane

State in one block before creating anything:

```
lane: <slug> - purpose: <one line>
base: <branch or commit> - branch: <type>/<slug> - path: .worktrees/<slug>
areas: <directories or files this lane owns>
parallel lanes: <none | list with their areas; no overlap>
integration: merge | cherry-pick | discard - decided by the user at Phase 4
```

When two lanes would touch the same files, split the work differently or run
them sequentially. Ownership prevents merge conflicts between parallel agents.

## Phase 2 - Create the lane

Ensure the ignore entry first (append `.worktrees/` to `.gitignore` only when
missing; never rewrite the file). Then show and confirm:

```bash
git worktree add -b <type>/<slug> .worktrees/<slug> <base>
```

Register the lane in the manifest or handoff document. Report the absolute
lane path; every later command in this lane uses it as working directory.

## Phase 3 - Work inside the lane

- Run build, test and edit commands with the working directory set to the
  lane path. Never edit the main checkout for lane work.
- A second agent or a fresh session assigned to the lane receives the lane
  path, the branch, the owned areas and the task; nothing else is shared.
- Commit inside the lane only when the user asked for commits or approved
  checkpoint commits; otherwise leave changes in the working tree and say so.
- Apply `forever-clean` inside the lane as in any checkout: edit over create,
  no unsolicited files.
- Record progress in the manifest or handoff document when work pauses.

## Phase 4 - Integrate

1. Verify the lane with the project's own gate (the commands `AGENTS.md`
   declares, or `verification-planning`'s evidence path when one was built).
   Quote the decisive output line.
2. Show the diff between the lane branch and its base:

   ```bash
   git -C .worktrees/<slug> diff <base>...HEAD --stat
   git -C .worktrees/<slug> diff <base>...HEAD
   ```

3. Ask the user how to integrate: merge, cherry-pick chosen commits, open a
   PR from the branch, or discard. Show the exact command and confirm.
4. Run the integration from the main checkout (or the user-approved
   integration checkout). Conflicts are resolved deliberately and the gate is
   rerun on the integrated tree before declaring done.

## Phase 5 - Clean up

Only after the work is merged, pushed to a branch the user keeps, or
explicitly discarded:

```bash
git -C .worktrees/<slug> status --short   # must print nothing
git worktree remove .worktrees/<slug>
git worktree prune
git branch -d <type>/<slug>               # only when integrated and the user agrees
```

Each command is shown and confirmed. A lane with uncommitted changes is kept
and flagged; `--force` is never used. Update the manifest or handoff document:
status `integrated`, `archived` or removed.

## When to use

- Refactors or migrations that could leave the active checkout broken.
- Parallel tasks or agents that must not share a working tree.
- Spikes and prototypes that may be discarded without trace.
- Dependency upgrades with a long install or build.
- The user asked for a worktree, or an isolated branch with its own directory.

## When not to use

- Single-file changes, documentation, small fixes: use a branch in place.
- Repositories with submodule layouts that worktrees do not handle.
- When the project's own tooling already provides isolation (the agent's
  built-in worktree mode, a container per task) and the user prefers it.

## Report

```
## Worktree lane
lane: <slug> - path: <absolute path> - branch: <type>/<slug> - base: <ref>
areas owned: <list> - parallel lanes: <none | list>
work: <summary of changes in the lane> - commits: <n | none, left in working tree>
verification: <command - decisive output line>
diff vs base: <files changed, +/- lines>
integration: merged | cherry-picked <shas> | PR <url> | discarded | pending user decision
cleanup: removed | kept (<reason>) - branch: deleted | kept
manifest: updated at <path> | not used
open questions: <numbered list or "none">
```

## Safety

- Every path this skill creates or removes is absolute, resolved through
  symlinks, and starts with the repository root from Phase 0. A lane path
  outside root is refused whatever the reason.
- Never touch the home directory, other repositories, global tool
  configuration, package caches or temp directories other sessions may use.
- Never run `git worktree remove --force`, `git clean`, `git reset --hard`,
  `git push --force`, branch deletion with `-D`, or any history rewrite as
  part of lane work. Interactive rebase is not available to agents; ask the
  user to run it when the project requires one.
- Never delete a dirty lane, never delete a branch that was not integrated or
  explicitly discarded, never remove a lane another agent still owns.
- List what will be removed before removing it. With doubt, or with no user
  present, keep the lane and flag it in the report.
- Lane work inherits the project's own rules: `.env*` and secrets are not
  copied into reports, and nothing outside the owned areas is edited.
