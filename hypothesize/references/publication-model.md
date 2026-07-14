# Publication model

The epistemic contract `hypothesize` enforces. The whole point is to make one honest, machine-readable research status in which **implementation progress can never be mistaken for empirical validation**. It does that by deriving three statuses that are usually — and dangerously — conflated.

## Contents
- [The three dimensions](#the-three-dimensions)
- [Capability status derivation](#capability-status-derivation)
- [Evidence maturity ladder](#evidence-maturity-ladder)
- [Scientific conclusion](#scientific-conclusion)
- [The quarantine rule](#the-quarantine-rule)
- [Authority boundaries](#authority-boundaries)
- [Deterministic source hash and staleness](#deterministic-source-hash-and-staleness)
- [Traceability validation](#traceability-validation)
- [The manifest](#the-manifest)

## The three dimensions

| Dimension | Answers | Derived from | Can a passing test change it? |
| --- | --- | --- | --- |
| **Capability status** | "Does the software do X?" | Tagged acceptance scenarios | Yes — this is what tests decide |
| **Evidence maturity** | "How strong is the strongest admitted evidence for hypothesis H?" | Evidence artifacts + evidence-role tags | Only to raise a *mechanism* rung — never a conclusion |
| **Scientific conclusion** | "Is hypothesis H supported / falsified / inconclusive?" | Qualified, preregistered study results only | **Never** |

The single most important invariant: **a green test suite proves behavior exists; it does not validate a hypothesis.** These three answers live in separate fields and are computed by separate rules. Collapsing them is the category error the system exists to prevent.

## Capability status derivation

Each capability in the registry links (via `@cap_*` tags) to a set of required acceptance scenarios. Status is a pure function of those scenarios' outcomes in the acceptance report, plus history for regression:

| Status | Condition |
| --- | --- |
| `implemented` | All required scenarios passed. |
| `partial` | Some required scenarios passed and some were skipped (none failing). |
| `specified` | Required scenarios exist but are all skipped — declared but unbuilt (e.g. `@wip`). |
| `failing` | A required scenario fails and this capability was not previously `implemented`. |
| `regressed` | A required scenario fails that used to pass — a regression, kept visible rather than hidden. |

`specified` is a feature, not a gap: a `@wip` scenario is a promise on the record. `regressed` deliberately preserves history — a capability that backslides does not silently revert to `failing`; it reads `regressed` so the regression is legible.

Capability status **never** touches evidence maturity or the scientific conclusion. A fully `implemented` capability whose hypotheses are `not_tested` is the normal, honest state of a project that has built mechanisms but not yet run studies.

## Evidence maturity ladder

Maturity is the **strongest admitted** evidence artifact linked to a hypothesis, on this total order:

```
none  <  design  <  mechanism  <  internal_pilot  <  comparative_pilot  <  external_replication
```

- `none` — nothing beyond the statement.
- `design` — a study is designed/preregistered but has produced no outcome (a `study_design` artifact).
- `mechanism` — a bounded mechanism demonstrably works on fixtures (`@evidence_mechanism` scenario or a `mechanism` artifact). This is the highest rung reachable *without a study result*.
- `internal_pilot` / `comparative_pilot` / `external_replication` — successively stronger empirical evidence, reachable only through admitted study results.

"Admitted" means the artifact passed traceability and role checks. A quarantined artifact contributes **nothing** to maturity. Maturity is orthogonal to conclusion: reaching `comparative_pilot` maturity does not by itself make a conclusion `supported` — the study still has to have been qualified and preregistered and to have reported that outcome.

## Scientific conclusion

Default `not_tested`. It becomes `supported`, `falsified`, or `inconclusive` **only** when an admitted study result satisfies *all* of:

1. `qualified = true` — the result meets the precommitted quality bar.
2. `preregistered = true` — the design was registered before the result.
3. `outcome` is one of `supported | falsified | inconclusive` (i.e. not `not_tested`).

If any of these fails, the conclusion stays `not_tested`. No tag, no passing scenario, no mechanism, and no unqualified artifact can move it. This is enforced by the authority table below.

## The quarantine rule

An artifact that **bears an outcome** (`outcome != not_tested`) but is **not both qualified and preregistered** is **quarantined**: it is listed in the manifest's `quarantined_evidence`, it does **not** raise maturity, and it does **not** touch the conclusion. Quarantine is the system's immune response to premature or unqualified claims — the claim stays visible (so it is not lost or hidden) but is stripped of authority.

Example: an artifact reporting `outcome = "supported"` with `qualified = false` appears in `quarantined_evidence`; the hypothesis conclusion remains `not_tested`.

## Authority boundaries

The complete matrix of which input class may move which status.

| Input class | Capability status | Evidence maturity | Scientific conclusion |
| --- | --- | --- | --- |
| Tagged scenario passes / fails / is skipped | **Sets** (`implemented`/`partial`/`specified`/`failing`/`regressed`) | — | — |
| `@evidence_capability` scenario | Confirms behavior | — | — |
| `@evidence_mechanism` scenario / `mechanism` artifact | — | **May raise to `mechanism`** | — |
| `study_design` / `design` artifact | — | **May raise to `design`** | — |
| `@evidence_scientific_contract` scenario | Capability only (workflow exists) | — | — |
| Admitted pilot / replication result (qualified + preregistered) | — | **May raise** to the corresponding pilot/replication rung | see next row |
| Qualified **and** preregistered study result with an outcome | — | — | **Sets** (`supported`/`falsified`/`inconclusive`) |
| Outcome-bearing artifact, NOT (qualified AND preregistered) | — | — (quarantined) | — (quarantined) |

Read it as a one-way flow:

```
tagged scenarios ──────────────▶ CAPABILITY STATUS
                                  (implemented/partial/specified/failing/regressed)

evidence-role tags + artifacts ─▶ EVIDENCE MATURITY
   @evidence_capability ─────────▶  (no bump)
   @evidence_mechanism ──────────▶  mechanism
   study_design/design artifact ─▶  design
   admitted pilot/replication ───▶  internal_pilot ▸ comparative_pilot ▸ external_replication

qualified + preregistered study ▶ SCIENTIFIC CONCLUSION  ◀── (nothing else reaches here)
   result outcome ───────────────▶  supported / falsified / inconclusive

unqualified outcome artifact ───▶ QUARANTINE (affects nothing)
```

The scientific-conclusion box has exactly one inbound arrow. If you are moving a conclusion by any other path, you are violating the model.

## Deterministic source hash and staleness

Derivation is a pure function of its inputs: the registry (`catalog`), the evidence (`evidence_dir` and/or `collector`), and the acceptance report (`runner.report`). The manifest records a `build.source_hash` over those inputs, so identical inputs produce **byte-identical** output.

A committed target is **stale** if re-deriving it from the current sources would differ from the committed bytes. `hypothesize check` re-derives, compares, and exits non-zero on any difference — without writing. That is what lets CI assert "the published status matches the tests and evidence" without trusting anyone to have re-run `sync`. `hypothesize sync` is the writing counterpart; `doctor` reports staleness as a diagnosis without writing.

## Traceability validation

Every `@hyp_*` and `@cap_*` tag used in the acceptance suite must resolve to a registered object in the portfolio. An **untracked tag** (used but unregistered) makes publication **fail** — a test cannot claim to exercise a hypothesis or capability the registry has never heard of. Conversely, `doctor` reports **orphaned** registry entries (registered but with no linked scenario) so the registry does not drift into aspirational fiction. Traceability is bidirectional and enforced; it is not advisory.

## The manifest

The `json` target is the canonical projection. Its top-level shape:

- `schema_version` — integer registry/manifest version.
- `build` — `{ evidence_count, scenario_counts, source_hash }`.
- `portfolio` — registry metadata (title, thesis, last_reviewed).
- `capabilities[]` — each with `id`, `tag`, `title`, `hypotheses`, `scenario_counts`, `scenario_ids`, `status`.
- `hypotheses[]` — each with `id`, `tag`, `title`, `statement`, `summary`, `capability_status`, `evidence_maturity`, `evidence_health` (`current`/`stale`), `conclusion`, `evidence` (linked artifact ids), `scenario_counts`.
- `requirements[]`, `studies[]`, `limitations[]` — projected from the registry.
- `quarantined_evidence[]` — outcome-bearing artifacts that failed the qualified+preregistered gate.

Markdown-region and JS targets render projections of this same manifest, so every surface agrees by construction — the Markdown table reports the same capability status the JSON carries.
