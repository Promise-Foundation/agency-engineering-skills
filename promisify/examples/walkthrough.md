# Example walkthrough

## Effective promises

For `/biology/botany/bryology`, the effective set is:

```text
/biology/_concerns_living_systems
/biology/botany/_relates_to_plants
```

Both retain their declaration addresses.

## Default view

The default view accepts all assessors and uses `unknown-on-conflict`.

- `/biology/_concerns_living_systems`: kept.
- `/biology/botany/_relates_to_plants`: disputed because accepted assessors disagree.

Expected result:

```yaml
score: 1.0
coverage: 0.5
counts:
  kept: 1
  broken: 0
  unknown: 0
  not_applicable: 0
  disputed: 1
```

The high score is not strong evidence because coverage is only 50%.

## Human-only view

The human-only view accepts only `person/human-reviewer`.

Expected result:

```yaml
score: 1.0
coverage: 1.0
counts:
  kept: 2
  broken: 0
  unknown: 0
  not_applicable: 0
  disputed: 0
```

The difference between the reports is not a contradiction in the promises. It reflects different observer policies over assessment claims.
