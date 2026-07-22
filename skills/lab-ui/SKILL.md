---
name: lab-ui
description: Best-practices review for ipywidgets UI architecture in Databricks notebooks - thin notebooks over a facade, native-control allowlist, factory+chrome pattern, idempotent mount, state/render separation, sync-kernel performance (hold_sync, build-and-swap, event-loop debounce). Use when the user asks to review, refine, or extend notebook UI code following this architecture.
---

# Lab UI — Databricks ipywidgets Architecture Review

Code is WRITTEN in Cursor but only BEHAVES in Databricks. Every recommendation must
hold in the Databricks runtime (cluster kernel, restartPython, control allowlist).
Reject advice that is only valid in generic Jupyter/JupyterLab: no third-party widget
libraries (ipyvuetify, ipydatagrid...), no injected JavaScript / %%javascript, no
labextensions, no background threads updating widgets.

## Architectural doctrine (the 7 techniques)

1. **Thin notebooks / presentation layer**: notebook cells are a facade call, nothing
   else. No business logic, no widget wiring, no state manipulation in cells. Cells
   orchestrate: import, mount, done.
2. **Native-control allowlist**: only ipywidgets controls empirically verified to
   render in the cluster's runtime. The allowlist is data, not assumption — when a
   control is not on it, test in Databricks before adopting; never assume Jupyter
   parity.
3. **Factory + chrome**: controls are created by factories that centralize
   environment quirks (defaults, layout fixes, runtime workarounds); visual identity
   comes from a chrome/theme wrapper with SCOPED CSS (never global selectors that
   leak into the Databricks notebook UI).
4. **Idempotent mount**: `mount()` rebuilds the entire view from session state and
   yields the same result on every call. After `dbutils.library.restartPython()` all
   widget objects and display handles are dead — full remount is the only recovery
   path. No code may depend on a widget surviving between mounts.
5. **State/render separation (unidirectional-ish)**: observers/on_click handlers do
   exactly two things — mutate the persisted session dict, then call a public facade
   entry that re-renders. Handlers never touch other widgets directly, never hold
   business logic. Render reads state; events write state; nothing else crosses.
6. **Sync-kernel performance**:
   - `hold_sync()` to batch traitlet updates into one comm message;
   - build-and-swap: assemble new subtree off-screen, then swap it in with a single
     `container.children = (...)` assignment — never mutate a visible tree
     piece by piece;
   - debounce via the kernel's event loop (asyncio task/cancel pattern), never via
     threads or `time.sleep` in handlers.
7. **Orchestration facade**: the ONLY bridge between UI and calculation engines.
   Engines are pure, environment-agnostic functions (no widgets, no dbutils, no
   display). The facade also owns the live context/lineage: session snapshot of
   inputs/results and staleness detection (inputs changed → downstream results
   flagged stale, not silently reused).

## Combined-technique interactions (check explicitly)
- `hold_sync` + build-and-swap: hold_sync batches updates on a LIVE widget; for
  off-screen subtrees it is redundant — apply it to the visible container doing the
  swap, not the hidden build.
- Debounce + idempotent mount: pending debounced tasks must be cancelled on remount,
  or a stale callback will fire against dead widgets after restartPython.
- State separation + staleness: because handlers only write the session dict,
  staleness detection can live in one place (the facade) by hashing/comparing the
  snapshot — verify no handler bypasses it.

## When invoked
1. **Research**: check current best practices for each technique involved — isolated
   and combined — before judging the code. Prefer sources that address Databricks
   specifically; adapt generic-Jupyter guidance to the runtime's constraints.
2. **Triage the code** into three verdicts, each item justified:
   - **Adjust**: refine without changing current behavior.
   - **Replace**: substitute for an approach better aligned with the doctrine above.
   - **Remove**: redundant, obsolete, or principle-violating code.
3. **Preserve what works**: no refactor without a real gain in performance, clarity,
   or maintainability. Working code that follows the doctrine is left untouched.
4. **Performance first**: within the synchronous kernel, prefer the option with the
   fewest comm round-trips and reflows (batching, single swap, debounced handlers),
   always within environment limits (no third-party widgets, no injected JS, no
   thread-based updates).

## Decision rule (mandatory before any change)
For every Adjust/Replace/Remove item, state:
1. WHY — the researched best practice that motivates the change.
2. INTEGRITY — why the change cannot break current behavior (what stays identical,
   what was checked: mount idempotence, session-state compatibility, allowlist).
No justification, no change. If integrity cannot be assured, flag it as an open
question instead of applying.

## Final report
Table: item → verdict (adjust/replace/remove/keep) → justification → integrity check.
Then the diffs, smallest first.
