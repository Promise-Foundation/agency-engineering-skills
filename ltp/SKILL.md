---
name: ltp
description: >
  Reconstruct the logic implicit in a software project as one evidence-backed,
  logically validated Theory-of-Constraints model, and enforce its validity with
  the deterministic `ltp` CLI. Use whenever the user wants a Goal Tree, Current
  or Future Reality Tree, Evaporating Cloud, Prerequisite Tree, Transition Tree,
  a system-constraint diagnosis, causal or root-cause analysis, plan/code
  reconciliation, or an evidence-backed recommendation for what to work on next --
  when analyzing a codebase, roadmap, TODO list, issue export, or design doc. Also
  use to install, adopt, extend, or repair an `ltp/` model, or to explore it in
  the bundled dashboard.
---

# ltp

`ltp` turns the logic implicit in a project into **one validated causal model**.
The six Logical Thinking Processes -- Goal Tree, Current Reality Tree, Evaporating
Cloud, Future Reality Tree, Prerequisite Tree, Transition Tree -- are *views* of
that shared model, derived deterministically. They are never authored separately,
so they cannot drift apart.

It ships as a deterministic engine plus a CLI
(`ltp validate | render | sync | check | doctor | migrate | explain`). This skill
covers the **judgment** work: interpreting a repository, proposing meaning,
scrutinizing causality, and repairing the model. Ordinary regeneration is not
your job -- developers and CI run `sync`/`check`.

## Why this exists

An ordinary diagram expresses someone's perception. The Categories of Legitimate
Reservation (CLR) are the tests that make it a *logical* tool. The old version of
this skill described those tests but never executed them, so the agent could omit
Necessary Conditions, flatten a whole Cloud into one node, disconnect a
Prerequisite Tree, and still produce something a viewer accepted.

`ltp` fixes that by making the model **self-policing**:

- The model is **typed**. Every node has a kind from a closed vocabulary; every
  relationship is a *typed claim*, not a generic arrow. A value outside a
  vocabulary is a structural error with a precise location.
- Logic is **validated, never asserted**. `ltp validate` runs the CLR and the
  structural rules of each tree and emits coded diagnostics (`GT-004`, `EC-008`,
  `CRT-006`, ...). The engine never decides whether a cause is real; it verifies
  the review was done and represented honestly.
- The model is the **only authored artifact**. Documents, Mermaid diagrams, and
  dashboard data are generated. `ltp check` re-derives them and fails if a
  committed file is stale or hand-edited -- so a document can never mention a
  `DE-3` the model does not contain.

Read `references/model-and-vocabulary.md` and `references/logical-scrutiny.md`
before building or revising a model.

## Skill vs. the deterministic CLI

Use the **CLI** for anything mechanical and repeatable; use the **skill** (your
judgment) to change what the model *means*.

| Do this with the CLI (deterministic, run by devs/CI) | Do this with the skill (judgment) |
| --- | --- |
| `ltp validate` -- run the CLR + structural rules; print coded diagnostics | Interpret a repository into entities, evidence, and typed claims |
| `ltp sync` -- validate, then **write** every generated projection | Decide the goal, the constraint, the root cause, the injection |
| `ltp check` -- re-derive; **write nothing**; fail on staleness/invalidity (CI) | Scrutinize a claim against the CLR and record the result |
| `ltp render` -- write projections without the publish gate | Decide which trees are warranted (the analysis plan) |
| `ltp doctor` -- diagnose without writing | Repair a diagnostic by changing meaning, not by silencing it |
| `ltp migrate` -- convert a v1 model to v2, preserving ids | Reconcile the model with the plan and the code |
| `ltp explain ID` -- evidence, assumptions, CLR, dependents for one record | Explain a status or defend a recommendation |

If the user just wants their documents regenerated, tell them to run `ltp sync`.
Do not hand-edit anything under `generated/` -- it is machine-owned.

## The CLI contract

- **`ltp validate [--strict] [--json]`** -- load the model and report logical
  diagnostics. Exit 1 if any **error**; with `--strict`, also exit 1 on warnings.
  Warnings and info never block; they are the scrutiny backlog.
- **`ltp sync [--force]`** -- validate, then write every projection. Refuses to
  publish a model with errors unless `--force`.
- **`ltp check`** -- re-derive in memory and write nothing; exit non-zero if the
  model is invalid or any committed projection is stale. This is what CI runs.
- **`ltp render`** -- write projections without the publish gate (for drafts).
- **`ltp doctor`** -- diagnostics plus staleness notes; never writes.
- **`ltp migrate [--write]`** -- convert a v1 permissive model to v2, preserving
  ids, backing up the original.
- **`ltp explain ID`** -- the record, its evidence, assumptions, CLR results,
  what references it, and any diagnostics targeting it.

## The model contract

One file is authored: `ltp/ltp-model.yaml`. Everything under `ltp/generated/` is
written by `ltp sync`. Full detail in `references/model-and-vocabulary.md`; the
essentials:

- **Entities** have a `kind` (goal, critical_success_factor, necessary_condition,
  undesirable_effect, cause, root_cause, constraint, injection, desirable_effect,
  obstacle, intermediate_objective, assumption, ...). **Assumptions are entities**
  with stable ids, referenced like anything else.
- **Status is four independent dimensions**, never one word:
  `basis` (observed | inferred | provisional) -- where it came from;
  `review_status` (unreviewed | corroborated | user_confirmed | disputed |
  invalidated | superseded) -- what scrutiny concluded;
  `confidence` (high | medium | low); and `satisfaction` (unknown | satisfied |
  partial | unsatisfied | not_applicable). Controllability is separate:
  `influence` (control | influence | monitor | outside) -- a necessary condition
  is kept even when it is outside the project's control.
- **Relationships are typed claims**, never generic edges:
  `necessity_claims` ("to achieve OBJECTIVE, PREREQUISITE must exist"),
  `causal_claims` ("PREMISES, combined by OPERATOR, are sufficient to cause
  CONCLUSION"). **Compound sufficiency uses `operator: all`** -- one AND gate,
  never two arrows that each look independently sufficient.
- **First-class structures** for the tools that used to collapse: `clouds` (five
  distinct roles, four necessity claims, an explicit conflict), `predicted_effects`
  (a root cause with no predicted effect is an untested guess),
  `obstacle_resolutions`, `transitions` (existing reality -> need -> action ->
  immediate effect -> advanced IO), and `constraint_assessment`.
- **Views are derived**, not authored. Do not write view membership lists.

## Workflow

Pick the analysis mode, then work the stages. Each stage ends by running
`ltp validate` and repairing what it flags. Never finish by hand-writing a status.

### Choose an operating mode

A full analysis decides which tools are *warranted* -- it does not manufacture
every diagram. Record the decision in `analysis_plan`:

- `diagnose` -- Goal Tree + Current Reality Tree.
- `resolve-conflict` -- Evaporating Cloud + Future Reality Tree.
- `plan-change` -- Future Reality Tree + Prerequisite/Transition Trees.
- `full` -- all warranted views.
- `reconcile` -- compare model, plan, and implementation.

If no persistent conflict exists, record `conflict_analysis` with the rejected
candidates rather than forcing a Cloud. Deferred trees are marked `deferred`, not
faked.

### Stages (forward mode)

1. **Inventory & coverage** -- enumerate and classify files; record coverage gaps.
2. **Evidence extraction by subsystem** -- create `evidence` records with source,
   line range, and observation. Bound each packet to a subsystem.
3. **System boundary & goal candidates** -- up to three candidate goals; select a
   provisional one; mark everything depending on it.
4. **Goal Tree** -- necessity claims from CSFs and NCs to the goal.
5. **Goal Tree scrutiny** -- `ltp validate`; resolve `GT-*` (missing NCs, leaves
   without satisfaction criteria, CSFs necessary for other CSFs).
6. **UDE selection** -- observable, present-tense undesirable effects (not "feature
   X is missing").
7. **Current Reality Tree** -- causal claims with explicit operators; assumptions.
8. **CLR scrutiny & predicted effects** -- record CLR results per important claim;
   give root-cause candidates predicted effects; resolve `CRT-*`, `CLR-*`, `PRED-*`.
9. **Persistent-conflict detection** -- is there a real, chronic conflict?
10. **Cloud construction** -- only when warranted; five roles, four necessity
    claims with assumptions, an explicit conflict, persistence evidence.
11. **Injection selection** -- what breaks an assumption behind the conflict or a
    core causal claim.
12. **Future Reality Tree & negative branches** -- desirable-effect paths to the
    goal; disposition every negative branch with a trimming injection.
13. **Prerequisite Tree** -- obstacles paired with intermediate objectives; order
    by necessity toward the injection.
14. **Transition decomposition** -- one reviewable change per transition, each with
    an immediate observable effect. The model may hold many transitions;
    `recommended_next_action` selects exactly one.
15. **Constraint assessment** -- a goal measure, a limiting-mechanism argument,
    rejected alternatives, a Five Focusing Steps posture.
16. **Whole-model reconciliation** -- `ltp validate`; resolve `XTR-*`.
17. **Deterministic rendering** -- `ltp sync`; commit.

Reverse mode starts from tasks (treat each as a candidate transition action and
infer the logic it serves); reconciliation mode compares code, plan, goal, and
missing work. See `references/workflow.md`.

### Builder / critic discipline

Separate proposing meaning from scrutinizing it. When you build a subtree, then
scrutinize it adversarially:

- A **builder** proposes entities and claims for one subgraph.
- A **critic** returns coded reservations (e.g. `CLR-CAUSE-INSUFFICIENT` on a
  claim); it does **not** silently rewrite the model.
- Run a small bounded repair loop (two or three passes), then retain unresolved
  reservations as recorded `open` CLR checks -- never generate plausible filler to
  make a warning disappear.

### Safe mutation

Change the model by editing typed records, then `ltp validate`; treat structural
errors and diagnostics as the contract to satisfy. Never invent fields or
free-form relationships to route around a validator. Repairing a diagnostic means
changing meaning (add the missing NC, split the compound transition, record the
CLR result honestly) -- not deleting the check.

### Claim-specific evidence

Different claims need different evidence. Current behavior is best evidenced by
tests and runtime; a **goal** or stakeholder preference is not -- for those,
`user_confirmed` review status, strategy docs, and charters outweigh naming
conventions. When you cannot confirm intent, continue with a clearly marked
`provisional` goal; do not stop.

## Publication rule

A model is **publishable** when it has zero error-severity diagnostics. Warnings
and info are the standing scrutiny list a mature model works down over time. A
sufficiency claim is only `scrutinized` once its applicable CLR checks pass; while
any check is `open` it is a **candidate**; a failed required check makes it
`contradicted`. The validator confirms the review happened and is represented
honestly -- it does not decide causality for you.

## Local dashboard

The dashboard is a read-only view of the generated `dashboard-model.json`. Run
`ltp sync` first, then:

```bash
python ltp/scripts/serve_dashboard.py --project /path/to/project --open
```

It binds to loopback and serves only the generated data. See
`references/cli-and-integration.md`.

## Complementarity with `hypothesize`

`ltp` owns system entities, causal structure, assumptions, and logical scrutiny.
`hypothesize` owns operational test definitions, evidence qualification, and
empirical status. Keep logical and empirical status separate: a green
implementation test may prove an injection *exists*; it does not prove the
injection *causes* the modelled effect. Link a claim to a hypothesis via
`verification: {hypothesis_ref, role}`. See `references/cli-and-integration.md`.

## Reference material

- `references/model-and-vocabulary.md` -- the typed model: kinds, the four status
  dimensions, typed claims, first-class structures, derived views.
- `references/logical-scrutiny.md` -- the CLR, predicted effects, sufficiency vs.
  necessity, the constraint-vs-root-cause distinction, publication.
- `references/workflow.md` -- modes, the stages, builder/critic, reverse and
  reconciliation modes, evidence priority, next-action selection.
- `references/cli-and-integration.md` -- the CLI, the generated tree, the
  dashboard, and the `hypothesize` bridge.
- `references/diagnostics.md` -- the full diagnostic-code catalog (generated).
- `references/ltp-model.schema.json` -- JSON Schema generated from the model types.
