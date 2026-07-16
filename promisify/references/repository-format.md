# Repository format

## Canonical layout

```text
.norms/
├── repository.yaml
├── promises/
│   └── <domain segments>/_<promise_name>.yaml
├── assessments/
│   └── <assessor>/<timestamp-or-id>.yaml
├── views/
│   └── <trust-view-name>.yaml
└── reports/
    └── <generated reports; optional>
```

`reports/` is derived output and should normally be ignored by version control unless reports are audit artifacts the team intentionally preserves.

## Repository descriptor

`.norms/repository.yaml` identifies format version and roots. Copy `assets/templates/repository.yaml`.

It may also explicitly register domains and the repository-relative subjects
they describe. This lets Promisify publish a domain even before that domain has
its own promise, and gives downstream skills a stable scope to analyze:

```yaml
spec:
  domains:
    - path: /skills/hypothesize
      subjects: [hypothesize]
    - path: /skills/zpd
      subjects: [zpd]
```

Domain registration does not declare a promise or imply a verdict. It only
connects a normative namespace to the body of work it names.

## Promise files

A promise file contains one `Promise` document. File placement mirrors `metadata.domain`; the filename equals `metadata.name` plus `.yaml`.

Required semantic fields:

- `metadata.domain`
- `metadata.name`
- `spec.statement`

For executable coding norms, include a structured `spec.criteria` block or precise assessment instructions. Criteria define what would count as evidence; they do not contain a verdict.

## Assessment files

Assessment files are append-only observations. Grouping by assessor keeps provenance visible, but the `metadata.assessor` field is authoritative.

A filename should be unique and sortable, for example:

```text
2026-07-15T101500Z-pydantic-customer.yaml
```

## Trust views

Trust view files describe observer-relative selection and scoring policy. A view can be reused across domains if `spec.domain` is updated explicitly or the tooling supports a domain override.

## Trust reports

Reports are generated from promises, assessments, and a view. A report must identify all inputs and policies needed to reproduce it.

## YAML conventions

- UTF-8.
- Two-space indentation.
- ISO 8601 UTC timestamps.
- Repository revisions should use full commit hashes when available.
- Paths are repository-relative with `/` separators.
- Do not store secrets or personal medical, legal, or personnel evidence in assessment records.
- Use stable actor identifiers such as `agent/static-analysis`, `team/architecture`, or `person/alice`, according to local policy.

## Schema mapping

| Kind | Schema |
|---|---|
| Repository | `assets/schemas/repository.schema.json` |
| Promise | `assets/schemas/promise.schema.json` |
| Assessment | `assets/schemas/assessment.schema.json` |
| TrustView | `assets/schemas/trust-view.schema.json` |
| TrustReport | `assets/schemas/trust-report.schema.json` |

## Minimum viable repository

```text
.norms/
├── repository.yaml
├── promises/
└── views/
    └── default.yaml
```

Assessments are added only when observations exist.
