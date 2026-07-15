# Maintaining the skill

## Design target

Keep `SKILL.md` as the compact operational entrypoint. Put detailed semantics in one-level-deep reference files and deterministic behavior in scripts.

## Versioning

- Increment the skill package version in `SKILL.md` metadata and `CHANGELOG.md` for instruction, example, or tooling changes.
- Change `apiVersion` only for incompatible repository-format or ontology changes.
- Preserve old schemas when migrations are needed.

## Evaluation loop

1. Run the trigger cases in `evals/trigger-cases.yaml` against both Claude Code and Codex.
2. Confirm should-trigger prompts activate the skill and should-not-trigger prompts do not.
3. Run each workflow case in `evals/workflow-cases.yaml` in a disposable repository.
4. Inspect the agent trace, not only its final answer.
5. Add concrete gotchas when the agent makes a repeatable mistake.
6. Keep the main skill under 500 lines and move conditional detail into references.

## Deterministic checks

```bash
python -m pip install -r scripts/requirements.txt
python -m py_compile scripts/norms.py
python scripts/norms.py validate examples
python scripts/norms.py effective examples /biology/botany/bryology
python scripts/norms.py trust examples --view default
python scripts/norms.py trust examples --view human-only
```

Expected trust results:

- `default`: score `1.0`, coverage `0.5`, one disputed promise.
- `human-only`: score `1.0`, coverage `1.0`, no disputed promises.

## Review checklist

- Promise objects remain free of status and trust fields.
- Inheritance preserves canonical identity.
- Assessments remain attributable and append-only.
- Trust reports remain reproducible and observer-relative.
- New policy choices are explicit rather than silently made universal.
- Example files validate against the bundled schemas.
- Platform-specific additions do not break portability under the Agent Skills standard.
