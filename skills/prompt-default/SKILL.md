---
name: prompt-default
description: Pre-execution prompt gate for any project and any AI. Screens the request before acting and raises grouped Open Questions only when readings would lead to materially different work or the action is drastic; otherwise states the assumption and proceeds. Use on every task before executing, and especially when the prompt names files, functions or routes that may not exist, mixes contradictory instructions ("delete it and update it"), uses vague verbs without a target ("improve", "fix it", "arruma isso"), asks to delete, rewrite, migrate or change the stack, conflicts with the project's own rules, or needs tools or access that are not available. Before the first edit of any change, states a four-line task brief (result, what must stay true, how to verify, what not to touch) that becomes the scope for the whole task. Also when the user says "valide meu pedido", "revise o prompt antes", "check this request", "is this task clear?", "define o escopo antes".
metadata:
  version: 2.1.0
  type: procedure
---

# Prompt Default - Pre-Execution Gate

Screens the user's request before any execution. Well-formed prompts pass
without questions. Flawed prompts get one grouped message of Open Questions
with evidence, options and defaults - never a trickle of questions, never a
silent guess on something that matters.

## Always-on installation

A skill loaded on demand cannot gate prompts it never sees. Put the short
block below in the layer the tool reads on every request, pointing back here
for the full procedure:

- Cursor: `.cursor/rules/NNN-prompt-gate.mdc` with `alwaysApply: true`
  (this repository ships `rules/002-prompt-gate.mdc`).
- Claude Code: a section in `CLAUDE.md`, or a `UserPromptSubmit` hook that
  injects the block.
- Codex, Gemini CLI, Copilot, Aider and others: a section in `AGENTS.md` or
  the tool's own instructions file.

Block (keep it under ~150 words):

```
Before executing any task, screen the request (full procedure: skill
`prompt-default`). Check: self-contradiction; missing target or criteria;
claims that do not match the project (one cheap lookup per named file,
function or stack); conflict with the project's own rules; tools, access or
credentials not available; drastic or irreversible scope. One obvious
reading: state the assumption in one line and proceed. Readings leading to
materially different work, or any drastic action: raise Open Questions in
one message with evidence, numbered options and a default per question,
and execute only what does not depend on the answer. At most two rounds.
Before the first edit of any change: state a task brief in four lines
(result, what must stay true, how to verify, what not to touch) and keep
it as the scope. No user present: safest reading with assumptions logged;
drastic actions never run. Well-formed prompt: no questions.
```

## Checks

Run all six, cheaply, in this order. Evidence for every failure is a quote
from the prompt or a fact from the project.

1. **Coherence** - the prompt contradicts itself: "delete the file and also
   update it", mutually exclusive goals, two incompatible outputs.
2. **Clarity** - target or criteria missing: which file/module/feature;
   vague verbs ("improve", "fix it", "clean this") with no acceptance
   criterion; unresolvable references ("change that"). Search before
   asking: a target becomes a question only when the search leaves two or
   more plausible candidates.
3. **Project match** - claims in the prompt versus the real state. For each
   named entity, one cheap lookup: file - glob; function/class/route -
   grep; dependency/stack - the manifest (`package.json`, `pyproject.toml`,
   `go.mod`, ...); described behavior - read the relevant function once.
   Cap the effort at a handful of lookups; verify the entities the task
   hinges on first. Record the closest match for every miss.
4. **Rules conflict** - the request asks for something the project's own
   rules forbid or already decide: `AGENTS.md`, `CLAUDE.md`,
   `.cursor/rules`, `CONTRIBUTING.md`, lint/format config. Quote the rule.
5. **Feasibility** - the task needs a tool, network, credential, permission
   or environment that is not available, or asks to bypass a security
   control. Ask before attempting; never simulate the result.
6. **Drastic scope** - the request implies any of:
   - irreversible operations: deleting data or files not recoverable from
     version control, history rewrite, force push, dropping tables or
     columns, touching production or shared resources, sending messages or
     publishing externally;
   - anything outside the working repository (see the Safety section of
     the `forever-clean` skill);
   - changing stack, framework or architecture; removing a feature;
     rewriting a module wholesale;
   - a footprint far wider than the request's stated area (a change
     crossing more than 3 directories is the signal).

   Drastic with clear intent gets one confirmation with an impact summary
   (what, how many files, reversible or not), not clarity questions.

**No codebase available** (chat without a workspace, prompt-only corporate
environment): skip checks 3 and 4, say so in one line, and carry the
prompt's claims as stated assumptions into the plan.

## Decide

| Situation | Action |
|---|---|
| All checks pass | Execute. No questions for a well-formed prompt. |
| Gap with one obvious reading, or readings whose difference is cheap to redo | State the assumption in one line (it becomes part of the plan) and execute. |
| Readings lead to materially different work | Open Questions. First execute everything that does not depend on the answer, then ask. |
| Check 6 fails | Confirm before any irreversible step. Never confirm on the user's behalf. |
| The prompt contradicts itself on the core action | Open Questions, nothing executed. |

Mid-execution: a fact that invalidates the prompt (the named file does not
exist after all, the described behavior is not what the code does) reopens
the gate at that point. Design decisions that merely surface during the
work follow the normal flow, not this gate.

## Task brief - before executing a change

A prompt that passes the gate still loses its constraints mid-task: the
agent drifts toward the easiest reading and touches what nobody asked for.
For any task that changes files, data or state, state this block once,
before the first edit, and repeat it in the final report:

```
Task brief
result:       <observable outcome; how a reader who did not do the work sees it is done>
keep true:    <invariants: behavior, public API, data, tests, files that must not change>
verify:       <exact commands or checks that prove the result; "none available" is stated, never implied>
do not touch: <files, modules, environments out of scope; default: everything not named in result>
```

- `result` is checkable by someone else. "Improve performance" is not a
  result; "p95 of `/search` under 300 ms in the project's benchmark" is.
- `verify` names the project's own commands first (test, lint, build,
  `.rules/check.sh` when `agents-md` is installed). None exists: say so
  and name the manual check.
- Every line comes from the prompt, the project's rules (`AGENTS.md`,
  `.rules/`) or the checks above. A line you cannot fill is an assumption
  (state it) or an Open Question; never an invention.
- The brief is the scope. Work that would leave `do not touch` reopens the
  gate at check 6. `forever-clean` Phase 0 and `verification-planning`
  build on this block instead of restating it.
- Pure questions, explanations and reviews without edits skip the brief.

## Open Questions - canonical format

```
## Open Questions
Request: <the user's prompt, summarized in one line>
Found:
- [coherence|clarity|project-mismatch|rules-conflict|feasibility|drastic] <issue>
  Evidence: <quote from the prompt and/or project fact, e.g. "file X does not exist; closest match is Y">
Questions:
1. <objective question> Options: (a) <found in the project> (b) <...> Default if unanswered: (a)
2. <objective question> ...
Done so far: <work executed that did not depend on the answers, or "nothing">
Awaiting answers.
```

Rules of conduct:
- Group all issues in one message - never one question at a time.
- Options come from the project ("did you mean `auth/login.ts` or
  `auth/session.ts`?"), lettered so a one-word reply is enough.
- Every question carries a default. Questions about drastic actions carry
  no default and never auto-proceed.
- Never "fix" the prompt silently by guessing intent on a failed check.
- At most two rounds. If the second answer is still ambiguous, proceed with
  the defaults as explicit assumptions for non-drastic items, and stop for
  drastic ones.
- After the answers, restate the corrected task in 1-2 lines and execute.
- Other skills that raise a question of their own (duplicate rule,
  conflicting convention) use this same block with the fitting tag.

## No user present

Scheduled runs, CI, batch jobs, autonomous loops - nobody will answer:
- Coherence and clarity failures: take the safest reading; log every
  assumption in the final report under `assumptions:`.
- Project mismatch: adapt to the real state when only one adaptation makes
  sense; otherwise stop and leave the Open Questions block as the output.
- Rules conflict and feasibility: stop. Do not work around.
- Drastic scope: never execute. Leave the Open Questions block as the
  output.

## Scope limits

- The gate screens the prompt, not the solution. It does not replace
  planning, code review or testing.
- Minor gaps are not a reason to block: trivia gets an assumption, not a
  question.
