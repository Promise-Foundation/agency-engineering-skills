"""The ``hypothesize`` command line: sync, check, doctor, adopt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .adapters import TraceabilityError
from .config import ConfigError, load_config
from .core import ResearchStatusError
from .publish import build_publication, collect_evidence, load_catalog, load_scenarios
from .targets import stale_targets, target_files, write_targets


def _cmd_sync(root: Path) -> int:
    config = load_config(root)
    if not config.targets:
        print("no targets configured", file=sys.stderr)
        return 0
    # The scientific conclusion and regression state carry forward from the
    # previously published projection, so the projection is a fixed point rather
    # than a one-shot output. Iterate until writing changes nothing (at most a
    # couple of passes); graphist's already-committed publication converges on
    # the first pass with no write.
    changed: "list[Path]" = []
    for _ in range(5):
        publication = build_publication(config)
        if not stale_targets(config, publication):
            break
        changed = write_targets(config, publication)
    else:
        print("warning: research status did not converge", file=sys.stderr)
    for path in changed:
        print(f"wrote {path.relative_to(config.root)}")
    if not changed:
        print("already current")
    return 0


def _cmd_check(root: Path) -> int:
    config = load_config(root)
    publication = build_publication(config)
    stale = stale_targets(config, publication)
    if stale:
        for path in stale:
            print(f"stale generated file: {path.relative_to(config.root)}", file=sys.stderr)
        print("run `hypothesize sync` to regenerate", file=sys.stderr)
        return 2
    print("generated research publication is current")
    return 0


def _cmd_doctor(root: Path) -> int:
    config = load_config(root)
    catalog = load_catalog(config.catalog_path())
    problems: "list[str]" = []
    notes: "list[str]" = []

    try:
        scenarios = load_scenarios(config, catalog)
    except (TraceabilityError, ConfigError) as error:
        problems.append(f"traceability: {error}")
        scenarios = []

    # Registry entries exercised by no scenario.
    linked_caps = {cap for item in scenarios for cap in item.get("capabilities", [])}
    linked_hyps = {hyp for item in scenarios for hyp in item.get("hypotheses", [])}
    for capability in catalog.get("capabilities", []):
        if capability["id"] not in linked_caps:
            notes.append(f"capability {capability['id']} has no linked scenarios (specified)")
    for hypothesis in catalog.get("hypotheses", []):
        if hypothesis["id"] not in linked_hyps:
            notes.append(f"hypothesis {hypothesis['id']} has no linked scenarios")

    # Evidence that would be quarantined.
    bundle = collect_evidence(config)
    for item in bundle.evidence:
        if (
            item.get("kind") == "scientific"
            and item.get("outcome") not in (None, "not_tested")
            and not (item.get("qualified") and item.get("preregistered"))
        ):
            problems.append(
                f"evidence {item.get('id')} reports {item.get('outcome')} but is not "
                "qualified+preregistered (will be quarantined)"
            )

    # Staleness of committed targets.
    try:
        publication = build_publication(config)
        for path in stale_targets(config, publication):
            problems.append(f"stale target: {path.relative_to(config.root)}")
    except (ResearchStatusError, ConfigError, ValueError) as error:
        problems.append(f"publication: {error}")

    for note in notes:
        print(f"note: {note}")
    for problem in problems:
        print(f"problem: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("doctor: no problems found")
    return 0


def _cmd_adopt(root: Path) -> int:
    root = root.resolve()
    print(f"Inspecting {root} for an existing hypothesize-compatible setup...\n")
    findings: "list[tuple[str, bool, str]]" = []

    # Configuration.
    try:
        config = load_config(root)
        findings.append(("configuration", True, "found [tool.hypothesize]"))
    except ConfigError:
        config = None
        findings.append(("configuration", False, "no [tool.hypothesize] / hypothesize.toml"))

    # Registry.
    catalog_rel = config.catalog if config else "research/portfolio.toml"
    catalog_path = root / catalog_rel
    findings.append(
        ("hypothesis registry", catalog_path.exists(), str(catalog_rel))
    )

    # Test traceability (a report from the configured adapter).
    if config:
        report = config.report_path()
        findings.append(
            (f"{config.adapter} traceability report", report.exists(), str(config.report))
        )
        for target in config.targets:
            path = root / target.path
            findings.append((f"target ({target.kind})", path.exists(), target.path))

    # CI enforcement.
    ci_dir = root / ".github" / "workflows"
    ci_enforces = False
    if ci_dir.is_dir():
        for workflow in ci_dir.glob("*.y*ml"):
            text = workflow.read_text(encoding="utf-8", errors="ignore")
            if "hypothesize check" in text or "research-check" in text:
                ci_enforces = True
                break
    findings.append(("CI enforcement", ci_enforces, "hypothesize check / research-check"))

    for name, present, detail in findings:
        mark = "found" if present else "missing"
        print(f"  [{mark:>7}] {name}: {detail}")

    if config is None or not catalog_path.exists():
        print("\nNot yet installed. Run the skill's install workflow to scaffold it.")
        return 0

    # Compatibility: can we derive without changing committed files?
    try:
        publication = build_publication(config)
        stale = stale_targets(config, publication)
    except (ResearchStatusError, ConfigError, ValueError, TraceabilityError) as error:
        print(f"\nInstallation is present but not yet compatible: {error}")
        return 1

    if stale:
        print("\nInstallation is present; regenerating would change:")
        for path in stale:
            print(f"  - {path.relative_to(root)}")
        print("Run `hypothesize sync` to reconcile, then commit.")
        return 0

    print("\nInstallation is compatible. No generated files would change.")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hypothesize",
        description="Derive and publish an honest, machine-readable research status.",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("sync", help="derive status and write all configured targets")
    sub.add_parser("check", help="fail if any committed target is stale (for CI)")
    sub.add_parser("doctor", help="diagnose traceability and publication problems")
    sub.add_parser("adopt", help="inspect an existing setup; change nothing")
    args = parser.parse_args(argv)

    handlers = {
        "sync": _cmd_sync,
        "check": _cmd_check,
        "doctor": _cmd_doctor,
        "adopt": _cmd_adopt,
    }
    try:
        return handlers[args.command](args.root)
    except (ResearchStatusError, ConfigError, TraceabilityError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
