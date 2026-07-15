# Assessments

## Meaning

An assessment is a claim with provenance:

```text
Assessor A judges promise P, effective in domain D,
at snapshot S, with verdict V, based on evidence E.
```

It is not an intrinsic property of the promise.

## Verdicts

### `kept`

The assessor believes the promise is fulfilled in the stated effective domain and subject scope at the stated snapshot.

### `broken`

The assessor believes the promise is not fulfilled in the stated effective domain and subject scope at the stated snapshot.

### `unknown`

The assessor cannot determine kept or broken from available evidence. Unknown is not success.

### `not_applicable`

The promise is effective by domain inheritance but has no applicable subject or circumstance in the assessed scope. Use sparingly and explain why.

### `disputed`

A derived or explicit assessment state indicating unresolved incompatible claims. Individual assessors should normally emit their own kept, broken, unknown, or not-applicable assessments; a resolver may derive disputed.

## Assessment identity

Assessment records require a unique ID. A practical logical key for deduplication is:

```text
promise + effectiveDomain + subject + assessor + revision + observedAt
```

Do not overwrite an older assessment merely because a newer one exists.

## Evidence

Evidence entries should be small, reviewable references:

```yaml
evidence:
  - kind: source
    path: src/models/customer.py
    lines: 10-22
    summary: Customer inherits from object rather than pydantic.BaseModel.
  - kind: command
    command: python -m pytest tests/models/test_customer.py
    exitCode: 1
    summary: Validation test failed.
```

Avoid embedding large logs. Store a path or artifact reference plus a concise summary.

## Repository revision

For code assessments, record the exact commit hash when possible. If the worktree is dirty, record both the base revision and a dirty-worktree marker or content hash. Trust reports should not casually combine assessments from incompatible revisions.

## Multiple subjects

A promise can apply to many concrete subjects. Version 1 supports two patterns:

1. **Domain-level assessment**: the assessor evaluates the promise over the entire target domain and emits one verdict.
2. **Subject-level assessments**: the assessor emits records for individual subjects, and a named policy later aggregates them to a domain-level verdict.

The default trust calculation counts resolved effective promises, not raw subject records. Therefore subject records need an explicit aggregation policy before contributing to trust.

## Conflicting assessments

Preserve all claims. A trust view chooses a conflict policy such as:

- `unknown-on-conflict`: disagreement becomes unscorable;
- `latest`: latest accepted assessment wins;
- `majority`: verdict with the most accepted assessor votes wins, ties unresolved;
- `conservative`: any accepted broken verdict yields broken; otherwise kept if at least one kept and none broken;
- `all`: do not reduce claims to one verdict; intended for reports, not scalar trust.

No policy is globally correct. The chosen policy must be visible in the trust view and report.

## Confidence

Confidence is optional and never a substitute for evidence. Version 1 does not weight trust by confidence unless a future extension declares that policy.

## Assessment lifecycle

1. Resolve promise and target domain.
2. Fix the snapshot.
3. Gather evidence.
4. State subject scope.
5. Emit verdict and rationale.
6. Validate record.
7. Append it without mutating the promise or prior assessments.
