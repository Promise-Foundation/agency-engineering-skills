# Trust model

## Principle

A domain has no single objective trust score. A trust result is always relative to:

```text
trust(domain, observer, accepted assessments, resolution policy, snapshot)
```

## Version 1 baseline ratio

After resolving one scorable verdict for each effective promise in the target domain:

```text
score = kept / (kept + broken)
```

Exclude `unknown`, `not_applicable`, and unresolved `disputed` verdicts from the denominator by default.

When `kept + broken == 0`, return `score: null`.

This ratio is the simplest demonstration of an observer-relative trust view. It
is already more informative than a flat reputation score because the underlying
promise dimensions, domains, verdicts, evidence, disagreement, and coverage
remain inspectable. It is not an adequate general model of trust.

Equal weighting allows trivial promises to outnumber a critical broken promise.
Excluding disputes can raise the ratio even while uncertainty increases. For
those reasons, never publish the scalar alone, rank domains by it alone, or use
it as an authorization decision without an explicit consumer policy.

## Coverage

A scalar score without coverage is misleading. Default coverage is:

```text
coverage = (kept + broken) / relevant
```

where `relevant` is the number of effective promises after excluding promises resolved as `not_applicable`.

Unresolved disputes and unknowns remain relevant but unscored, reducing coverage.

Example:

```text
kept = 7
broken = 2
unknown = 3
not_applicable = 1
disputed = 0

score = 7 / 9 = 0.7778
coverage = 9 / 12 = 0.75
```

## Default scoring unit

Version 1 defaults to one resolved verdict per effective promise in the target domain.

This matches the question: what proportion of applicable promises does the observer believe are kept?

Subject-level assessments do not enter the denominator directly unless the view declares a subject aggregation rule that produces a promise-level verdict.

## Observer and assessor

- **Assessor**: makes an evidence-backed claim.
- **Observer**: defines which assessment claims are accepted and how disagreements are handled.

The same actor may fill both roles, but the fields remain separate.

## Snapshot policy

A trust view should prefer assessments tied to the same repository revision. Default behavior:

1. If `spec.snapshot.revision` is set, accept only matching assessments.
2. If no revision is set, select the newest assessment per accepted assessor and effective promise, while clearly labeling the report as cross-time and potentially non-reproducible.
3. Never mix historical kept and current broken verdicts as separate promises.

## Selection pipeline

1. Resolve effective promises.
2. Filter assessments to those promises and the target domain.
3. Filter by snapshot.
4. Filter by accepted assessors.
5. Select one latest record per assessor and promise.
6. Resolve across assessors using the conflict policy.
7. Count resolved verdicts.
8. Compute score and coverage.
9. Emit a reproducible report with selected assessment IDs.

## Comparing trust

Only compare scores when the following are compatible or differences are explicitly discussed:

- target domain;
- effective promise set;
- observer;
- accepted assessors;
- conflict policy;
- snapshot;
- scoring unit;
- weighting policy;
- coverage.

A rise in score caused by lower coverage is not necessarily an improvement.

Every presentation must retain the promise-by-promise verdict vector and call
out broken and disputed promises. Coverage is a separate dimension, not a
confidence decoration on the score.

## Weighting

Version 1's default is equal weight per effective promise. Weighted, severity-aware,
and decision-specific trust are planned extension policies, not intrinsic promise
truth. A future view may map promise addresses or tags to weights, but reports
must include the mapping and must preserve the unweighted vector.

## Staleness

An assessment is current only for the subject revision or digest it identifies.
A revision-pinned view excludes nonmatching assessments. An unpinned view may
select the newest claim for exploration, but must label the result cross-time and
potentially stale. Consumers must not treat that exploratory result as current
authorization. Automatic digest comparison and expiry windows remain planned
policies; until implemented, re-assess after a material subject change.

## Generated report requirements

Every trust report includes:

- target domain;
- observer;
- snapshot;
- score and coverage;
- kept, broken, unknown, not-applicable, and disputed counts;
- effective promise count;
- selection and conflict policy;
- selected assessment IDs;
- unresolved conflicts;
- generation time and tool version.
