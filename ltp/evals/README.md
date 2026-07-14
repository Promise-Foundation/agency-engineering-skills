# Evals

Two layers, both checked by `pytest` from the skill root.

## Deterministic validator fixtures

`fixtures/valid/` and `fixtures/invalid/` each hold `ltp-model.yaml` + an
`expected.yaml` listing the diagnostic codes the model must produce. `test_validators.py`
loads each fixture, runs `ltp validate`, and asserts:

- **valid** fixtures are publishable (zero errors);
- **invalid** fixtures raise their planted `expected_errors` / `expected_warnings`.

Each invalid fixture isolates one planted defect (a reversed causal claim, a
collapsed Cloud, a compound transition, a root cause labelled a constraint, ...),
so a diagnostic firing means the engine caught exactly that defect.

The fixtures are generated -- and self-checked -- by `build_fixtures.py` from one
pristine base model, so a defect is the only difference from a clean model:

```bash
python evals/build_fixtures.py     # regenerate + self-check
```

The committed YAML (not the generator) is what the tests read.

## Golden render snapshot

`../tests/golden/` holds a byte-for-byte snapshot of the generated tree for the
`compound-cause` fixture. `test_renderers.py` proves identical inputs produce
identical documents, diagrams, and dashboard data. Regenerate after an
intentional renderer change:

```bash
python tests/regen_golden.py
```

## Other fixtures

- `fixtures/v1/ltp-model.yaml` -- a v1 permissive model, used by `test_migrate.py`.
- `fixtures/dashboard/` -- a synced v2 project (`ltp-model.yaml` + `generated/`)
  the dashboard server serves in tests and demos.
