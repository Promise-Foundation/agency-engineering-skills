# Adoption playbook

How to bring `hypothesize` into a repo — especially one that **already** implements this pattern by hand (a bespoke `research`/status module, a portfolio file, tagged tests, a committed status JSON). The governing principle:

> The portfolio, evidence, and linked tests are the **source of truth**. The package only **derives**. CI **enforces**. The skill **installs, migrates, and maintains**. The package must not be the source of any truth it publishes.

Adoption succeeds when the package can reproduce the existing published status without being told what the answer is.

## The right success test

**Adopt an existing implementation and leave its publication unchanged.** If `hypothesize` is wired correctly against a repo that already has a hand-rolled version of this pattern, then `hypothesize check` must pass with **zero** changes to the generated targets — the committed status JSON, the README region, and any JS data file stay byte-for-byte identical. If adoption *changes* the published status, one of two things is true and both must be fixed before proceeding:

1. The config points at the wrong inputs (registry, evidence, or report), so the derivation differs — fix the config, not the output.
2. The existing hand-published status was itself wrong — surface this to the user explicitly as a finding; do **not** silently "correct" it during adoption.

Never make the published status "look better" as part of adopting. Adoption is a fidelity test, not an opportunity to improve the numbers.

## Extraction sequence

1. **Freeze current outputs.** Note the exact paths and current contents of the existing published artifacts (status JSON, README/doc regions, JS data file). These are the fixtures the adoption must reproduce. If they are not committed, commit them first so `check` has something to compare against.
2. **Point config at them.** Add `[tool.hypothesize]` to `pyproject.toml` (or a `hypothesize.toml`) with:
   - `catalog` -> the existing registry file (do not rewrite it).
   - `evidence_dir` and/or `[tool.hypothesize.evidence].collector` -> the existing evidence source.
   - `[tool.hypothesize.runner]` `adapter` + `report` -> the existing acceptance report (behave JSON or a pytest JSON report).
   - One `[[tool.hypothesize.targets]]` per existing published artifact, at its current path (and for markdown regions, the existing `marker`).
3. **`hypothesize adopt`.** It inspects the repo and reports what exists — registry, test traceability, publication targets, CI enforcement — and whether installation is **compatible**. It writes nothing. Read its report; resolve anything it flags as incompatible (usually a config path pointing at the wrong file, or an untracked tag).
4. **`hypothesize check`.** With config pointing at frozen outputs, `check` must report the targets are **current** and exit zero — i.e. re-deriving reproduces the committed bytes. This is the success test above. If it fails, diff the re-derived output against the committed output to find whether the discrepancy is a config error (fix config) or a latent bug in the old hand-rolled status (surface to the user).
5. **Optionally re-export the engine from the consumer.** If the consumer had its own bespoke module (e.g. a `mypkg.research` CLI), you can now have it re-export or thin-wrap `hypothesize` so there is a single derivation implementation. This is optional and comes *after* `check` is green — never before. The bespoke entry point can delegate to the package while keeping its existing command name for muscle memory and CI.
6. **Hand off regeneration to the CLI + CI.** Wire `make research-status` / `make research-check` (see `templates/Makefile.snippet`) and the CI job (`templates/ci-github.yml`) so `sync` is how humans regenerate and `check` is how CI enforces. From here the skill steps back; ongoing regeneration is not a skill task.

## Division of responsibility

| Concern | Owner |
| --- | --- |
| What the hypotheses/capabilities/requirements/studies/limitations are | The registry (`catalog`) — human-authored |
| What evidence exists and its qualified/preregistered/outcome status | Evidence artifacts / collector — human-authored |
| Which behaviors are proven | The tagged acceptance suite |
| Turning those inputs into a status | The `hypothesize` engine (deterministic) |
| Keeping the published status honest over time | CI running `hypothesize check` |
| Installing, adopting, extending, migrating, repairing the wiring | This skill |
| Ordinary regeneration | `hypothesize sync` / `check`, run by devs and CI — **not** the skill |

## What adoption must never do

- Never edit a generated target by hand to make `check` pass — fix the inputs or the config.
- Never change a published capability status, maturity, or conclusion as a side effect of wiring the tool.
- Never treat the package as authoritative over the registry — if they disagree, the registry (and the tests/evidence it points to) wins, and the disagreement is a finding to report.
- Never adopt on top of untracked tags. Resolve traceability first (`doctor`), because publication fails on unregistered `@hyp_*`/`@cap_*` tags anyway.
