# hypothesize

A reusable engine + CLI that derives one honest, machine-readable **research
status** for a project by keeping three usually-conflated dimensions apart:

- **Capability** — what the code demonstrably does, from tagged acceptance tests.
- **Evidence maturity** — the strongest admitted evidence artifact.
- **Scientific conclusion** — changed only by a qualified, preregistered result.

A passing test can raise a capability to `implemented`; it can never promote a
hypothesis. Unqualified outcome-bearing artifacts are quarantined. Output is
deterministic and CI-checkable.

See [`SKILL.md`](SKILL.md) for the agent-facing workflows and
[`references/`](references/) for the epistemic model, tag vocabulary, and
adoption playbook.

## Install

```bash
python3 -m pip install -e .        # provides the `hypothesize` command
```

## Use

Configure `[tool.hypothesize]` in your `pyproject.toml` (or a `hypothesize.toml`)
pointing at your portfolio, acceptance report, and publication targets, then:

```bash
hypothesize sync      # regenerate all publication targets (README table, JSON, ...)
hypothesize check     # CI gate: fail if any committed target is stale
hypothesize doctor    # diagnose traceability and publication problems
hypothesize adopt     # inspect an existing setup; change nothing
```

## Develop

```bash
PYTHONPATH=src python3 -m pytest -q
```

The suite includes a backward-compatibility golden test proving the engine
reproduces the Graphist project's committed publication byte-for-byte.
