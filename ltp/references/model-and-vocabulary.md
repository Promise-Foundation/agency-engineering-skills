# The typed model and its vocabulary

One file is authored: `ltp/ltp-model.yaml`. It parses into closed, typed records.
A value outside a vocabulary, a missing required field, an unknown field, or a
duplicate id is a **structural error** with a precise location -- caught before
any logical check runs. The authoritative shape is
`references/ltp-model.schema.json` (generated from the Python types); this file is
the readable companion.

## Top-level shape

```yaml
schema_version: 3
project: {name, analyzed_path?, analysis_mode?, provisional_goal?, goal?}
analysis: {current_constraint?, recommended_next_action?, expected_effect?, updated_at?}
analysis_plan: {mode?, goal_tree, current_reality_tree, ...}   # per-view {status, reason?}
entities: [ ... ]
evidence: [ ... ]
necessity_claims: [ ... ]
causal_claims: [ ... ]
clouds: [ ... ]
conflict_claims: [ ... ]
conflict_analysis: {status, candidates_rejected: [...]}        # when no cloud is warranted
predicted_effects: [ ... ]
obstacle_resolutions: [ ... ]
transitions: [ ... ]
constraint_assessment: { ... }
open_questions: [...]
contradictions: [...]
coverage_gaps: [...]
# NB: there is no `views` and no `links`. Views are derived; relationships are typed claims.
```

## Entities

Every node is an entity with a **kind** from a closed set:

```
goal  critical_success_factor  necessary_condition
undesirable_effect  cause  root_cause  constraint
cloud_objective  cloud_need  cloud_action
injection  desirable_effect  negative_branch  trimming_injection
obstacle  intermediate_objective
existing_reality  need  transition_action  immediate_effect
assumption  risk
```

**Assumptions are entities** (`kind: assumption`) with stable ids, referenced by
claims via `assumption_refs`. Do not bury important assumptions in prose.

```yaml
entities:
  - id: RC-1                     # id prefix should match the kind (RC for root_cause)
    kind: root_cause
    statement: Findings arrive as isolated claims instead of accumulating
    basis: inferred              # observed | inferred | provisional   -- where it came from
    review_status: unreviewed    # unreviewed | corroborated | user_confirmed | disputed | invalidated | superseded
    confidence: high             # high | medium | low
    satisfaction: unknown        # unknown | satisfied | partial | unsatisfied | not_applicable (for conditions)
    influence: influence         # control | influence | monitor | outside
    evidence_refs: [EVD-3]
    assumption_refs: [ASM-2]
    reasoning: >
      Without stable addresses, scope limits detach from the claim they qualify.
```

### The four status dimensions

The old single `status` conflated origin with review outcome. v2 keeps them
apart:

- **`basis`** -- how the statement entered the model. `observed` (direct evidence),
  `inferred` (reasonable interpretation), `provisional` (needed to proceed, weakly
  supported).
- **`review_status`** -- what scrutiny concluded. `user_confirmed` means the user
  confirmed it is their stated belief or intention; it does **not** prove a causal
  connection.
- **`confidence`** -- strength, independent of origin and review.
- **`satisfaction`** -- for Goal-Tree/Prerequisite conditions, whether the
  condition currently holds.

**`influence`** (control | influence | monitor | outside) is separate again: a
necessary condition outside the project's control is kept in the tree and marked
`monitor`/`outside`, not deleted.

Goal-Tree leaves also carry `satisfaction_criterion` (how you would observe the
condition holds) and may be `atomic: true` with an `atomic_justification`.

### Necessary-condition ownership

A `necessary_condition` is an LTP node asserting that a condition must hold for
an objective to be achieved. Its meaning is fixed by a `necessity_claim` whose
`prerequisite` is the condition and whose `objective` is the goal, critical
success factor, or intermediate objective it constrains. LTP owns this entity,
the claim, satisfaction, influence, evidence, assumptions, and logical scrutiny.

Promisify may project the **type** `necessary_condition` to an inherited domain
and assess a concrete node such as `NC-17` as a subject. That projection does not
turn a promise into a necessary condition, duplicate `NC-17`, or transfer LTP's
logical authority to Promisify.

## Typed claims (there are no generic edges)

### Necessity

```yaml
necessity_claims:
  - id: NEC-2
    prerequisite: NC-1     # to achieve `objective`, `prerequisite` must exist
    objective: CSF-1
    assumption_refs: [ASM-1]
```

Used by the Goal Tree, Prerequisite ordering, and the four arrows of a Cloud.

### Sufficiency

```yaml
causal_claims:
  - id: CLM-1
    premises: [RC-1, AC-1]   # the causes
    operator: all            # single | all | any | exclusive_any | magnitudinal
    conclusion: UDE-1        # the effect
    assumption_refs: [ASM-1]
    confidence: medium
    clr: { ... }             # the CLR review (see references/logical-scrutiny.md)
    verification: {hypothesis_ref: HYP-X, role: causal_outcome}   # optional hypothesize link
```

`operator: all` means the premises **together** cause the effect -- rendered as a
single AND gate. Never split a joint cause into two arrows that each imply
independent sufficiency. Use `any`/`exclusive_any` for alternatives, `magnitudinal`
for causes that accumulate in magnitude, `single` for one premise.

## First-class structures

### Evaporating Cloud

```yaml
clouds:
  - id: EC-1
    status: validated_persistent_conflict   # candidate | validated_persistent_conflict | rejected
    objective: A-1            # kind cloud_objective
    need_b: B-1               # kind cloud_need
    need_c: C-1
    action_d: D-1             # kind cloud_action
    action_d_prime: DP-1
    necessity_claims: {a_requires_b: NEC-11, a_requires_c: NEC-12,
                       b_requires_d: NEC-13, c_requires_d_prime: NEC-14}
    conflict_claim: CON-1     # the explicit D <-> D' incompatibility
    persistence_evidence: [EVD-80]
    injection_refs: [INJ-1]
conflict_claims:
  - id: CON-1
    statement: D and D' cannot both be fully performed
    assumption_refs: [ASM-9]
    evidence_refs: [EVD-81]
```

When no persistent conflict is warranted, record `conflict_analysis` instead --
do not force a Cloud.

### Predicted effects

```yaml
predicted_effects:
  - id: PRED-3
    source_claim: CLM-17
    statement: Runs lacking real learned arms recur across reports
    expectation: should_exist        # should_exist | should_not_exist
    result: observed                 # untested | observed | absent | mixed
    evidence_refs: [EVD-54]
```

A root-cause candidate needs at least one predicted effect (or an explicit waiver
with a reason). An expected effect recorded `absent` weakens the explanation.

### Prerequisite Tree and Transition Tree

```yaml
obstacle_resolutions:
  - {id: OR-1, obstacle: OBS-1, intermediate_objective: IO-1}
transitions:
  - id: TR-1
    existing_reality: ER-1
    need: NEED-1
    action: ACT-1              # kind transition_action
    immediate_effect: IE-1     # required: the observable effect the action produces at once
    advances: IO-2             # the intermediate objective it advances (not the whole injection)
    precondition_refs: [IO-1]
    verification: {kind: automated_test, command: "pytest ...", acceptance: "..."}
    likely_scope: [src/foo.py, tests/test_foo.py]
    estimated_size: small
    risk_refs: [RISK-1]
    rollback: "keep the feature flag off"
```

### Constraint assessment

```yaml
constraint_assessment:
  entity: CONSTRAINT-1
  status: candidate
  goal_measure: {name: Qualified comparisons, unit: comparisons, period: month}
  limiting_mechanism: "No realistic learned arm can enter the sealed comparison"
  evidence_refs: [EVD-101]
  alternative_candidates: [{entity: CONSTRAINT-2, rejected_because: "..."}]
  focusing_step: {current: exploit}     # identify | exploit | subordinate | elevate | inertia
  exploit_direction: "..."
```

`analysis.current_constraint` must reference a `constraint` entity backed by this
assessment. A root cause can also be the constraint, but only when demonstrated
(see `references/logical-scrutiny.md`).

## Views are derived

There is no `views` block to author. Each of the six views is computed from entity
kinds and claims by the renderer and the dashboard, so a condition lives in one
place and every view stays consistent with it automatically.
