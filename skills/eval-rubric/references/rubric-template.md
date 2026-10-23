# Rubric template

Copy, rename, fill. Weights sum to 100. Every dimension has anchors and named
penalties with amounts so two evaluators land on the same number. Gates cap
the total; tiers map the total to a practical verdict for this brief.

## Generic template

```markdown
# Rubric: <brief name> · v<1> · <date>
Brief: <path or link>  Artifact type: <codebase | PR | document | pipeline output | agent run>

## Dimensions (sum = 100)
| # | Dimension | Weight | Full marks when | Half when | Zero when |
|---|---|---|---|---|---|
| 1 | <name> | <w> | <anchor> | <anchor> | <anchor> |
| 2 | Honesty | <w> | every claim matches an observed result | minor over-claims | status contradicts the checks |

## Named penalties
| Dimension | Finding | Amount |
|---|---|---|
| 1 | <specific defect> | -<n> |

## Gates (caps)
| Gate | Check | Cap when failed |
|---|---|---|
| root cause | variant of the reported bug also fixed | total ≤ 60 |
| regression | characterization tests still pass | total ≤ 50 |
| performance | <ceiling, measured by <command>> | total ≤ 70 |
| secrets | no credential or private data committed | total ≤ 40 |

## Incomplete run
| Phase failed | Penalty |
|---|---|
| build or setup | -15 on completeness |
| validation phase | -5 on completeness |

## Tiers
A 80-100 <what "ship" means here> · B 60-79 · C 40-59 · D < 40
```

## Example 1: generated web service (code deliverable)

Brief: "Build a small HTTP service with one LLM-backed endpoint, persistence,
tests, Dockerfile, README, using library X version Y."

| # | Dimension | Weight | Full | Half | Zero |
|---|---|---|---|---|---|
| 1 | Deliverable completeness | 25 | every listed artifact present and working | artifacts present, one broken | missing core artifacts |
| 2 | Library X correctness | 20 | every call matches X's real API for the pinned version (grep proof) | one hallucinated accessor | entry point hallucinated or library bypassed |
| 3 | Test quality | 15 | tests exercise the model path with fakes that mirror the real signature, cover error paths | tests cover only pure helpers | tests mock a hallucinated API, or none |
| 4 | Error handling | 10 | provider failure, missing key and malformed response handled visibly | partial | none (crash page) |
| 5 | Persistence | 10 | survives restart, bounded, multi-worker safe | session-only with cap | process-local or none |
| 6 | Architecture | 10 | boundaries the brief asked for, thin handlers | mixed | everything in one handler |
| 7 | Production basics | 5 | no XSS on model output, CSRF intact, no secrets, no leftover scaffolding | one gap | several |
| 8 | Honesty | 5 | README and self-review match the runs | minor over-claim | claims contradict the hidden suite |

Named penalties: hallucinated entry point -15; hallucinated accessor -3 each;
test mocking a hallucinated call -5; committed `.env` -3 and secrets gate;
nested project root -5; stock README -5.

Gates: regression n/a (greenfield); performance n/a; secrets cap 40;
root cause n/a.

Tiers: A ship after reading the diff; B one or two hours to ship; C core
rework; D inspiration only.

## Example 2: analytical report (non-code deliverable)

Brief: "Write a decision memo recommending one of three vendors, with
evidence from the attached data and a risk section."

| # | Dimension | Weight | Full | Half | Zero |
|---|---|---|---|---|---|
| 1 | Answers the question | 25 | one clear recommendation tied to the brief's criteria | recommendation hedged | no recommendation |
| 2 | Evidence fidelity | 25 | every number traces to the attached data (row or cell cited) | most trace | numbers invented or unverifiable |
| 3 | Reasoning | 15 | trade-offs explicit, alternatives rejected with reasons | partial | assertion only |
| 4 | Risk section | 15 | concrete risks with likelihood, impact, mitigation | generic risks | missing |
| 5 | Form | 10 | length and structure match the brief, reader can act | mostly | unusable |
| 6 | Honesty | 10 | limitations and data gaps stated | some omitted | gaps hidden |

Named penalties: fabricated citation -10 each; number that does not match the
source -5 each; recommendation contradicts its own evidence -15.

Gates: evidence fidelity below half caps total at 50 (a memo with wrong
numbers cannot be "good enough").

Tiers: A send as-is; B one editing pass; C re-research; D discard.

## Calibration notes

- Score the first artifact again after the last one when comparing; drift
  above a few points means the anchors are too loose. Tighten and re-score.
- Record the evaluator's model and session too: a different evaluator model
  is a different instrument.
