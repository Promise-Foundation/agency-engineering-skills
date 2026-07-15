# agency-engineering-skills
Agentic Coding Skills for Agency Engineering

## Skills

- [`hypothesize/`](hypothesize/SKILL.md) — derive an honest, machine-readable research
  status (capability vs. evidence vs. scientific conclusion) from tagged acceptance tests
  and an evidence registry; deterministic `hypothesize sync | check | doctor | adopt` CLI.
- [`ltp/`](ltp/SKILL.md) — reconstruct the logic implicit in a repository as one
  evidence-backed Theory-of-Constraints model (Goal Tree, Current/Future Reality Tree,
  Evaporating Cloud, Prerequisite Tree, Transition Tree) and enforce its logical validity
  with a deterministic `ltp validate | render | sync | check | doctor | migrate | explain`
  CLI. The model is the single source of truth; documents, diagrams, and the dashboard are
  generated projections.

## Interface

- [`agency-ui/`](agency-ui/README.md) — a read-only shell that hosts the skills as
  **plugins** over a shared `ResourceSource` contract. Skills contribute routes, cards,
  resource views, and cross-skill relations without importing each other (an LTP claim is
  `VERIFIED_BY` a hypothesis); the seams for mutable data are built in, so a live/writable
  skill (ZPD) hosts on the same shell with zero shell changes.
