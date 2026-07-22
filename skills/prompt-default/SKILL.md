---
name: prompt-default
description: Pre-execution prompt check. Use when the user writes a task or requests work whose prompt is incoherent, ambiguous, conflicts with the project's actual state, or implies drastic changes. Identifies the problems BEFORE executing and raises Open Questions so the user can redirect the prompt.
---

# Prompt Default — Pre-Execution Gate

Before executing a task, screen the user's prompt against the checks below.
If any check fails, DO NOT execute. Raise Open Questions first.
If all checks pass, proceed normally — do not ask questions for well-formed prompts.

## Checks

1. **Internal coherence**: the prompt contradicts itself (e.g. "delete the file and
   also update it", conflicting requirements, mutually exclusive goals).
2. **Clarity**: essential information is missing or ambiguous — undefined target
   (which file/module/feature?), vague verbs ("improve", "fix it") with no criteria,
   unresolvable pronoun references ("change that").
3. **Project consistency**: claims in the prompt do not match the project's actual
   state. Verify before executing: mentioned files/functions/routes exist? named
   stack/framework matches the codebase? described behavior matches the real code?
4. **Drastic changes**: the request implies deleting or rewriting large parts of the
   project, changing architecture/stack, removing features, touching many files, or
   irreversible operations — confirm intent and scope before acting.

## On failure — Open Questions format

```
## Open Questions — prompt needs direction before execution
Request: <the user's prompt, summarized>
Issues found:
- [coherence|clarity|project-mismatch|drastic-change] <what was identified>
  Evidence: <quote from prompt and/or project fact, e.g. "file X does not exist; closest match is Y">
Questions:
1. <objective question offering options when possible>
2. <objective question>
Nothing was executed. Awaiting answers to proceed.
```

Rules of conduct:
- Group ALL issues in one message — never drip one question at a time.
- Offer concrete options discovered in the project (e.g. "did you mean `auth/login.ts`
  or `auth/session.ts`?") instead of open-ended "what do you mean?".
- Never "fix" the prompt silently by guessing intent on a failed check.
- After the user answers, restate the corrected task in 1-2 lines and execute.

## Scope limits
- Minor gaps with one obvious reading: state the assumption in one line and proceed —
  do not block on trivia.
- This gate screens the prompt, not the solution: design decisions that surface
  mid-execution follow the normal flow, not this skill.
