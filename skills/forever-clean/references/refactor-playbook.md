# Refactor Playbook

Used by Phase 2 (new-secret test), Phase 4 (recipes) and Phase 6 (review
checklist) of `forever-clean`. Every recipe preserves external behavior.

## Tests

### New-secret test (Phase 2 - should this be a new file?)

A new file is justified only if the code encapsulates a genuinely new
**secret** (Parnas, 1972): a design decision, data format, algorithm or
external dependency likely to change independently of everything else in
the candidate owner file.

Not a new secret:
- "It is a different function" doing similar work to its neighbors.
- "The file is getting long" - a size signal, see the split recipe.
- "It is another step of the same pipeline" - steps of one process share a
  secret: the process itself.

Is a new secret:
- A different external system's integration details (payment provider A vs
  provider B).
- A different persistence mechanism or data shape.
- An algorithm swappable independently behind the same interface.

### Depth test (is a split worth a file?)

A **deep module** (Ousterhout) has a small public surface hiding substantial
implementation. A **shallow module** has a surface about as big as what it
hides and costs a file's worth of imports, indirection and retrieval for
near-zero abstraction value. Count exported names against body size; if
most of the file is exported and little is private, the split is shallow -
inline into the caller or pick a different seam.

### Net-neutral rule (does extraction reduce anything?)

```
lines_removed_from_source >= lines_added_to_new_file - glue_overhead
```

`glue_overhead` is roughly 10% of the new file (imports, exports, re-wiring
at call sites). Below that bar the move relocates bloat instead of reducing
it.

### Net-simplification test (does any move help?)

Applies to merges and splits alike. After the move the repository must have
fewer moving parts or clearer ownership: fewer files that change together,
fewer wrappers, fewer places to look for a concept, no file mixing
unrelated reasons to change. If the simplification cannot be named in one
sentence, do not make the move.

## Recipes

### Consolidate (sprawl)

1. List the files that share a secret: they change together, or one exists
   only to serve another.
2. Pick the owner: the file with the most direct name match and the
   clearest responsibility - not the smallest one.
3. Move code into the owner with targeted edits; keep public names stable
   or update every call site in the same step.
4. Delete the absorbed files (tracked: `git rm`, inside the repository
   root, listed first).
5. Check the result is not bloat: the owner still has one reason to change.

### Split (bloat, god-file)

1. List the distinct secrets mixed in the file - independent reasons to
   change, not visual sections.
2. Group functions/types by secret.
3. Extract the secret with the single clearest owner first - into an
   existing file when one fits, a new file only when none does.
4. Verify the net-neutral and depth tests. Repeat only while both still
   pass.

### Long function

1. Separate named sub-steps (candidates for private helpers) from the
   sequential mechanics of one secret (leave inline).
2. Extract only sub-steps with one clear purpose and a name that reads
   better than the inline code did.
3. Colocate helpers with the function; no new file unless the helper is
   reused elsewhere.

### Duplicated logic across 3+ sites (Rule of Three)

1. Confirm the duplicates share the same reason to change. Similar today
   but diverging tomorrow stays separate - a wrong abstraction costs more
   than duplication.
2. Extract to the closest existing common owner. No new `utils` file if any
   existing module can legitimately own it.

### Shallow wrapper

1. One caller: inline into it, delete the wrapper.
2. Several callers and no added behavior (no retries, adaptation, config):
   collapse into the callee and update every call site.
3. Keep it only when it genuinely hides complexity the callers should not
   see.

### Too many parameters

1. Bundle related parameters into one struct/object/record named for the
   concept they jointly represent.
2. Colocate the type with its primary owner.

### Hedge-named duplicate (`thing_v2`, `thing_new`, `thing_old`)

1. Diff the variants; identify which one is live (call sites, recent
   commits).
2. Fold the live behavior into the original name; update call sites.
3. Delete the dead variant. If both are referenced, stop and ask which
   wins.

## Phase 6 review checklist (touched files only, behavior preserved)

- [ ] Dead code, unused imports/exports, unreachable branches left by the
      change.
- [ ] Comments that narrate what the code already says, or now contradict
      it.
- [ ] Snippets the edit made redundant (two copies of the same guard,
      mapping or constant).
- [ ] Conditionals that simplify without changing outcomes (early returns,
      merged guards).
- [ ] Names that no longer match what the code does after the change -
      rename only inside the touched file unless the user asked for more.
- [ ] Error handling: nothing swallowed, no silent fallback introduced by
      the change; messages name the offending value and the expected shape.
- [ ] Compatibility shims added "temporarily" during the move and no longer
      needed.
- [ ] Comments that say why (workaround, constraint, issue, commit) are
      still there; the change itself left one wherever it introduced an
      odd line.
- [ ] Names an agent can grep: a touched name whose search hits are mostly
      unrelated gets a more specific one, inside the touched file only.
- [ ] Nesting the change deepened: guard clauses and early returns where
      the behavior is identical.

Anything outside this list, outside the touched files, or that could alter
behavior goes to `flags` in the report.

## Anti-patterns, both directions

Sprawl:

```
# BAD - new file for a 6-line function used exactly once
# utils/formatDateShort.ts
export function formatDateShort(d: Date) { ... }

# GOOD - colocated with its one caller until reused elsewhere
# invoice/renderInvoice.ts
function formatDateShort(d: Date) { ... }
```

```
# BAD - shallow wrapper, zero added behavior
# services/userServiceWrapper.py
def get_user(id): return user_repo.get_user(id)

# GOOD - callers use user_repo directly; wrapper deleted, call sites updated
```

```
# BAD - "extraction" that fails the net-neutral rule
# source file: -8 lines    new file: +45 lines (imports/types re-declared)
# net: +37 lines for the same behavior

# GOOD - the new file's 45 lines let the source drop 50+ redundant lines
```

Bloat:

```
# BAD - one file is the whole app: routes + SQL + email templates + cron
# app.py (2,800 lines, six reasons to change)

# GOOD - split by secret into the layout the project already uses
# app/routes.py  app/db.py  app/mail.py  app/jobs.py
```

```
# BAD - merging "to reduce file count" produced a bucket
# core.py = parser + HTTP client + CLI + config (changes for four reasons)

# GOOD - merge only files that share a secret (parser + its tokenizer)
```

```
# BAD - one 180-line function: validate, fetch, transform, persist, notify
# GOOD - five named steps, colocated helpers, same file, same behavior
```

```
# NOT bloat - a 1,400-line cohesive parser, or a generated schema file
# leave it; length alone is not a signal
```
