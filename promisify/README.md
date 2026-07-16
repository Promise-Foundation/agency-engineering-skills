# Promisify Agent Skill

A portable Agent Skills package for representing norms and capacities as promises, assessments, and observer-relative trust views.

## Concept in one paragraph

A promise states what OUGHT to be true or what capacity is expected under stated conditions. It is canonically addressed by a hierarchical domain plus a local name, such as `/biology/botany/_relates_to_plants`, and is inherited by descendant domains. A promise never stores whether it is kept or broken. Assessments are attributable, evidence-backed claims about a type or concrete subject. A trust view preserves the full verdict vector and may include the version 1 baseline ratio `kept / (kept + broken)` with coverage and disagreement shown separately.

## Package contents

- `SKILL.md`: portable instructions loaded by Claude Code or Codex.
- `references/`: the complete ontology, repository protocol, assessment semantics, trust model, workflows, validation rules, and extension points.
- `assets/schemas/`: JSON Schemas for repository descriptors, promises, assessments, trust views, and trust reports.
- `assets/templates/`: copy-ready YAML and agent-instruction snippets.
- `examples/`: a small working `.norms/` repository.
- `scripts/norms.py`: validation, effective-promise resolution, and trust calculation.
- `evals/`: trigger and workflow cases for iterating on the skill.
- `SECURITY.md`: execution and evidence safety boundaries.
- `MAINTAINING.md`: versioning, evaluation, and release checklist.

## Install for Codex

From the repository root:

```bash
mkdir -p .agents/skills
cp -R /path/to/promisify .agents/skills/promisify
```

Codex discovers repository skills under `.agents/skills` from the working directory up to the repository root.

Optionally copy `assets/templates/AGENTS.md.snippet` into the repository's `AGENTS.md`.

## Install for Claude Code

From the repository root:

```bash
mkdir -p .claude/skills
cp -R /path/to/promisify .claude/skills/promisify
```

Optionally copy `assets/templates/CLAUDE.md.snippet` into `CLAUDE.md`. If the project already uses `AGENTS.md`, Claude Code can import it from `CLAUDE.md` with `@AGENTS.md`.

## Install once for both

Keep one canonical copy and link the other:

```bash
mkdir -p .agents/skills .claude/skills
cp -R /path/to/promisify .agents/skills/promisify
ln -s ../../.agents/skills/promisify .claude/skills/promisify
```

On Windows, copy the directory twice or create a directory junction if symlinks are unavailable.

## Validate the included example

```bash
python -m pip install -r scripts/requirements.txt
python scripts/norms.py validate examples
python scripts/norms.py effective examples /biology/botany/bryology
python scripts/norms.py trust examples --view default
```

## Typical prompts

- "Represent the rule that domain model classes under `/software/python/models` ought to use Pydantic."
- "Assess every promise effective in `/software/python/models` at the current commit."
- "Calculate trust for `/biology/botany` from the default view and show coverage."
- "Repair the broken promises in `/software/python`, reassess them, and show the trust delta."

## Version

Ontology and file format: `norms/v1`  
Skill package: `0.1.0`

## Automated local installation

```bash
./scripts/install.sh --both /path/to/repository
```
