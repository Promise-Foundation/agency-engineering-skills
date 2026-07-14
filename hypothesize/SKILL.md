---
name: hypothesize
description: Installs and maintains the hypothesize CLI that derives an honest, machine-readable research status by keeping capability (from tagged tests), evidence maturity, and scientific conclusion strictly separate. Use when asked to extract hypotheses, hook tests up to hypotheses, add a research-status or hypothesis portfolio, adopt hypothesize, connect pytest/behave tests to hypotheses, publish project status, repair traceability, or explain why a hypothesis is marked supported or falsified.
---

# hypothesize

`hypothesize` publishes one honest, machine-readable **research status** for a project by keeping three dimensions that are usually conflated strictly apart. It ships as a deterministic engine plus a CLI (`hypothesize sync | check | doctor | adopt`); this skill covers the judgment work of **installing, adopting, extending, migrating, and repairing** that setup. Ordinary regeneration is not your job — developers and CI run `sync`/`check`.

## The three dimensions (why this exists)

Projects routinely lie to themselves by letting green tests read as "the science works." `hypothesize` refuses to let that happen by deriving three independent statuses:

1. **Capability status** — derived from tagged acceptance scenarios (behave or pytest). A capability is `implemented` when its required scenarios pass, `specified` when they are skipped (declared but unbuilt), `partial` when some pass and some are skipped, `failing` when a required scenario fails and it was never previously green, and `regressed` when something that used to pass now fails. Passing tests prove *behavior exists*. Nothing more.
2. **Evidence maturity** — the single strongest *admitted* evidence artifact linked to a hypothesis, on the ladder `none < design < mechanism < internal_pilot < comparative_pilot < external_replication`. A working mechanism raises maturity to `mechanism`; it does not raise a conclusion.
3. **Scientific conclusion** — `not_tested` by default, and `supported | falsified | inconclusive` only when a **qualified, preregistered study** produces that outcome. **Passing tests can never promote a hypothesis.** Outcome-bearing artifacts that are not both qualified and preregistered are **quarantined** — surfaced, but powerless.

Capability != evidence != conclusion. Most defects this system prevents are category errors that collapse these three. When in doubt, keep them separate.

See `references/publication-model.md` for the full derivation, the maturity ladder, the quarantine rule, and the authority-boundary diagram.

## Skill vs. the deterministic CLI

Use the **CLI** for anything mechanical and repeatable; use the **skill** (your judgment) only for changes to how the repo is wired.

| Do this with the CLI (deterministic, run by devs/CI) | Do this with the skill (judgment, one-time or structural) |
| --- | --- |
| `hypothesize sync` — derive and **write** all targets | Initial install into a repo |
| `hypothesize check` — derive and **write nothing**; fail if a committed target is stale (CI) | Adopt a repo that already implements the pattern |
| `hypothesize doctor` — diagnose without writing | Add pytest or behave integration |
| `hypothesize adopt` — report what exists and whether install is compatible; change nothing | Add a publication target, add CI, migrate schema, repair traceability, author templates, explain a status |

If the user just wants their status regenerated, tell them to run `hypothesize sync` (or `make research-status`). Do not hand-edit generated targets — they are machine-owned between the markers.

## The CLI contract

- **`hypothesize sync`** — read config, load the acceptance report + evidence, derive status, and **write** every configured target (JSON manifest, README/doc marked regions, optional JS data file).
- **`hypothesize check`** — same derivation, **writes nothing**; exits non-zero if any committed target is stale. This is what CI runs.
- **`hypothesize doctor`** — diagnose without writing: untracked test tags (used but unregistered), registry entries with no linked scenarios, unqualified outcome artifacts (would be quarantined), and missing/stale targets.
- **`hypothesize adopt`** — inspect a repo that may already implement this pattern; report what exists (registry, test traceability, publication targets, CI enforcement) and whether installation is compatible. Changes **no** generated files.

## Workflows

Pick the workflow that matches the request. Each ends by running the CLI to prove the wiring works — never by hand-writing a status.

### Install (greenfield)
1. Create the registry from `templates/portfolio.toml` at the configured `catalog` path (default `research/portfolio.toml`). Register the project's real hypotheses, capabilities, requirements, studies, and limitations.
2. Add the `[tool.hypothesize]` config (below) to `pyproject.toml`, or a standalone `hypothesize.toml`.
3. Tag at least one acceptance scenario per capability (see `templates/capability.feature` and `references/tag-vocabulary.md`).
4. Optionally seed `evidence_dir` from `templates/evidence.toml`.
5. Run `hypothesize sync`, commit the generated targets, then run `hypothesize check` — it must pass.
6. Add CI from `templates/ci-github.yml` and the `make` targets from `templates/Makefile.snippet`.

### Adopt (repo already implements the pattern)
Follow `references/adoption.md`. The short version: freeze current outputs, point config at them, run `hypothesize adopt` (expect "compatible"), then `hypothesize check` — the **success test is that adoption leaves the existing publication byte-for-byte unchanged**. The portfolio, evidence, and linked tests stay the source of truth; the package only derives. Do not "improve" the published status during adoption.

### Add pytest or behave integration
Set `[tool.hypothesize.runner].adapter` to `"behave"` or `"pytest"` and point `report` at that runner's JSON acceptance report. Ensure the suite is tagged so every capability traces to scenarios. behave already emits `-f json.pretty`; for pytest, emit a compatible JSON report the adapter reads. Re-run `sync`, then `check`.

### Add a publication target
Append a `[[tool.hypothesize.targets]]` block (`json`, `markdown_region`, or `js`). For `markdown_region`, add the `<!-- BEGIN GENERATED: <marker> -->` / `<!-- END GENERATED: <marker> -->` fence to the doc first, then `sync`. Use `render = "use_cases"` (or another projection) when a region should show something other than the default hypotheses table.

### Add CI enforcement
Copy `templates/ci-github.yml`: run the acceptance suite to produce the report, then `hypothesize check`. Staleness or broken traceability must fail the build.

### Migrate a schema version
When `schema_version` in the registry/manifest changes, update the registry, run `hypothesize doctor` to surface incompatibilities, migrate entries, then `sync` and re-commit. Call out any target whose shape changed.

### Repair broken traceability
`doctor` reports untracked tags and orphaned registry entries. For an **untracked test tag** (used in a feature but not registered), either register the object in the portfolio or correct the tag — never delete the check. For an **orphaned entry** (registered but no linked scenario), add a scenario or mark it `@wip`/specified. Publication *fails* on unresolved untracked tags, so this is load-bearing.

### Explain a status ("why is HYP-x supported / not_tested / partial?")
Read the manifest and the registry, then trace the answer through the three dimensions and the authority table. Common answers: a hypothesis stays `not_tested` because no qualified+preregistered study has produced an outcome (passing tests cannot promote it); a capability is `partial` because a required scenario is skipped; an artifact claiming `supported` is **quarantined** because it is not both qualified and preregistered. Never resolve such a question by editing a status by hand.

## Configuration contract

In the consumer repo's `pyproject.toml` (or a standalone `hypothesize.toml`). Match these keys exactly.

```toml
[tool.hypothesize]
catalog = "research/portfolio.toml"        # the versioned registry (source of truth)
evidence_dir = "research/evidence"          # optional: dir of *.toml evidence artifacts

[tool.hypothesize.runner]
adapter = "behave"                          # "behave" or "pytest"
report = "artifacts/research/behave.json"   # path to the JSON acceptance report

[tool.hypothesize.evidence]
collector = "mypkg.research:collect_evidence"  # optional "module:function" -> EvidenceBundle

[[tool.hypothesize.targets]]
kind = "json"                               # write the full manifest
path = "research/generated/research-status.json"

[[tool.hypothesize.targets]]
kind = "markdown_region"                    # replace a BEGIN/END GENERATED block
path = "README.md"
marker = "research-status"                  # <!-- BEGIN GENERATED: research-status --> / END

[[tool.hypothesize.targets]]
kind = "markdown_region"
path = "use-cases/README.md"
marker = "use-case-status"
render = "use_cases"                        # optional: which projection to render

[[tool.hypothesize.targets]]
kind = "js"                                 # write `window.<variable> = <manifest json>;`
path = "site/generated/research-data.js"
variable = "RESEARCH_STATUS"
```

## Registry contract (`research/portfolio.toml`)

Stable-ID object families (see `templates/portfolio.toml`):

- **`hypotheses`** — empirical propositions. `tag` (e.g. `hyp_ub_1`) maps the Gherkin tag to the `id` (`HYP-*`); the tag may be auto-derived from the id. Only a qualified, preregistered study result changes a hypothesis conclusion.
- **`capabilities`** — things the implementation can demonstrably do. `tag` (`cap_*`) maps to `CAP-*`; `hypotheses = [...]` links the capability to what it informs.
- **`requirements`** — normative release/workflow gates (not hypotheses), with `capabilities`/`hypotheses` links.
- **`studies`** — evidence-producing designs, carrying `preregistered` and `qualified` flags.
- **`limitations`** — reasons a claim cannot yet be promoted.

Evidence artifacts (in `evidence_dir` or from the `collector`) carry: `id`, `hypotheses`, `kind` (`mechanism | scientific | study_design | ...`), `maturity`, `qualified`, `preregistered`, `outcome` (`not_tested | supported | falsified | inconclusive`). See `templates/evidence.toml`.

## Tag contract (acceptance features/tests)

Full detail in `references/tag-vocabulary.md`. Summary:

- **Domain/architecture** tags name the area — freeform (e.g. `@application`, `@scoring`).
- **Requirement strength**: `@must` `@should` `@may`.
- **Hypothesis links**: `@hyp_<id>` (e.g. `@hyp_ub_1`) -> `HYP-*`. **Capability links**: `@cap_*` -> `CAP-*`.
- **Evidence role**: `@evidence_capability` (behavior exists; no maturity bump), `@evidence_mechanism` (bounded mechanism -> maturity `mechanism`), `@evidence_scientific_contract` (tests a scientific *workflow*, not an outcome).
- **Controls**: `@clean_control` `@negative_control` `@adversarial` `@synthetic_fixture` `@independence_required` `@wip` (specified-but-unbuilt; skipped, registers as "specified").
- There is **never** a `@hypothesis_supported` or `@validated` tag. Scientific status is *computed*, never asserted in feature text.

Every `@hyp_*`/`@cap_*` tag used in a test must be registered in the portfolio, or **publication fails**. This is the traceability contract `check` and `doctor` enforce.

## Authority boundaries

Which input class is allowed to move which status. This is the heart of the model — enforce it in every workflow.

| Input class | Capability status | Evidence maturity | Scientific conclusion |
| --- | --- | --- | --- |
| Tagged scenario passes / fails / is skipped | Sets it (`implemented`/`partial`/`specified`/`failing`/`regressed`) | No effect | **No effect** |
| `@evidence_capability` scenario | Confirms behavior | No bump | **No effect** |
| `@evidence_mechanism` scenario / `mechanism` artifact | No effect | May raise to `mechanism` | **No effect** |
| `study_design` / `design` artifact | No effect | May raise to `design` | **No effect** |
| `@evidence_scientific_contract` scenario | Capability only (workflow exists) | No bump | **No effect** |
| Outcome-bearing artifact, NOT (qualified AND preregistered) | No effect | No effect | **Quarantined** — no effect |
| Qualified **and** preregistered study result with an outcome | No effect | No effect | **Sets it** (`supported`/`falsified`/`inconclusive`) |

The bottom row is the *only* way a scientific conclusion changes. If you are ever tempted to move a conclusion any other way, stop — that is the category error this system exists to prevent.

## Determinism and staleness

The manifest carries a `build.source_hash` computed from its inputs (registry + evidence + acceptance report). Identical inputs produce byte-identical output. `check` re-derives and compares against the committed targets; if any differ, they are **stale** and `check` exits non-zero. This is why CI can enforce "the published status matches the tests" without trusting a human to re-run `sync`.

## Reference material

- `references/publication-model.md` — the epistemic model in depth (three dimensions, capability-status derivation, maturity ladder, quarantine, source hash, staleness, authority diagram).
- `references/adoption.md` — the adoption playbook and extraction sequence.
- `references/tag-vocabulary.md` — the full tag vocabulary and the three `@evidence_*` roles.
- `templates/` — `portfolio.toml`, `evidence.toml`, `capability.feature`, `ci-github.yml`, `Makefile.snippet`.
