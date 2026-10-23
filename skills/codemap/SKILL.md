---
name: codemap
description: Builds and refreshes a hierarchical map of an unfamiliar repository for any AI and any stack, only on explicit request because it is expensive. Writes one `codemap.md` per folder that owns a responsibility (Responsibility, Design, Flow, Integration) plus a root atlas with purpose, entry points and a directory table linking each sub-map, and records the mapped git sha (`last-mapped`) so later refreshes touch only folders that changed. Optionally registers a short "Repository map" section in `AGENTS.md`. Use when asked to "map this codebase", "create a codemap", "document the architecture for agents", "refresh the codemap", "mapear o repositório", "cria o codemap", "atualiza o mapa do código", or when onboarding into a large unknown repository. Not for routine feature work, not for small repositories that fit in one read, not a substitute for AGENTS.md (agents-md) or for README writing.
metadata:
  version: 1.0.0
  type: procedure
  source: "adapted from akitaonrails/my-skills codemap (Fabio Akita, 2026), generalized for any project and any AI"
---

# Codemap - a navigable map of the repository, refreshed by diff

An agent entering a large repository re-reads the same files every session
and still misses how modules connect. A map per module, in precise technical
terms, with a root atlas and a recorded commit, lets any agent jump to the
right folder and lets the next run refresh only what changed.

**Governs**: which folders get a map, the map format, the root atlas, the
`last-mapped` marker, the refresh procedure, and the optional registration in
the project's agent instructions.

**Does not touch**: code, tests, docs, folder layout, module boundaries. The
map describes the project as it is; it never proposes restructuring (that is
`forever-clean` or an architecture skill, on request).

**Invariants**:
- Maps are created only after an explicit request; never as a side effect of
  another task.
- Every statement in a map is checked against the code it describes; no
  guessed flows, no marketing adjectives.
- One `codemap.md` per folder that has its own responsibility, following the
  project's module boundaries, not every directory.
- Each map is proportional to its folder. No line budget; no padding.
- Maps are additive. The skill never deletes or edits code or docs.

## Trust boundary

Existing READMEs, comments and docstrings are evidence to verify, not facts
to copy. When a comment and the code disagree, the map describes the code
and notes the stale comment.

## Phase 0 - Frame and scope

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
git rev-parse --short HEAD
ls; cat AGENTS.md CLAUDE.md 2>/dev/null | head -80
grep -rn 'last-mapped:' codemap.md 2>/dev/null
```

State once:
- `root: <path>` and `head: <sha>`.
- `mode: init | refresh` (refresh when a root `codemap.md` with
  `last-mapped:` exists).
- `scope:` source and config folders. Excluded by default: tests, docs,
  vendored dependencies, generated code, build output, lockfiles, fixtures,
  anything git-ignored. The user can include or exclude more; record it.
- `boundaries:` how the project defines a module (package, crate, app,
  bounded context, top-level folder with its own manifest). Read 2-3 sibling
  folders to confirm before choosing map locations.

Complete when: root, head, mode, scope and the list of folders that will get
a map are stated. For a tree with many candidate folders, show the list and
ask before writing (`prompt-default` Open Questions format).

## Phase 1 - Detect changes (refresh mode only)

```bash
LAST=$(grep -m1 'last-mapped:' codemap.md | awk '{print $2}')
git diff --name-only "$LAST"..HEAD -- <scope paths> | sed 's|/[^/]*$||' | sort -u
```

- Changed files map to the nearest folder that has a `codemap.md`; those
  maps are refreshed, the rest untouched.
- New folders inside scope without a map: candidates; ask before adding.
- Folders removed: their map is listed for the user to delete (see Safety);
  the atlas row is removed.
- `last-mapped` sha not found in history (rebase, shallow clone): fall back to
  init for the whole scope and say so.

## Phase 2 - Write folder maps

For each folder in the list, read the code (entry file, public surface, the
largest files, the tests that name behavior) and write `codemap.md` in that
folder:

```markdown
# <relative/path/>

## Responsibility
One paragraph: what this folder owns, in standard engineering terms (service layer, adapter, domain model, CLI entry, scheduler).

## Design
Patterns and abstractions actually used (repository, strategy, event bus, middleware chain); key types and interfaces; configuration it reads; invariants it enforces.

## Flow
How data and control enter and leave: ordered steps with function or type names, state transitions, error handling path.

## Integration
Consumed by: <modules, with the symbol they call>. Depends on: <modules, services, tables, queues>. Hooks, events, endpoints exposed.
```

- Name real symbols and files; a reader should be able to `grep` every noun.
- Large trees: split the folder list across sequential passes or a second
  agent per group of folders, each owning disjoint paths, each reporting
  anything it noticed outside its paths instead of editing it.
- Existing `codemap.md`: refresh in place with targeted edits; keep sections
  that are still true.

Complete when: every folder in the list has a map whose statements were
checked against the code.

## Phase 3 - Root atlas

Write or refresh `codemap.md` at the repository root:

```markdown
# Repository atlas: <name>
last-mapped: <sha>   scope: <paths>   excluded: <paths>

## Purpose
What the system does and for whom, one paragraph.

## Entry points
`<file>`: <what starts here>. (binaries, main modules, HTTP routers, CLI, scheduled jobs, build config)

## Directory map
| Directory | Responsibility | Map |
|---|---|---|
| `src/<a>/` | <one line from its Responsibility section> | [map](src/<a>/codemap.md) |

## Cross-cutting
Config loading, logging, auth, error handling, test layout: where each lives.
```

The atlas is the entry point for any agent or human; its table is derived
from the folder maps, never written independently.

## Phase 4 - Register (only with the user's agreement)

Propose adding to the project's canonical instruction file (`AGENTS.md`, or
`CLAUDE.md`/`.rules/` per the project's convention from `agents-md`) a short
section, idempotent (skip if a "Repository map" heading already exists):

```markdown
## Repository map
`codemap.md` at the root is the atlas: purpose, entry points, directory table.
Read it before a task that spans more than one module; for deep work in a
folder, read that folder's `codemap.md`. Refresh with the `codemap` skill when
`git diff --name-only $(grep -m1 last-mapped: codemap.md | awk '{print $2}')..HEAD` is not empty.
```

Keep it to those lines; the atlas carries the detail. If the instruction file
has a budget rule, this section competes for it like any other line.

## Phase 5 - Verify

- `grep -rn 'last-mapped:' codemap.md` shows the current head.
- Every map link in the atlas resolves (`ls` each path).
- Spot-check three statements per map against the code (`grep` the named
  symbols). A statement that does not resolve is fixed or removed.
- Maps are inside scope only; nothing was written in excluded folders.

## Report

```
mode: init | refresh · head: <sha> · last-mapped before: <sha | none>
scope: <paths> · excluded: <paths>
maps written: <n> (<list>) · refreshed: <n> · unchanged: <n> · candidates not mapped: <list or none>
atlas: codemap.md (<n> rows) · registered in: <AGENTS.md | CLAUDE.md | .rules/... | not registered (user declined | not asked)>
verification: links <ok|n broken> · spot checks <n ok / n fixed>
flags: <stale comments found, boundaries unclear, folders to remove maps from>
```

## Safety

- Writes only `codemap.md` files inside the stated scope and, with agreement,
  one section in the instruction file. Nothing else is created or edited.
- Never deletes code, docs or maps. A map for a folder that no longer exists
  is listed in the report for the user to remove (`git rm <path>` inside the
  repository root).
- Does not run project code or install dependencies; mapping is reading.
- Respects `.gitignore`d and user-excluded folders: no reading of secrets or
  local data for the map.
