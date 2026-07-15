# Validation rules

## Structural validation

- `.norms/repository.yaml` exists when `.norms/` exists.
- Every YAML document has `apiVersion`, `kind`, `metadata`, and `spec` as required by its schema.
- `apiVersion` is `norms/v1`.
- Kind-specific schemas pass.

## Domain validation

- Domain is absolute and normalized.
- No trailing slash except root.
- No empty, `.` or `..` segments.
- Segment characters satisfy the schema.

## Promise validation

- Local name begins with `_`.
- Canonical address is unique.
- File path mirrors declaring domain.
- Filename equals local name.
- Promise has no status-like fields such as `status`, `verdict`, `kept`, `broken`, `trust`, or `score`.
- Statement expresses an OUGHT expectation.
- Criteria are assessable or a clear human-assessment procedure is given.

## Assessment validation

- Referenced promise exists.
- Effective domain is equal to or below the promise's declaring domain.
- Assessor, observed time, and verdict exist.
- Repository revision is present for code-state claims when git is available.
- Evidence is present for kept and broken verdicts unless explicitly justified.
- Assessment does not modify or duplicate promise fields as authoritative data.

## Trust-view validation

- Observer is explicit.
- Target domain is valid.
- Conflict policy is recognized.
- Scoring unit is explicit.
- Excluded verdicts are explicit.

## Trust-report validation

- Report identifies its view and input assessments.
- Counts reconcile with effective promise count.
- Score equals kept divided by kept plus broken within numeric tolerance.
- Coverage denominator and exclusions are reproducible.
- `score` is null when no scorable promises exist.

## Semantic warnings

Warnings do not invalidate the repository but require review:

- Promise declared at `/` has very broad reach.
- Same local name appears at ancestor and descendant domains.
- Conflicting accepted assessments exist.
- Trust score has low coverage.
- Assessment revision differs from requested snapshot.
- Promise has no source or authority.
- Criteria depend only on unstructured model judgment when deterministic evidence appears possible.
