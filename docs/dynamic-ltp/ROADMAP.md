# Dynamic-LTP roadmap

From an **instrumented current-state model** to a **currency-enforced learning
system** — without throwing away what already works.

This is the plan we converged on across the design dialogue. It is deliberately
written the way this repo writes everything: the moves are registered as
hypotheses and capabilities with gherkin acceptance contracts and evidence-role
ceilings ([`docs/dynamic-ltp/portfolio.toml`](portfolio.toml),
[`docs/dynamic-ltp/features/`](features/)), and the UI moves are fully explicated
as gherkin ([`agency-ui/features/`](../../agency-ui/features/)). Practice what we
preach: the plan is on the record and derivable, not prose that drifts.

## Implementation status · 2026-07-17

Workstreams A–E are implemented. Schema v3 adds typed semantic relations,
observations, temporal prediction fields, pure evaluations, and deterministic
learning obligations. The read-only history projector unifies existing source
records, and the LTP plugin exposes current model, history/diff/playback,
prediction, perspective, attention, and lifecycle views. Executable evidence is
in `ltp/tests/test_dynamic.py`, `ltp/tests/test_migrate.py`, and the 21-scenario /
117-step Cucumber/Playwright suite under `agency-ui/features/`. These results
prove bounded capabilities; they do not change any scientific conclusion.

## 1. What we are building

The LTP engine already nails the *structural* half of a dynamic model: separated
status dimensions, typed claims, one-model-many-derived-views, CLR-validated
logic, and a hypothesize bridge that keeps logical and empirical status side by
side. The implemented program adds the previously missing **time** axis across four gaps:
no timeline/diff, no decision/change records, no predicted-vs-observed learning
state, and no expected-lag on arrows.

The reframe that organizes the whole program:

> **Publishable should mean "no overdue unresolved learning obligations," not
> merely "the projections match the source."**

`ltp check --as-of YYYY-MM-DD` now enforces both *internal* currency (the diagram
cannot drift from the model) and representable *external* currency (overdue
learning obligations block publication). The fifth workstream makes that state
legible in the UI.

## 2. What we are NOT building

- **Not a parallel generic event store.** The refined architecture keeps the
  typed current-state model as the authored artifact and **unifies records that
  already exist** into a read-model. (`HYP-DYN-HISTORY`.)
- **Not wall-clock time inside the engine.** Every obligation and evaluation is
  computed relative to an **explicit as-of date** passed by the caller/CI, so
  `validate()` stays a pure function and golden tests / `source_hash` stay
  deterministic.
- **Not animation-first.** The load-bearing dynamic features are separated
  status, instrumented arrows, the prediction loop, the semantic diff, and
  preserved dissent. Playback is the least important and comes last.

## 3. Design invariants

1. **Determinism is sacred.** `source_hash` hashes with `prune=False`
   ([`provenance.py:21`](../../ltp/src/ltp/provenance.py)), so *any* new field
   rebases every model's hash → each schema change is a `schema_version` bump with
   a [`migrate.py`](../../ltp/src/ltp/migrate.py) path. New derivations must be
   pure functions of (model, explicit-clock).
2. **Evidence-role ceilings hold everywhere.** `@evidence_capability` proves a
   behavior exists; `@evidence_mechanism` may reach `mechanism` maturity;
   `@evidence_scientific_contract` proves the status machinery works; only a
   qualified+preregistered study moves a conclusion. The UI honors the same
   ceiling visually (Workstream E).
3. **Structure vs. epistemic state stay separate.** The typed model owns current
   structure; the learning history owns change/evidence/positions over time. A new
   field never conflates the two (e.g. an observation never edits a CLR result).
4. **Schema/TS/catalog are generated, never hand-edited.** `python -m ltp.schema`
   re-derives [`ltp-model.schema.json`](../../ltp/references/ltp-model.schema.json),
   [`model-types.ts`](../../ltp/dashboard/src/model-types.ts), and
   [`diagnostics.md`](../../ltp/references/diagnostics.md) from the dataclasses
   ([`schema.py:43`](../../ltp/src/ltp/schema.py)); `--check` is the CI gate.
5. **Gherkin-first parity.** Every move lands as a `@wip` contract first, then
   code, then the tag drops and the scenario must pass — the same progression the
   reference project and hypothesize both use.

## 4. Workstreams

### A — Relation polarity (the ontology fix) · `CAP-RELATION-POLARITY`

**Why first:** it's cheap, orthogonal to time, and a defect in any architecture —
a `causes`-typed edge from `TRIM-1` to `NBR-1` is as false event-sourced as in
YAML. Today the self-model carries a three-line apology comment on `CLM-6`
because a *neutralizes* relationship can only be expressed as sufficiency.

**Implemented:** a first-class `SemanticRelation` record with a closed vocabulary
(`causes|requires|enables|contributes_to|prevents|mitigates|neutralizes|detects|responds_to|evidences|tests|implements|supersedes|contradicts`).
Forward causation remains a scrutinizable `CausalClaim`; `REL-002` rejects
attempts to bypass its sufficiency semantics.

**Seams** (mirror `ObstacleResolution`'s ~13 touch-points):
- dataclass + `LtpModel` field + `_ID_FAMILIES` + `ModelIndex`
  ([`models.py:264,400,553,640`](../../ltp/src/ltp/models.py)); id prefix
  ([`ids.py:51`](../../ltp/src/ltp/ids.py)).
- kind validation ([`structure.py:153`](../../ltp/src/ltp/validators/structure.py));
  **replace FRT-006's causal-reachability check**
  ([`reality.py:167`](../../ltp/src/ltp/validators/reality.py)) and the causal
  adjacency it uses ([`graph.py:38`](../../ltp/src/ltp/validators/graph.py)).
- stop hard-coding `"causes"` in the three renderers
  ([`mermaid.py:98`](../../ltp/src/ltp/renderers/mermaid.py),
  [`dashboard.py:53`](../../ltp/src/ltp/renderers/dashboard.py),
  [`markdown.py:142`](../../ltp/src/ltp/renderers/markdown.py)).
- migration mirrors the `overcome_by`→`obstacle_resolutions` map
  ([`migrate.py:204`](../../ltp/src/ltp/migrate.py)).

**Done:** [`relation_polarity.feature`](features/relation_polarity.feature) passes;
`CLM-6` needs no comment; a prevention-as-sufficiency raises a coded error.

### B — Live causal-outcome prediction loop · `CAP-PREDICTION-EVALUATION`

**Why:** generalize the one live "did reality behave as predicted?" loop the repo
already runs for *capabilities* (tagged scenario → report → pass/fail/regressed)
to *causal outcomes*. Today `consequences`/`defeaters` are authored pass-through
the engine never evaluates.

**Do:** add temporal fields (`expected_by`, `expected_lag`, `tolerance`,
`review_by`) to `PredictedEffect` ([`models.py:249`](../../ltp/src/ltp/models.py);
they round-trip as strings via
[`store.py:27`](../../ltp/src/ltp/store.py)); add a `PredictionEvaluation` record
(mirror the `PredictedEffect` wiring); add a pure evaluator classifying
`supported|contradicted|inconclusive|not_yet_due` from (prediction, observation,
as-of-date); add `PRED-OVERDUE`/`OBS-STALE` codes.

**Seams:** codes in `CATALOG` ([`diagnostics.py:32`](../../ltp/src/ltp/diagnostics.py));
emit from a validator registered in
[`validators/__init__.py:28`](../../ltp/src/ltp/validators/__init__.py) (aggregated
by `run_all`, `:71`).

**Done:** [`prediction_evaluation.feature`](features/prediction_evaluation.feature)
passes on a synthetic fixture (`@evidence_mechanism`); recording an observation
never changes a CLR result.

### C — Unified learning history · `CAP-LEARNING-HISTORY`

**Why:** the read-model that makes timeline/diff/attention possible without a new
write path.

**Do:** a deterministic, hashable projection unifying **git** revisions of the
single authored `ltp-model.yaml`, promisify's already-append-only
[`.norms/assessments/`](../../.norms) (repairs are superseding records), hypothesize's
regenerated `research-status.json` snapshots, and Workstream-B prediction
evaluations. Provide `as_of(date)` and `diff(date_a, date_b)` (semantic, not text).

**Seam / gap:** **promisify emits no relations today**
([`promisify-plugin/src/mapping.ts`](../../agency-ui/skills/promisify-plugin/src/mapping.ts)),
so the projection correlates assessments to a claim by **subject + domain**, or we
add a `toRelations` to promisify. The federation merge point is
[`resource-service.ts:81`](../../agency-ui/packages/agency-core/src/resource-service.ts);
join key is `domain`.

**Done:** [`learning_history_projection.feature`](features/learning_history_projection.feature)
passes; no source record is copied into a new authoritative log.

### D — Enforcement: the learning-obligation gate · `CAP-LEARNING-OBLIGATION-GATE`

**Why:** turn "please keep it current" into red CI. This is where the reframe bites.

**Do:** derive learning obligations (overdue prediction, stale observation,
unreviewed revision, completed-but-unverified intervention) relative to an
**explicit as-of date**; emit an **ERROR**-severity code when one is overdue.

**Seam:** a new ERROR code flows through `report.errors`
([`validators/__init__.py:47`](../../ltp/src/ltp/validators/__init__.py)) and blocks
`cmd_sync` / `cmd_check`
([`cli.py:139`](../../ltp/src/ltp/cli.py)). The CLI adds `--as-of` so the clock is
explicit and reproducible; `is_publishable` then means *both* zero logical errors
and no overdue obligations at that date.

**Done:** [`learning_obligation_gate.feature`](features/learning_obligation_gate.feature)
passes; the same model is green before a review date and red after — from data, not
a hand-edited status.

### E — The dynamic dashboard, fully in gherkin · `CAP-DYNAMIC-DASHBOARD`, `CAP-EPISTEMIC-CEILING-UI`

**Why:** make it legible, and prove the essay's core point — no green signal reads
as a conclusion it hasn't earned.

**Do:** six views, each a projection of the same records, specified in full at
[`agency-ui/features/`](../../agency-ui/features/):

| Feature | Recommendation it realizes |
|---|---|
| [`01_learning_history_timeline`](../../agency-ui/features/01_learning_history_timeline.feature) | snapshot / semantic diff / playback |
| [`02_prediction_vs_outcome`](../../agency-ui/features/02_prediction_vs_outcome.feature) | predicted vs observed vs validated, kept separate |
| [`03_disagreement_perspective`](../../agency-ui/features/03_disagreement_perspective.feature) | observer-relative disagreement (promisify) |
| [`04_attention_required`](../../agency-ui/features/04_attention_required.feature) | "you are here / what's next" from obligations |
| [`05_node_lifecycle_history`](../../agency-ui/features/05_node_lifecycle_history.feature) | lifecycle as a sequence, not a scalar |
| [`06_epistemic_ceiling_guard`](../../agency-ui/features/06_epistemic_ceiling_guard.feature) | the flagship guard (mirrors the reference app) |

**Seams:** add a `RouteContribution` + `dashboardCards` in a plugin
([`contributions.ts:119`](../../agency-ui/packages/agency-skill-sdk/src/contributions.ts);
template [`ltp-plugin/src/plugin.ts:26`](../../agency-ui/skills/ltp-plugin/src/plugin.ts));
the **unused `inspectors` slot**
([`ResourceInspector.tsx:51`](../../agency-ui/apps/web/src/shell/ResourceInspector.tsx))
is free for a timeline inspector. Data via `useDomainModel`
([`views.tsx:21`](../../agency-ui/skills/ltp-plugin/src/views.tsx)); cross-source
history via the federated `relations()` the `Relations` panel already uses
([`ResourceInspector.tsx:94`](../../agency-ui/apps/web/src/shell/ResourceInspector.tsx)).

**Shell wiring (the one non-additive change):** in e2e mode the shell loads a
fixture `manifestSource` selected by the `x-e2e-fixture` header (see
[`features/support/world.ts`](../../agency-ui/features/support/world.ts)); the
`createMemorySource` live seam in
[`zpd-demo.tsx`](../../agency-ui/apps/web/src/demo/zpd-demo.tsx) is the precedent.

**Done:** each feature's `@wip` drops and it passes against the real shell through
its public surface; `REQ-DYN-CEILINGS-HELD` holds.

## 5. Sequencing

```
A (polarity)  ──┐         cheap, orthogonal, unblocks nothing but pays down debt now
                │
B (prediction) ─┼──> D (obligation gate)   D needs B's temporal fields to have obligations
                │
                └──> C (learning history)  C consumes B's evaluations + existing records
                            │
                            └──> E (dashboard)  E projects B/C/D; ships view-by-view
```

This sequence was followed: A shipped independently; B unlocked D and fed C; E
then landed as coordinated projections with every `@wip` tag removed.

## 6. Putting the plan on the record

The program remains registered in [`portfolio.toml`](portfolio.toml) as
`HYP-DYN-*` / `CAP-*`. Engine contracts are mirrored by executable pytest tests;
UI contracts run through Cucumber and Playwright against deterministic fixture
sources and the real shell. Evidence-role tags remain the inference ceiling.

Verify the current state anytime:

```bash
cd agency-ui && npm run test:bdd:serve
../.venv/bin/python -m pytest ../ltp/tests/test_dynamic.py ../ltp/tests/test_migrate.py
```

## 7. Migration & back-compat

Schema v3 has a v2→v3 migration in [`migrate.py`](../../ltp/src/ltp/migrate.py).
It moves a trimming-injection→negative-branch sufficiency claim into
`semantic_relations` as `neutralizes`, preserving `CLM-6`; v1 migration composes
through v2 and v3. Generated schema, TypeScript types, diagnostics, and golden
artifacts are refreshed with the change.

## 8. Risks & open questions

- **Event/replay determinism** (if C ever grows a real write path): version events
  with upcasters and golden-test over *sequences*, not just states. Deferred while
  C stays a read-model.
- **Obligation granularity.** Journaling too much yields "an impeccable history of
  meaningless activity." Record only acts whose provenance changes a decision;
  keep wording diffs to git. If the attention queue is noisy, the gate gets
  disabled — a UX failure, tracked as a `HYP-DYN-CURRENCY` defeater.
- **Promisify correlation remains bounded:** the perspective projection
  correlates attributable assessments by subject/domain. A future stable direct
  relation would be stronger when Promisify persists token-level claim links.
- **"Model drifts from reality" is only ever bounded, not closed.** The gate makes
  *representable* obligations enforceable; it cannot know about an obligation no one
  recorded. Honest limitation, on the record as `LIM-DYN-*`.

## 9. Definition of done (program)

1. `relation_polarity` green; `CLM-6` apology deleted.
2. `prediction_evaluation` green on fixtures; observation never edits logic.
3. `learning_history_projection` green; deterministic, hashable, no new log.
4. `learning_obligation_gate` green; a stale-but-consistent model is red in CI.
5. All six `agency-ui/features/` pass against the real shell; ceilings hold.
6. Capability evidence comes from real pytest and browser results; the separate
   program portfolio remains an epistemic envelope and does not hand-author a
   scientific conclusion.
