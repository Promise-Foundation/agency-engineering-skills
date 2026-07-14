# ltp

A reusable engine + CLI that reconstructs the logic implicit in a project as
**one validated Theory-of-Constraints model** and enforces its logical validity.

The six Logical Thinking Processes -- Goal Tree, Current Reality Tree, Evaporating
Cloud, Future Reality Tree, Prerequisite Tree, Transition Tree -- are *views* of a
single typed model, derived deterministically. They cannot drift apart, and the
model cannot silently violate the Categories of Legitimate Reservation:

- The model is **typed**. Every node has a kind from a closed vocabulary; every
  relationship is a *typed claim* (necessity or compound sufficiency), never a
  generic arrow.
- Logic is **validated, not asserted**. `ltp validate` runs the CLR and the
  structural rules of each tree and emits coded diagnostics (`GT-004`, `EC-008`,
  `CRT-006`, ...). The engine verifies the review was done and represented
  honestly; it never decides causality for you.
- The model is the **only authored artifact**. Documents, Mermaid diagrams, and
  dashboard data are generated; `ltp check` fails if any committed file is stale
  or hand-edited.

See [`SKILL.md`](SKILL.md) for the agent-facing workflows and
[`references/`](references/) for the model vocabulary, the logical-scrutiny model,
the staged workflow, and the diagnostic-code catalog.

## Install

```bash
python3 -m pip install -e .        # provides the `ltp` command
```

The model layer is pure standard library; PyYAML is the only runtime dependency.

## Use

```bash
ltp init            # scaffold ltp/ltp-model.yaml
ltp validate        # run the CLR + structural rules; print coded diagnostics
ltp sync            # validate, then write every generated projection
ltp check           # CI gate: fail on staleness or invalidity
ltp doctor          # diagnose without writing
ltp migrate --write # convert a v1 permissive model to v2, preserving ids
ltp explain CLM-17  # evidence, assumptions, CLR, and dependents for one record
```

Explore the result locally (read-only):

```bash
ltp sync && python scripts/serve_dashboard.py --project . --open
```

## Develop

```bash
PYTHONPATH=src python3 -m pytest -q        # engine + validator + golden tests
python3 -m ltp.schema --check              # schema / TS types / diagnostics are current
python3 evals/build_fixtures.py            # regenerate + self-check the eval fixtures
npm --prefix dashboard ci && npm --prefix dashboard run build
```

The suite includes fixture-driven validator tests (valid models must be
publishable; each invalid model must raise its planted diagnostic) and a
byte-for-byte golden render test.
