# agency-engineering-skills
Agentic Coding Skills for Agency Engineering

## Skills

- [`promisify/`](promisify/SKILL.md) — represent norms and general capacities as
  hierarchical promises; keep declarations separate from attributable assessments and
  observer-relative trust views.
- [`hypothesize/`](hypothesize/SKILL.md) — derive an honest, machine-readable research
  status (capability vs. evidence vs. scientific conclusion) from tagged acceptance tests
  and an evidence registry; deterministic `hypothesize sync | check | doctor | adopt` CLI.
- [`ltp/`](ltp/SKILL.md) — reconstruct the logic implicit in a repository as one
  evidence-backed Theory-of-Constraints model (Goal Tree, Current/Future Reality Tree,
  Evaporating Cloud, Prerequisite Tree, Transition Tree) and enforce its logical validity
  with a deterministic `ltp validate | render | sync | check | doctor | migrate | explain`
  CLI. The model is the single source of truth; documents, diagrams, and the dashboard are
  generated projections.

## Composition

The skills form a federation, not a mandatory pipeline. Each shipped skill can run in
isolation. Promisify is the recommended shared context: before LTP or Hypothesize runs
without a current Promisify model, it offers to run Promisify first and continues if the
user declines. ZPD is specified with a hard Promisify dependency because its learner
model is defined in terms of capacity promises.

[`agency-engineering.yaml`](agency-engineering.yaml) is the machine-readable dependency
and maturity registry. `required`, `recommended`, and `optional` have the same meanings
in agent skills and UI plugin manifests.

## Interface

- [`agency-ui/`](agency-ui/README.md) — a prototype shell that hosts the skills as
  **plugins** over a shared `ResourceSource` contract. Skills contribute routes, cards,
  resource views, and cross-skill relations without importing each other (an LTP claim is
  `VERIFIED_BY` a hypothesis); the seams for mutable data are built in, so a live/writable
  skill (ZPD) hosts on the same shell with zero shell changes. Promisify publishes the
  domain hierarchy into the shared resource model; the shell keeps domain selection
  separate from skill selection so every skill view receives the same working context.

The shell demonstrates static and writable resource seams; it is not yet the evented,
permissioned, challenge-and-adjudication runtime described by Agency Engineering.
