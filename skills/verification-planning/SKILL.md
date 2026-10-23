---
name: verification-planning
description: Builds an evidence path before non-trivial implementation, for any project and any AI. States the claim the change must make true, derives from the system itself how that claim can be established, limited or refuted, sets a verification budget, adds the smallest verification affordance only when the decisive truth is too indirect, and closes the path after implementation with established / limited / refuted. Use before a feature, bug fix, refactor, migration, cross-system change or any behavior change the user must be able to trust; when asked "how will we know this works?", "plan the verification", "what is the evidence?", "prove it", "como vamos testar isso?", "como provar que funcionou?", "planeja a verificação", "qual a evidência?". Not for small mechanical changes already covered by the project's ordinary checks, and not a replacement for the post-change gate (tests, lint, `git diff --stat`) that `agents-md` and `forever-clean` already require.
metadata:
  version: 1.0.0
  type: procedure
  source: "adapted from akitaonrails/my-skills verification-planning (Fabio Akita, 2026), generalized for any project and any AI"
---

# Verification Planning - the evidence path

"Tests pass" is not evidence that a change did what was asked; it is evidence
that whatever the tests check still holds. Before changing a non-trivial
system, decide how this system can reveal the truth of this particular change.
That route, from claim to evidence, is the evidence path. It is written before
implementation, followed during it, and closed after it.

**Governs**: the claim, the evidence path, the verification budget, any
temporary affordance built to observe the system, and the closing verdict.

**Does not touch**: the implementation itself, the project's test framework or
coverage targets, the shape of the codebase. It adds no dependency, flag or
diagnostic surface without asking.

**Invariants**:
- The path is derived from this system, not from a familiar technique.
- Every distinct claim has one owner and one piece of decisive evidence.
- Evidence is reused only while its inputs, environment and state are proven
  unchanged.
- The closing verdict distinguishes known facts from remaining uncertainty.

## Phase 0 - Decide whether this skill applies

Apply it when the change crosses a boundary (module, service, persistence,
network, platform), alters behavior users or other systems depend on, fixes a
bug whose cause is not yet proven, or will be hard to reverse. Skip it for a
mechanical change the project's ordinary checks already cover; say so in one
line and proceed. `prompt-default` screens the request; this skill screens
the proof. Scope rule: never widen the task to make it more verifiable.

## Phase 1 - Frame the claim

State, in plain sentences:
- what must become true (observable behavior, not code shape);
- what must remain true (adjacent behavior, contracts, data, performance);
- where the change crosses a boundary and who is on the other side;
- the failure that would matter most if the conclusion were wrong.

Write the conditions that could make a confident conclusion false: a hidden
code path, a cached result, a platform difference, a test double that lies.

**Complete when**: claim, meaningful uncertainty and worst failure mode are
concrete enough to investigate.

## Phase 2 - Design the evidence path

Derive candidate paths from the system itself: its controllable inputs,
observable effects (outputs, logs, state, metrics, files), invariants, state
transitions, artifacts, and its ability to repeat or reverse a scenario.

Generate at least two alternatives before choosing, for example:
- a unit or integration test that fails on the current code and passes after;
- a replay of a recorded real input against before and after;
- an invariant check over existing data (count, hash, sum, schema);
- an end-to-end run against a disposable environment with synthetic data;
- a manual observation with a stated procedure, when nothing else is viable.

Prefer the path that gives a trustworthy conclusion with proportionate cost,
safety and effort. Record its limitations and keep a weaker and a stronger
alternative in reserve.

**Complete when**: one preferred path, its blind spots, and the alternatives
are written down.

## Phase 3 - Set the verification budget

List the distinct claims (usually two to five). For each, assign one owner and
choose the minimum non-duplicative evidence that covers the claim and its
important boundary. Required repository and release checks still apply on top.

Reuse rules:
- Reuse a prior green result only when the relevant code, inputs, toolchain,
  environment and state are byte-identical or proven equivalent, and say which
  run supplied it.
- A change to build scripts, manifests, fixtures, migrations, workflows or
  generated inputs invalidates reuse even when the prose diff looks harmless.
- Broaden or repeat verification only when a stated condition justifies it,
  never as ritual.

**Complete when**: a short table of claim, evidence, owner exists and nothing
in it is duplicated.

## Phase 4 - Add a verification affordance only when needed

When the existing system leaves the decisive truth too indirect (the effect
is buried in a log, the state is not inspectable, the scenario cannot be
repeated from a known start), extend the path with the smallest capability
that makes the relevant state controllable, observable, repeatable and
diagnosable: a seed or fixture, a debug endpoint behind a flag, a structured
log line, a dry-run mode, an injectable clock or fake.

Decide its lifecycle before building it: temporary (removed in the closing
phase) or durable (kept as a project asset, documented). Ask before adding a
dependency, a persistent diagnostic surface or a structural change whose only
purpose is evidence gathering. Treat the affordance as part of the evidence
path, not as a product feature that slipped in.

**Complete when**: the path can establish the claim directly enough for its
stakes, and any affordance has a stated lifecycle.

## Phase 5 - Research when the path is unknown

When the right path depends on an unfamiliar dependency, framework, external
service or fast-moving capability, look for official or project-specific
facilities first: the dependency's own test helpers, documented debug modes,
the project's existing fixtures and `AGENTS.md` commands. A second agent or a
fresh session may do this focused research so the planning context stays
small; hand it the exact question, not the whole task. Use existing project
evidence directly when it already settles the choice.

**Complete when**: the chosen path rests on known capabilities and real
constraints, not on assumption.

## Phase 6 - Make the path runnable

Prepare only the support needed to follow the path reliably: the command, the
data, the environment, the expected signal. Keep it narrow, repeatable and
safe to inspect. Write the exact commands and the line of output that counts
as pass. Decide whether each piece of support has recurring value or exists
only for this uncertainty; mark the temporary pieces for removal.

**Complete when**: another agent could follow the path without guessing about
setup, state or interpretation.

## Phase 7 - Close the evidence path

After implementation, follow the planned path exactly. Interpret the result
against the original claim and report one of:
- **established**: the evidence supports the claim within the stated scope;
- **limited**: the claim holds for the cases exercised; name what was not;
- **refuted**: the evidence contradicts the claim; implementation returns to
  the implementer with the failing evidence attached.

Quote the decisive output line for every claim. Remove temporary affordances;
document durable ones. Record a surprise that changed the plan in
`.rules/decisoes.md` or `.rules/erros.md` when the project uses `agents-md`.

**Complete when**: a future reader can see what supports the conclusion and
what remains outside its reach.

## Output - Evidence path block

Produced at the end of Phase 6 and handed to whoever implements:

```
## Evidence path
claim: <what must become true>
must stay true: <adjacent behavior, contracts, data>
worst failure: <what matters most if wrong>
path: <chosen route - inputs, observation, repeatability>
alternatives: <weaker / stronger, when to switch>
budget:
- <claim 1> - <evidence> - <owner>
- <claim 2> - <evidence> - <owner>
affordance: <none | temporary: what, removed in close | durable: what, documented where>
run: <exact commands; the output line that counts as pass>
reuse: <prior runs reused and why they still apply, or "none">
```

## Report

Produced at the end of Phase 7:

```
## Verification result
verdict: established | limited | refuted
evidence:
- <claim> - <command / observation> - <decisive output line>
not covered: <cases, platforms or boundaries outside the path>
affordances: <removed | kept and documented at <path>>
surprises: <what changed the plan, recorded where>
```

## Scope limits

- Proportionate: a one-line fix with an existing failing test needs the
  Phase 7 report only.
- For multi-phase work, this skill sets the path once; later phases follow it
  and extend it only when a new claim appears.
- The path never substitutes for the project's own gate; it tells you what
  the gate cannot.
