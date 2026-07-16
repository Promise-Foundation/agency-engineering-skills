---
name: hypothesize
description: Makes uncertain assertions explicit and maintains their evidentiary standing without collapsing hypotheses, capabilities, evidence, and conclusions. Use when asked to extract hypotheses from documents, plans, models, repositories, or research programs; identify consequences, defeaters, assumptions, or evidence; connect another tool's assertions to an epistemic record; install or adopt the hypothesize CLI; link pytest/behave tests to hypotheses; publish project status; repair traceability; or explain why a conclusion has its current status.
---

# hypothesize

`hypothesize` is a thin layer for hypothetical reasoning. It makes consequential assertions explicit, keeps them open to possible defeat, links them to relevant evidence, and records what that evidence currently warrants.

A hypothesis is a proposition held in the interrogative mood:

> Could this be so?

It may organize inquiry, explain an observation, motivate a design, or support a plan. It is not thereby a fact, a requirement, an implemented capability, or a finding.

The originating document or tool owns the assertion's domain meaning. `hypothesize` adds an **epistemic envelope** around it:

```text
assertion
  + scope and conditions
  + expected consequences
  + possible defeaters
  + evidence and provenance
  + current evidentiary standing
```

The current CLI implements a concrete **software-research profile** for publishing deterministic project status. Use that profile when the target is a software project that adopts its contracts. Do not force open-ended research programs, strategies, causal models, or other epistemological projects into the software profile merely because the CLI exists.

## Core invariants

Preserve these in every workflow.

1. **A hypothesis is not a finding.** Plausibility may justify investigation; it does not establish truth.
2. **The host owns the assertion.** Reference an LTP claim, design decision, manuscript passage, or external model rather than silently replacing its domain representation.
3. **Scope is part of the proposition.** Population, environment, version, conditions, and time horizon cannot be dropped when evidence is transferred.
4. **A meaningful hypothesis must be losable.** State what would follow if it were true and what could count against it. If no conceivable observation bears on it, report that limitation rather than inventing a test.
5. **Evidence is relational and contextual.** Record whether evidence supports, challenges, limits, or merely concerns the proposition, together with its provenance and conditions.
6. **Standing must not exceed evidence.** Missing evidence is not support; implementation is not validation; repetition is not independence; a favorable result at one revision or scope does not automatically transfer to another.
7. **Keep distinct status dimensions distinct.** Logical coherence, implementation capability, evidence maturity, empirical conclusion, normative fulfillment, and action authorization are different judgments.
8. **Preserve uncertainty and disagreement.** Do not manufacture one clean narrative when the record supports local conclusions and unresolved questions.

## Choose the task mode

### Analyze

Use when the user gives a document, plan, model, repository, research program, or body of claims and wants its hypotheses or evidence structure made explicit.

### Model or interoperate

Use when another tool already owns the assertions and needs epistemic annotations—for example, causal claims from LTP or promises from Promisify.

### Integrate the software-research profile

Use when installing, adopting, extending, or migrating the current `hypothesize` CLI in a software project.

### Explain or repair

Use when tracing a published status to its inputs, repairing broken traceability, diagnosing quarantine, or reconciling generated outputs with their sources.

## Analyze a body of work

Do not begin by forcing the material into the current TOML schema. First understand the epistemic structure.

1. **Set the target and granularity.** Identify the document, model, project, decision, or subsystem being analyzed. Prefer local, decision-relevant propositions over one grand thesis that hides distinct uncertainties.
2. **Inventory consequential assertions.** Look for causal claims, predictions, generalizations, mechanism claims, feasibility assumptions, transfer claims, and propositions on which a plan depends.
3. **Classify before extracting.** Distinguish:
   - hypotheses: propositions that could receive empirical or evidential support;
   - observations: reports of what was seen;
   - assumptions: conditions taken for granted;
   - definitions: meanings fixed by stipulation;
   - norms or promises: what ought to be true;
   - capabilities: what a system demonstrably does;
   - decisions: choices made under uncertainty.

   Do not turn every important sentence into a hypothesis.
4. **Normalize each hypothesis.** Make the subject, relation, scope, conditions, and time horizon explicit. Split compound assertions when their parts could receive different evidence.
5. **Derive inquiry consequences.** Record what else should be observable if the proposition is correct. Reuse predictions owned by the host tool when available.
6. **Identify defeaters and alternatives.** State observations that would weaken the proposition, rival explanations, and assumptions whose failure would change its interpretation.
7. **Map evidence conservatively.** For each artifact or observation, record:
   - the proposition it actually bears on;
   - whether it supports, challenges, limits, or contextualizes it;
   - provenance, date, version, population, and method;
   - independence and known limitations;
   - whether the evidence concerns the same object and conditions.
8. **Assign a scoped standing under an explicit policy.** Use the vocabulary requested by the user or active profile. Include the rationale; do not reduce a mixed record to a bare label.
9. **Separate conclusions from unknowns.** Report what can be concluded, what cannot be concluded, and what observation or decision would change the state of inquiry.

For open-ended analysis, a useful output shape is:

```yaml
hypothesis:
  id: HYP-001
  subject_ref: ltp://claims/CLM-17
  proposition: Realistic evaluation fixtures reduce readiness overestimation.
  conditions:
    - software projects using pre-deployment readiness reviews
  consequences:
    - calibration error is lower when representative fixtures are used
  defeaters:
    - no calibration difference under a representative comparison
  alternatives:
    - reviewer incentives explain the difference instead
  evidence:
    - ref: evidence://study-12
      relation: supports
    - ref: evidence://case-7
      relation: limits
  standing:
    value: inconclusive
    policy: project://evidence-policy/v2
    rationale: Evidence is directionally favorable but not comparative.
```

Use only fields supported by the requested output or consumer. When the current CLI schema cannot represent an important distinction, preserve it in a linked source document, `summary`, or `limitations`; do not silently discard it or invent incompatible schema behavior.

## Interoperate without taking over

The originating tool remains authoritative for its own objects and status dimensions.

Prefer a stable reference plus a revision or digest:

```yaml
subject_ref: ltp://claims/CLM-17
subject_revision: 8f21c4a
subject_digest: sha256:...
```

If the referenced assertion changes materially, its old evidentiary standing must not silently transfer.

### LTP

LTP owns causal propositions, necessary conditions, injections, predicted effects, and CLR scrutiny. `hypothesize` records what evidence bears on those propositions.

Keep these side by side:

```yaml
logical_status:
  source: ltp
  value: scrutinized

evidentiary_standing:
  source: hypothesize
  value: inconclusive
```

A logically coherent claim may be empirically falsified. An empirically suggestive claim may remain logically incomplete. Hypothesize results may trigger renewed LTP scrutiny, but they must not overwrite LTP's logical status.

### Promisify

Promisify owns what ought to be true and attributable assessments of promise fulfillment. Hypothesize owns empirical propositions and what evidence warrants about them.

```text
Hypothesis: Technique X improves outcome Y.
Promise: We will run probation P under conditions C.
Assessment: P was performed as specified.
Conclusion: The admitted result supports, challenges, or leaves the hypothesis unresolved.
```

Do not treat a kept promise as proof of the linked hypothesis, or a supported hypothesis as proof that a promise was fulfilled.

### General interoperability rule

> The host owns the assertion and its domain semantics. Hypothesize owns the record of why the assertion remains open, what evidence bears on it, and what standing that evidence currently warrants.

Use thin adapters and shared identifiers. Do not copy an entire host model into a second competing representation.

## The current software-research profile

The shipped CLI publishes one deterministic, machine-readable research status for a software project. In this profile, three dimensions are derived independently.

### 1. Capability status

Derived from tagged acceptance scenarios:

- `implemented` — all required linked scenarios pass;
- `partial` — at least one required scenario passes and others do not pass;
- `specified` — no required scenario passes, including skipped or currently unlinked capabilities;
- `failing` — a required scenario fails and the capability was not previously implemented;
- `regressed` — a previously implemented capability now has a required failure.

Passing tests provide bounded evidence that the tested behavior is implemented under the tested conditions. They do not establish usefulness, generality, causal effect, or the truth of a linked hypothesis.

The current engine uses `specified` both for explicitly skipped work and for a capability with no linked required scenarios. When explaining that status, distinguish those cases from the manifest and traceability record rather than describing both as demonstrated specification.

### 2. Evidence maturity

The current profile derives the strongest admitted maturity value:

```text
none < design < mechanism < internal_pilot < comparative_pilot < external_replication
```

This ladder is a profile policy for the shipped software-research engine, not a universal ordering of all evidence. Other domains may require different evidence types or admission policies.

A working mechanism may raise maturity to `mechanism`; it does not change a scientific conclusion.

### 3. Scientific conclusion

The current profile uses:

```text
not_tested | supported | falsified | inconclusive
```

A conclusion changes only when a `scientific` evidence artifact:

- is `qualified = true`;
- is `preregistered = true`;
- carries an outcome other than `not_tested`.

Outcome-bearing artifacts that fail this gate are **quarantined**: they remain visible but cannot change maturity or conclusion.

This qualified-plus-preregistered gate is the current profile's admission policy. Obey it exactly when operating the shipped CLI. Do not present it as the only legitimate epistemology for every research domain.

```text
capability != evidence maturity != scientific conclusion
```

## Skill versus deterministic CLI

Use the CLI for mechanical derivation. Use the skill for analysis, modeling, integration, and structural repair.

| CLI: deterministic | Skill: judgment |
| --- | --- |
| `hypothesize sync` — derive and write configured targets | Extract and normalize hypotheses |
| `hypothesize check` — derive without writing; fail on stale targets | Identify consequences, defeaters, alternatives, and evidence links |
| `hypothesize doctor` — diagnose without writing | Install or adopt the project profile |
| `hypothesize adopt` — inspect compatibility without changing generated files | Add adapters, targets, CI, schema migrations, or repair traceability |

If the user only wants an existing status regenerated, direct them to `hypothesize sync` or the project's equivalent make target. Do not hand-edit generated regions or manifests.

## CLI contract

- **`hypothesize sync`** — read configuration, acceptance reports, and evidence; derive status; write every configured target.
- **`hypothesize check`** — perform the same derivation without writing and exit non-zero when committed targets are stale.
- **`hypothesize doctor`** — report untracked tags, orphaned registry entries, quarantined outcomes, and missing or stale targets without writing.
- **`hypothesize adopt`** — inspect an existing repository and report registry, traceability, publication, and CI compatibility without changing generated files.

## Software-project workflows

Each structural workflow ends by running the CLI to prove that the wiring works. Never establish a status by hand.

### Install a new project

1. Analyze the project's claims before modeling them. Separate hypotheses from capabilities, requirements, observations, and decisions.
2. Create the registry from `templates/portfolio.toml` at the configured `catalog` path, normally `research/portfolio.toml`.
3. Register stable hypotheses and capabilities. Add studies and limitations only when the project uses them.
4. Treat `requirements` as passive normative metadata or references. Prefer linking to an external norms system such as Promisify when one exists; the current engine validates and republishes requirements but does not derive or enforce their gate status.
5. Add `[tool.hypothesize]` configuration to `pyproject.toml` or a standalone `hypothesize.toml`.
6. Tag acceptance scenarios for each capability. See `templates/capability.feature` and `references/tag-vocabulary.md`.
7. Optionally seed the evidence directory from `templates/evidence.toml`.
8. Run `hypothesize sync`, commit generated targets, then run `hypothesize check`; it must pass.
9. Add CI from `templates/ci-github.yml` and make targets from `templates/Makefile.snippet`.

### Adopt an existing project

Follow `references/adoption.md`.

1. Freeze the current generated outputs.
2. Point configuration at the existing registry, evidence, acceptance report, and publication targets.
3. Run `hypothesize adopt`; expect a compatible result before changing the model.
4. Run `hypothesize check`.
5. The success condition is byte-for-byte preservation of existing generated publication during adoption.

Do not use adoption as an opportunity to improve, reinterpret, or promote the project's claims.

### Add pytest or behave integration

Set `[tool.hypothesize.runner].adapter` to `behave` or `pytest` and point `report` at the runner's JSON report. Ensure each capability tag resolves to a registered capability. Re-run `sync`, then `check`.

### Add a publication target

Append a `[[tool.hypothesize.targets]]` block with kind `json`, `markdown_region`, or `js`.

For a Markdown region, create the fence before running `sync`:

```html
<!-- BEGIN GENERATED: research-status -->
<!-- END GENERATED: research-status -->
```

Use `render = "use_cases"` or another supported projection when the target should not use the default hypothesis table.

### Add CI enforcement

Run the acceptance suite to produce its JSON report, then run `hypothesize check`. Broken traceability and stale generated output must fail CI.

### Migrate a schema version

1. Update the registry schema version.
2. Run `hypothesize doctor` to surface incompatibilities.
3. Migrate source entries rather than generated targets.
4. Run `sync`, inspect shape changes, commit, and run `check`.

### Repair broken traceability

For an untracked `@hyp_*` or `@cap_*` tag, register the intended object or correct the tag. Never delete a meaningful check merely to make publication pass.

For an orphaned capability, determine whether:

- scenarios are missing;
- work is explicitly specified but skipped;
- the capability is obsolete;
- the object was registered aspirationally without an executable contract.

Do not automatically add `@wip` merely to suppress the diagnostic. Record the actual state.

### Explain a status

Read the manifest, registry, linked scenarios, evidence artifacts, and previous manifest where regression matters. Explain each dimension independently.

Examples:

- A hypothesis remains `not_tested` because no admitted scientific result has passed the profile gate.
- A capability is `partial` because some required scenarios pass and others do not.
- An outcome is quarantined because it is not both qualified and preregistered.
- A conclusion applies to an earlier subject revision and should not be transferred without new evidence.

Never answer a status question by editing the generated value.

## Configuration contract

Use these keys exactly in `pyproject.toml` or `hypothesize.toml`.

```toml
[tool.hypothesize]
catalog = "research/portfolio.toml"
evidence_dir = "research/evidence"

[tool.hypothesize.runner]
adapter = "behave"
report = "artifacts/research/behave.json"

[tool.hypothesize.evidence]
collector = "mypkg.research:collect_evidence"

[[tool.hypothesize.targets]]
kind = "json"
path = "research/generated/research-status.json"

[[tool.hypothesize.targets]]
kind = "markdown_region"
path = "README.md"
marker = "research-status"

[[tool.hypothesize.targets]]
kind = "markdown_region"
path = "use-cases/README.md"
marker = "use-case-status"
render = "use_cases"

[[tool.hypothesize.targets]]
kind = "js"
path = "site/generated/research-data.js"
variable = "RESEARCH_STATUS"
```

## Registry contract

The current registry supports stable-ID object families. See `templates/portfolio.toml`.

- **`hypotheses`** — empirical propositions. `tag` maps test tags to stable `HYP-*` IDs. The current profile changes conclusions only through admitted scientific results.
- **`capabilities`** — bounded implementation behaviors linked to `CAP-*` tags and optionally to hypotheses they inform.
- **`requirements`** — passive normative metadata linked to capabilities or hypotheses. The engine validates references and republishes these records; it does not currently compute whether a requirement gate passes. Do not claim enforcement that does not exist.
- **`studies`** — evidence-producing designs with profile-specific qualification and preregistration fields.
- **`limitations`** — explicit reasons conclusions remain restricted, uncertain, or non-transferable.
- **`tracks`** and **`use_cases`** — optional groupings and projections when present in an adopted portfolio.

Evidence artifacts may come from `evidence_dir` or a configured collector. They carry stable identity, linked hypotheses, kind, maturity, qualification, preregistration, outcome, source, and summary.

The registry and evidence records are authoritative inputs to the generated publication. They are not themselves authoritative descriptions of reality.

## Tag contract

See `references/tag-vocabulary.md` for complete details.

### Traceability tags

- `@hyp_*` links a scenario to a registered hypothesis.
- `@cap_*` links a scenario to a registered capability.

Every used link tag must resolve, or publication fails.

### Evidence-role tags

- `@evidence_capability` — bounded implementation behavior; no maturity or conclusion change.
- `@evidence_mechanism` — a bounded mechanism demonstration; may raise maturity to `mechanism`; no conclusion change.
- `@evidence_scientific_contract` — tests the evidence workflow itself; capability effect only.

There is never a `@hypothesis_supported`, `@validated`, or equivalent result tag. Scientific status is derived from evidence records, not asserted in test text.

### Control tags

- `@clean_control`
- `@negative_control`
- `@adversarial`
- `@synthetic_fixture`
- `@independence_required`
- `@wip`

`@wip` means the scenario is skipped and the behavior has not been demonstrated. Describe it as a declared or specified capability, not as a promise.

### Requirement-strength tags

`@must`, `@should`, and `@may` may be retained as project metadata. The current engine does not derive requirement-gate outcomes from them. Do not imply that these tags enforce release policy unless another consumer does so.

## Software-profile transition rules

| Input class | Capability status | Evidence maturity | Scientific conclusion |
| --- | --- | --- | --- |
| Tagged scenario passes, fails, or is skipped | May set it | No direct effect unless an evidence role applies | No effect |
| `@evidence_capability` scenario | Confirms bounded behavior | No bump | No effect |
| `@evidence_mechanism` scenario or mechanism artifact | No effect beyond linked capability | May raise to `mechanism` | No effect |
| Study-design artifact | No effect | May raise to `design` | No effect |
| `@evidence_scientific_contract` scenario | Confirms workflow capability | No bump | No effect |
| Outcome artifact failing the profile gate | No effect | No effect | Quarantined |
| Qualified, preregistered scientific outcome | No effect | No effect | May set `supported`, `falsified`, or `inconclusive` |

The final row is the only route by which the current CLI changes a scientific conclusion.

## Determinism and staleness

The manifest's `build.source_hash` is derived from the registry, evidence, acceptance report, previous state, and supplied results. Identical inputs produce byte-identical outputs.

A target is stale when re-derivation differs from committed bytes. `hypothesize check` detects this without writing. `hypothesize sync` is the writing operation. CI should use `check`.

## Success criteria

A good use of this skill leaves the user with clearer uncertainty, not merely more structure.

- Important assertions are visible as hypotheses rather than smuggled in as facts.
- Non-hypotheses remain correctly typed.
- Conditions, alternatives, consequences, and possible defeat are explicit where the evidence permits.
- Evidence is linked without overstating relevance or transfer.
- The host tool retains ownership of its model.
- The chosen profile is explicit rather than treated as universal epistemology.
- Generated status is reproducible and traceable.
- Unknowns and disagreements remain visible.

## Reference material

- `references/publication-model.md` — current software-profile derivation, maturity, quarantine, source hash, and manifest.
- `references/adoption.md` — adoption workflow and compatibility checks.
- `references/tag-vocabulary.md` — acceptance-suite tags and evidence roles.
- `templates/` — starter portfolio, evidence, capability, CI, and Makefile files.
