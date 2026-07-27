# Context Map Reference

Used by Phase 1 (locate the concept) of `forever-clean`, and by the project
rule `010-file-lifecycle-policy.mdc` if loaded.

## Why a repo index pays for itself

Every file the agent must open to re-derive "where does X live" is a fixed
retrieval cost paid every session. A one-page index that maps directories to
the concept they own turns that into a single lookup instead of a grep
sweep or, worse, a guess that leads to creating a duplicate.

## Building/maintaining the index

If the project has no architecture doc yet, create exactly **one**:
`ARCHITECTURE.md` or `docs/index.md` at the repo root. Structure:

```markdown
# Architecture Index

## Modules
| Directory | Owns |
|---|---|
| src/auth | session/token issuance and validation |
| src/billing | invoicing and payment provider adapters |
| src/api | HTTP route definitions, request/response mapping only |

## Glossary
- **Tenant**: an isolated customer workspace, not a database row alias for "user"
- **Adapter**: provider-specific implementation behind a shared interface in billing
```

Update rule: when a module's responsibility changes, edit its row in place.
Never append a dated changelog entry to this file - that's a different
concern (git history already is the changelog) and turns the index itself
into a bloat target.

## Search protocol (Phase 1 of forever-clean)

1. Check the index first if one exists - it's cheaper than grepping blind.
2. If no index, or the index doesn't resolve it, search the concept under
   at least 3 name variations: singular/plural, common synonym, and any
   domain abbreviation used in the codebase (check the glossary).
3. Prefer the file with the most direct name match over the file with the
   most convenient current size - "this file is smaller so I'll put it
   there" is not a valid reason to misplace a concept.

## Context radius heuristic

Count the number of distinct directories a change touches (excluding
frozen zones). If a task crosses more than 3, treat that as a signal before
proceeding, not after:

- The task may be under-scoped (doing more than what was asked).
- Or the module boundaries are wrong (the concept is split across
  directories that should be one owner, or one directory owns too much).

State this explicitly - "this change touches N directories, which suggests
<reason> - proceeding as scoped" or "...suggests the boundary in <dir> is
off, flagging before continuing" - rather than silently pushing a wide-radius
change through.
