# Refactor Playbook

Used by Phase 4 of `forever-clean`, when Phase 3 flags a hard-limit breach.

## The new-secret test (governs Phase 2 create-or-edit gate)

A new file is justified only if the code encapsulates a genuinely new
**secret** (Parnas, 1972): a design decision, data format, algorithm, or
external dependency that is likely to change independently of everything
else in the candidate owner file.

Not a new secret:
- "It's a different function" doing a similar kind of work as neighbors in
  the same file.
- "The file is getting long" (that's a size signal, not a secret signal -
  see the god-file recipe instead).
- "It's a different step in the same pipeline" (steps of one process usually
  share a secret: the process itself).

Is a new secret:
- A different external system's integration details (e.g. payment provider
  A vs. provider B).
- A different persistence mechanism or data shape.
- A different algorithm swappable independently (e.g. two caching
  strategies behind the same interface).

## The depth test (governs whether a split is worth doing)

A **deep module** (Ousterhout) has a small public interface hiding
substantial implementation - high value per file. A **shallow module** has
an interface about as complex as what it hides - the file costs a full
retrieval/import/context slot for near-zero abstraction value.

Before finalizing any extraction, count:
- Public surface of the new file (exported functions/types/constants).
- Body size of the new file.

If the public surface is close to the whole body (most of the file is
exported, little private implementation), the split is shallow - prefer
inlining into the caller or picking a different seam.

## The net-neutral rule (governs whether extraction is a real reduction)

Extracting code into a new file only counts as a reduction if:

```
lines_removed_from_source >= lines_added_to_new_file - glue_overhead
```

where `glue_overhead` is roughly 10% of the new file (imports, exports,
re-wiring at call sites). If a proposed extraction doesn't clear this bar,
it's moving bloat, not reducing it - reconsider the seam.

## Recipe: God-file (many unrelated responsibilities)

1. List the distinct secrets currently mixed in the file - actual
   independent reasons to change, not visual "sections".
2. Group functions/types by secret.
3. Extract the secret with the single clearest owner first.
4. Verify net-neutral and depth tests on the result.
5. Repeat only if more secrets remain and each extraction still passes both
   tests.

## Recipe: Long function

1. Identify named sub-steps (candidates for private helpers) vs. sequential
   mechanics of one secret (leave inline - don't extract just to shorten).
2. Extract only sub-steps with one clear purpose and a name that reads
   better than the inline code did.
3. Do not create a new file for this - colocate helpers with the function
   unless the helper is independently reused elsewhere.

## Recipe: Duplicated logic across 3+ sites (Rule of Three)

1. Confirm the duplicates share the same *reason to change*. If they look
   similar today but would diverge for different reasons tomorrow, keep
   them separate - a wrong abstraction costs more than duplication (Sandi
   Metz).
2. If they do share a reason to change, extract to the closest existing
   common owner. Avoid creating a new top-level `utils`/`helpers` file if
   any existing module can legitimately own it.

## Recipe: Shallow wrapper (file exists only to forward calls)

1. If there's exactly one caller, inline the wrapper into it and delete the
   file.
2. If there are multiple callers but the wrapper adds no real behavior
   (no retries, no adaptation, no config), collapse into the callee and
   update every call site.
3. Keep the wrapper only if it genuinely hides complexity the callers
   shouldn't see.

## Recipe: Too many parameters

1. Bundle related parameters into one struct/object/record named for the
   concept they jointly represent.
2. Colocate the new type with its primary owner - don't spin up a new file
   for it unless it's reused across multiple modules.

## Anti-pattern examples

```
# BAD - new file for a 6-line function used exactly once
# utils/formatDateShort.ts
export function formatDateShort(d: Date) { ... }

# GOOD - colocate with its one caller until reused elsewhere
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
# source file: -8 lines
# new file: +45 lines (mostly imports/types re-declared)
# net: +37 lines for the same behavior - not a real reduction

# GOOD - extraction where the new file's 45 lines let the source
# drop 50+ lines of now-redundant logic - net negative, worth doing
```
