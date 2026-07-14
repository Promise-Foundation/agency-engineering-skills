# Logical scrutiny

The engine never decides whether a cause is real. It checks that the Categories of
Legitimate Reservation (CLR) were **applied** and that their conclusions are
**represented honestly**. This is the difference between a diagram of someone's
perception and a logical tool.

## The eight CLR checks

Each important sufficiency claim carries a `clr` block. Every check has a
`result` from: `not_applicable | untested | open | pass | fail`, and may carry
`evidence_refs`, a `reservation`, or a `proposed_additional_premise`.

```yaml
causal_claims:
  - id: CLM-17
    premises: [RC-1, AC-3]
    operator: all
    conclusion: UDE-4
    clr:
      clarity: {result: pass}
      entity_existence: {result: pass, evidence_refs: [EVD-4, EVD-9]}
      causality_existence:
        result: open
        reservation: "evidence establishes correlation but not causation yet"
      cause_insufficiency:
        result: fail
        proposed_additional_premise: AC-3
      additional_cause: {result: open}
      cause_effect_reversal: {result: pass}
      predicted_effect_existence: {result: untested}
      tautology: {result: pass}
```

What each check asks:

- **clarity** -- is the statement unambiguous?
- **entity_existence** -- do the named cause and effect actually exist? (needs
  evidence)
- **causality_existence** -- is there a causal mechanism, not mere correlation or
  sequence?
- **cause_insufficiency** -- is the stated cause enough on its own, or is another
  premise required? A `fail` names the missing premise.
- **additional_cause** -- is there another independent cause also producing the
  effect?
- **cause_effect_reversal** -- are cause and effect the right way round?
- **predicted_effect_existence** -- does a predicted consequence actually appear?
- **tautology** -- does the "cause" merely restate the effect?

## Logical status is derived, not asserted

From the CLR block the engine derives a claim's standing (shown in the dashboard):

- **candidate** -- no CLR review yet, or one or more checks are `open`.
- **scrutinized** -- every applicable check `pass`es.
- **contradicted** -- a required check (`causality_existence`, `cause_effect_reversal`,
  or `tautology`) is `fail`.

A `cause_insufficiency` or `additional_cause` `fail` raises **CRT-006** ("may
require an additional premise") -- the claim is not wrong, it is incomplete. Never
mark a claim `scrutinized` by editing a status; make the checks pass.

## Sufficiency vs. necessity

Two different logics, two different structures. Do not mix them.

- **Sufficiency** (Reality Trees): "IF these causes exist, THEN the effect
  follows." Compound sufficiency (`operator: all`) means *all* the contributing
  causes together deliver the effect -- one AND gate.
- **Necessity** (Goal Tree, Cloud, Prerequisite order): "to have the parent, the
  child MUST exist." A necessity claim does not assert the child is sufficient.

Reservoir of common confusions to avoid: sequence is not causality; correlation is
not causality; an implementation detail is not an objective; the absence of a
feature is not an undesirable effect; a proposed action is not its expected result;
a symptom is not a root cause.

## Predicted effects

A root cause you cannot test is a guess. For each root-cause candidate, state at
least one nontrivial predicted effect -- something that *should* (or should not)
appear in the repository or its behavior if the cause is active -- and record
whether it was observed. An expected-but-absent effect (**PRED-002**) should
reduce or invalidate confidence in the explanation; a root cause with no predicted
effect at all raises **PRED-001**. Waive only with an explicit reason.

## Root cause vs. constraint

A **root cause** explains undesirable effects. A **constraint** limits throughput
toward the goal. They can coincide, but that must be *demonstrated*, not assumed:

`analysis.current_constraint` must reference a `constraint`-kind entity backed by a
`constraint_assessment` that states a goal/progress measure, a limiting-mechanism
argument, rejected alternative constraints, and a Five Focusing Steps posture.
Pointing `current_constraint` at a `root_cause` without that demonstration raises
**CON-006**; without a limiting-mechanism argument at all, **CON-002**.

Do not accept "we have finite time/resources" as a conflict or a constraint unless
the contention is specific, persistent, and consequential (**EC-009**).

## Publication

`ltp validate` returns diagnostics at three severities:

- **error** -- blocks publication. `ltp sync` refuses (without `--force`).
- **warning** -- the standing scrutiny backlog; a mature model works it down.
- **info** -- conventions and notes.

A model is **publishable** when it has zero errors. That is the honest bar: the
logic holds together structurally and every claim's review is represented as it
actually stands -- with open reservations left open, not papered over.

See `references/diagnostics.md` for the full code catalog.
