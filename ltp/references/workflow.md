# Workflow

Analysis proceeds in bounded stages, each consuming only the subgraph, evidence,
and unresolved diagnostics it needs -- not the whole repository re-sent to one
context. Every stage ends by running `ltp validate` and repairing what it flags.

## Operating modes

Decide which tools are warranted and record it in `analysis_plan`; a full analysis
does not manufacture every diagram.

| Mode | Builds | Use when |
| --- | --- | --- |
| `diagnose` | Goal Tree + Current Reality Tree | you need to understand why a system is stuck |
| `resolve-conflict` | Evaporating Cloud + Future Reality Tree | a chronic conflict blocks progress |
| `plan-change` | Future Reality Tree + Prerequisite/Transition Trees | the direction is set; you need a plan |
| `full` | all warranted views | a complete study |
| `reconcile` | model vs. plan vs. code | a roadmap exists to check |

Mark deferred trees `deferred` and skipped ones `skipped` with a reason. If no
persistent conflict exists, record `conflict_analysis` with rejected candidates.

## Forward mode: repository to plan

Work the stages in `SKILL.md` (inventory -> evidence -> goal candidates -> Goal
Tree -> scrutiny -> UDEs -> CRT -> CLR + predicted effects -> conflict detection
-> Cloud (if warranted) -> injection -> FRT + negative branches -> PRT ->
transition decomposition -> constraint assessment -> reconciliation -> `ltp sync`).

### Coverage

First enumerate and classify every file: source, tests, build/package config,
deployment/infra, docs, ADRs, API specs, DB schemas/migrations, UI text, CI/CD,
monitoring, TODOs/comments, issue/roadmap exports, generated files, vendor deps,
binaries, unknown. Inspect all analyzable, project-relevant files. Never claim
complete examination when files were omitted, unreadable, binary, generated, too
large, or inaccessible -- record those in `coverage_gaps`.

### Evidence priority (by claim kind)

Weight evidence differently depending on what the claim asserts:

| Claim | Stronger evidence |
| --- | --- |
| Current behavior | executable behavior, tests, runtime traces, implementation |
| Intended goal | user confirmation, strategy, charter, product docs |
| Necessary condition | stakeholder requirements, contracts, strategy, causal argument |
| Undesirable effect | operational failures, user impact, stakeholder testimony |
| Active conflict | policies, decisions, recurring behavior on both sides |
| Implementation obstacle | code contracts, dependency graph, tests, build config |

A test that contradicts a README is stronger evidence of *current behavior*. A
user-confirmed purpose outweighs naming conventions for *intended purpose*. The
global "tests before docs" order is right for behavior and wrong for ultimate
purpose -- choose by claim kind.

Every evidence packet should note supporting evidence, contradicting evidence,
coverage limits, and unsearched areas.

## Reverse mode: plan to logic

When the input is a TODO list, roadmap, or task set, treat each task as a candidate
`transition` action and infer the logic it must serve: its immediate effect, the
need behind it, the obstacle/IO it addresses, the desirable effect it creates, the
UDE it removes, the assumption it rests on, the NC it supports, and the goal it
ultimately serves. Then flag tasks that do not trace to the goal, duplicate one
another, have unstated effects, are ordered by habit rather than dependency, aim at
symptoms rather than causes, or are likely to create negative branches.

## Reconciliation mode

With both code and a plan, compare: what the code does; what the plan assumes it
does; what the plan intends to change; what the goal requires; what work is
underway but not goal-relevant; and what necessary work is absent from the plan.
Treat each discrepancy as evidence.

## Builder / critic discipline

Separate proposing meaning from scrutinizing it.

- A **builder** proposes entities and claims for one subgraph (e.g. the Goal Tree,
  or one root cause's CRT branch).
- A **critic** returns coded reservations against that subgraph -- e.g.
  `CLR-CAUSE-INSUFFICIENT` on a claim, or "this UDE reads as a missing feature".
  A critic does not silently rewrite the model.
- Run a small, bounded repair loop (two or three passes). Then **retain**
  unresolved reservations as recorded `open` CLR checks or `open_questions` --
  never fabricate plausible filler to clear a warning.

Give critics distinct lenses when a claim can fail in more than one way
(correctness, does-the-evidence-support-it, does-it-reproduce) rather than N
identical passes.

## Determining what to work on next

1. **Identify the constraint** -- what presently limits progress toward the goal
   (a bottleneck, a missing decision, a knowledge or validation gap, a recurring
   conflict, an unsatisfied prerequisite). Back it with a `constraint_assessment`.
2. **Locate the earliest blocked objective** -- the earliest unsatisfied IO on the
   path to an important injection.
3. **Prefer leverage over activity** -- work that removes a root cause behind
   several UDEs, breaks a core conflict, enables many downstream transitions, or
   yields decisive evidence about a major assumption. Not what is merely easy,
   visible, or already started.
4. **Resolve uncertainty economically** -- when two causal models remain
   plausible, pick the smallest safe action that distinguishes them.
5. **Recommend exactly one action** -- set `analysis.recommended_next_action` to a
   single transition, with its expected immediate effect and the uncertainty most
   likely to change the recommendation. The model may hold many transitions;
   `XTR-004` fails if the chosen one has no complete path to the goal.

## Incremental updates

On re-run: load the model, examine changed evidence, preserve stable ids where
meaning is unchanged, and mark invalidated conclusions (`review_status:
invalidated`) rather than deleting them. Treat implementation results as new
evidence; when an action produces an unexpected effect, re-examine the assumptions
and causal links, not just the transition.
