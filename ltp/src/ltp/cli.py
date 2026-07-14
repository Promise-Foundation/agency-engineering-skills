"""The ``ltp`` command line.

    ltp init        scaffold a starter model
    ltp validate    check logical validity; print coded diagnostics
    ltp render      write every generated projection
    ltp sync        validate, then write projections (refuses on errors)
    ltp check       re-derive in memory; fail on staleness or invalidity (CI)
    ltp doctor      diagnose without writing
    ltp migrate     convert a v1 model to v2, preserving ids
    ltp explain ID  show evidence, assumptions, CLR, and dependents for one record

The CLI is the deterministic half; the skill (SKILL.md) is the judgment half.
Developers and CI run ``sync``/``check``; the skill proposes and repairs meaning.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .errors import LtpError
from .migrate import migrate_dict, needs_migration
from .models import LtpModel, ModelIndex, to_dict
from .provenance import source_hash
from .renderers import render_all
from .store import (
    Workspace,
    dump_model,
    load_model,
    locate,
    save_model,
    stale_generated,
    write_generated,
    yaml_load,
)
from .validators import validate

_STARTER = """\
schema_version: 2
project:
  name: {name}
  analysis_mode: forward
  provisional_goal: G-1
analysis_plan:
  mode: diagnose
  goal_tree: {{status: required}}
  current_reality_tree: {{status: deferred, reason: add UDEs and causes next}}
entities:
  - id: G-1
    kind: goal
    statement: State the system's ultimate purpose here
    basis: provisional
  - id: CSF-1
    kind: critical_success_factor
    statement: A condition that must hold for the goal
    satisfaction_criterion: How you would observe this holds
  - id: NC-1
    kind: necessary_condition
    statement: A condition necessary for CSF-1
    satisfaction_criterion: How you would observe this holds
necessity_claims:
  - id: NEC-1
    prerequisite: CSF-1
    objective: G-1
  - id: NEC-2
    prerequisite: NC-1
    objective: CSF-1
open_questions:
  - Replace this starter with the real goal, conditions, and evidence.
"""


def _workspace(args: argparse.Namespace) -> Workspace:
    return locate(args.root, model=getattr(args, "model", None))


def _print_diagnostics(report, *, stream=sys.stdout) -> None:
    for item in report.diagnostics:
        print(item.format(), file=stream)
    counts = report.counts
    print(
        f"\n{counts['error']} error(s), {counts['warning']} warning(s), "
        f"{counts['info']} info.",
        file=stream,
    )


# --------------------------------------------------------------------------- #
def cmd_init(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    if workspace.model_path.exists() and not args.force:
        print(f"{workspace.model_path} already exists (use --force to overwrite)", file=sys.stderr)
        return 2
    workspace.model_path.parent.mkdir(parents=True, exist_ok=True)
    name = args.name or workspace.home.parent.name or "New project"
    workspace.model_path.write_text(_STARTER.format(name=name), encoding="utf-8")
    # Prove the starter is valid.
    load_model(workspace.model_path)
    print(f"wrote {workspace.model_path}")
    print("edit it, then run `ltp validate` and `ltp sync`.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    model = load_model(workspace.model_path)
    report = validate(model)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_diagnostics(report)
    if report.errors:
        return 1
    if args.strict and report.warnings:
        print("strict: warnings present", file=sys.stderr)
        return 1
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    model = load_model(workspace.model_path)
    files = render_all(model)
    written = write_generated(workspace, files)
    for path in written:
        print(f"wrote {path.relative_to(workspace.home)}")
    if not written:
        print("already current")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    model = load_model(workspace.model_path)
    report = validate(model)
    if report.errors and not args.force:
        _print_diagnostics(report, stream=sys.stderr)
        print(
            "\nrefusing to publish an invalid model; fix the errors above or pass "
            "--force to write anyway",
            file=sys.stderr,
        )
        return 2
    files = render_all(model, report)
    written = write_generated(workspace, files)
    for path in written:
        print(f"wrote {path.relative_to(workspace.home)}")
    if not written:
        print("already current")
    warnings = report.counts["warning"]
    print(f"synced ({warnings} warning(s) remain)")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    model = load_model(workspace.model_path)
    report = validate(model)
    files = render_all(model, report)
    stale = stale_generated(workspace, files)
    problems = False
    if report.errors:
        problems = True
        print(f"model is invalid: {len(report.errors)} error(s)", file=sys.stderr)
    for path in stale:
        problems = True
        print(f"stale generated file: {path.relative_to(workspace.home)}", file=sys.stderr)
    if problems:
        print("run `ltp sync` to regenerate", file=sys.stderr)
        return 2
    print("generated projections are current and the model is valid")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    model = load_model(workspace.model_path)
    report = validate(model)
    _print_diagnostics(report)
    # Staleness is a doctor concern too, but doctor never writes.
    try:
        stale = stale_generated(workspace, render_all(model, report))
    except LtpError:
        stale = []
    for path in stale:
        print(f"note: stale generated file: {path.relative_to(workspace.home)}")
    return 1 if report.errors else 0


def cmd_migrate(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    if not workspace.model_path.exists():
        print(f"model not found: {workspace.model_path}", file=sys.stderr)
        return 2
    raw = yaml_load(workspace.model_path.read_text(encoding="utf-8")) or {}
    if not needs_migration(raw):
        print("model is already v2; nothing to migrate")
        return 0
    migrated = migrate_dict(raw)
    model = LtpModel.from_dict(migrated)  # prove it parses
    if args.write:
        backup = workspace.model_path.with_suffix(workspace.model_path.suffix + ".v1.bak")
        backup.write_text(workspace.model_path.read_text(encoding="utf-8"), encoding="utf-8")
        save_model(workspace.model_path, model)
        print(f"backed up v1 to {backup.name}")
        print(f"wrote v2 model to {workspace.model_path}")
        report = validate(model)
        print(
            f"migrated model has {report.counts['error']} error(s), "
            f"{report.counts['warning']} warning(s) -- run `ltp validate` and repair"
        )
    else:
        print(dump_model(model))
        print("# (dry run; pass --write to replace the model, backing up the v1 file)", file=sys.stderr)
    return 0


def _dependents(model: LtpModel, target: str) -> "list[str]":
    hits: "list[str]" = []
    for claim in model.necessity_claims:
        if target in (claim.prerequisite, claim.objective) or target in claim.assumption_refs:
            hits.append(f"necessity_claim {claim.id}")
    for claim in model.causal_claims:
        if target == claim.conclusion or target in claim.premises or target in claim.assumption_refs:
            hits.append(f"causal_claim {claim.id}")
    for cloud in model.clouds:
        roles = [cloud.objective, cloud.need_b, cloud.need_c, cloud.action_d, cloud.action_d_prime]
        if target in roles or target in cloud.injection_refs:
            hits.append(f"cloud {cloud.id}")
    for res in model.obstacle_resolutions:
        if target in (res.obstacle, res.intermediate_objective):
            hits.append(f"obstacle_resolution {res.id}")
    for transition in model.transitions:
        fields = [
            transition.action, transition.advances, transition.existing_reality,
            transition.need, transition.immediate_effect,
        ] + list(transition.precondition_refs)
        if target in fields:
            hits.append(f"transition {transition.id}")
    for pred in model.predicted_effects:
        if target == pred.source_claim:
            hits.append(f"predicted_effect {pred.id}")
    return hits


def cmd_hypotheses(args: argparse.Namespace) -> int:
    from .integrations import hypothesize

    workspace = _workspace(args)
    model = load_model(workspace.model_path)
    if args.action == "export":
        print(json.dumps(hypothesize.export_links(model), indent=2, sort_keys=True))
        return 0
    # check
    known: "Optional[set[str]]" = None
    if args.catalog:
        try:
            import tomllib  # Python 3.11+
        except ModuleNotFoundError:  # pragma: no cover
            print("--catalog needs Python 3.11+ (tomllib)", file=sys.stderr)
            return 2
        data = tomllib.loads(Path(args.catalog).read_text(encoding="utf-8"))
        known = {h["id"] for h in data.get("hypotheses", [])}
    problems = hypothesize.check_links(model, known)
    links = hypothesize.export_links(model)
    print(f"{len(links)} verification link(s)")
    for problem in problems:
        print(f"problem: {problem}", file=sys.stderr)
    if known is None:
        print("note: pass --catalog <portfolio.toml> to resolve hypothesis refs")
    return 1 if problems else 0


def cmd_evidence(args: argparse.Namespace) -> int:
    from .integrations import hypothesize

    workspace = _workspace(args)
    model = load_model(workspace.model_path)
    changes = hypothesize.import_evidence(model, Path(args.path))
    for change in changes:
        print(change)
    if not changes:
        print("no changes")
        return 0
    if args.write:
        save_model(workspace.model_path, model)
        print(f"wrote {workspace.model_path}")
    else:
        print("# (dry run; pass --write to update the model)", file=sys.stderr)
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    model = load_model(workspace.model_path)
    index = ModelIndex(model)
    target = args.id
    record = index.any_record(target)
    if record is None:
        print(f"no record with id {target!r}", file=sys.stderr)
        return 2
    print(f"# {target}\n")
    print(json.dumps(to_dict(record, prune=True), indent=2, sort_keys=True))

    if target in index.entities:
        entity = index.entities[target]
        if entity.evidence_refs:
            print("\n## Evidence")
            for ref in entity.evidence_refs:
                ev = index.evidence.get(ref)
                print(f"- {ref}: {ev.observation if ev else '(missing)'}")
        if entity.assumption_refs:
            print("\n## Assumptions")
            for ref in entity.assumption_refs:
                asm = index.entities.get(ref)
                print(f"- {ref}: {asm.statement if asm else '(missing)'}")

    if target in index.causal_claims and index.causal_claims[target].clr is not None:
        print("\n## CLR review")
        for name, check in index.causal_claims[target].clr.checks().items():
            print(f"- {name}: {check.result.value}" + (f" -- {check.reservation}" if check.reservation else ""))

    dependents = _dependents(model, target)
    print("\n## Referenced by")
    for hit in dependents:
        print(f"- {hit}")
    if not dependents:
        print("- (nothing)")

    report = validate(model)
    related = [d for d in report.diagnostics if d.target == target]
    if related:
        print("\n## Diagnostics")
        for item in related:
            print(f"- {item.format().strip()}")
    return 0


# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ltp", description="Logical Thinking Processes engine.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (holds ltp/)")
    parser.add_argument("--model", type=Path, default=None, help="explicit path to ltp-model.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="scaffold a starter model")
    p_init.add_argument("--name", default=None)
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_validate = sub.add_parser("validate", help="check logical validity")
    p_validate.add_argument("--strict", action="store_true", help="fail on warnings too")
    p_validate.add_argument("--json", action="store_true")
    p_validate.set_defaults(func=cmd_validate)

    sub.add_parser("render", help="write generated projections").set_defaults(func=cmd_render)
    p_sync = sub.add_parser("sync", help="validate then write projections")
    p_sync.add_argument("--force", action="store_true", help="write even if invalid")
    p_sync.set_defaults(func=cmd_sync)
    sub.add_parser("check", help="fail on staleness or invalidity (CI)").set_defaults(func=cmd_check)
    sub.add_parser("doctor", help="diagnose without writing").set_defaults(func=cmd_doctor)

    p_migrate = sub.add_parser("migrate", help="convert a v1 model to v2")
    p_migrate.add_argument("--write", action="store_true", help="replace the model (backs up v1)")
    p_migrate.set_defaults(func=cmd_migrate)

    p_explain = sub.add_parser("explain", help="explain one record by id")
    p_explain.add_argument("id")
    p_explain.set_defaults(func=cmd_explain)

    p_hyp = sub.add_parser("hypotheses", help="hypothesize bridge: export | check")
    p_hyp.add_argument("action", choices=["export", "check"])
    p_hyp.add_argument("--catalog", default=None, help="hypothesize portfolio.toml to resolve refs")
    p_hyp.set_defaults(func=cmd_hypotheses)

    p_ev = sub.add_parser("evidence", help="hypothesize bridge: import a research-status.json")
    p_ev.add_argument("action", choices=["import"])
    p_ev.add_argument("path", help="path to hypothesize research-status.json")
    p_ev.add_argument("--write", action="store_true", help="update the model in place")
    p_ev.set_defaults(func=cmd_evidence)

    return parser


def main(argv: "Optional[list[str]]" = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except LtpError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
