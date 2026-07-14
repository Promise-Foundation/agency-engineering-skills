"""Orchestration: turn a project's configuration into a publication result."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    import tomli as tomllib  # type: ignore[no-redef]

from .adapters import behave as behave_adapter
from .adapters import pytest as pytest_adapter
from .collector import EvidenceBundle, load_collector, load_evidence_dir
from .config import Config, ConfigError
from .core import ResearchStatusService

_ADAPTERS = {
    "behave": behave_adapter.load_scenarios,
    "pytest": pytest_adapter.load_scenarios,
}


def load_catalog(path: Path) -> "dict[str, Any]":
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_scenarios(config: Config, catalog: "dict[str, Any]") -> "list[dict[str, Any]]":
    if config.adapter not in _ADAPTERS:
        raise ConfigError(f"unknown runner adapter {config.adapter!r}")
    report = config.report_path()
    if not report.exists():
        raise ConfigError(
            f"acceptance report not found: {report} "
            f"(run the {config.adapter} suite first)"
        )
    return _ADAPTERS[config.adapter](report, catalog)


def collect_evidence(config: Config) -> EvidenceBundle:
    evidence: "list[dict[str, Any]]" = []
    results: Optional["dict[str, Any]"] = None
    if config.evidence_dir:
        evidence.extend(load_evidence_dir(config.root / config.evidence_dir))
    if config.collector:
        bundle = load_collector(config.collector)
        evidence.extend(bundle.evidence)
        results = bundle.results
    return EvidenceBundle(evidence=evidence, results=results)


def previous_projection(config: Config) -> Optional["dict[str, Any]"]:
    target = config.generated_json_target()
    if target is None:
        return None
    path = config.root / target.path
    if not path.exists():
        return None
    previous = json.loads(path.read_text(encoding="utf-8"))
    return {
        "hypotheses": [
            {"id": item["id"], "conclusion": item["conclusion"]}
            for item in previous.get("hypotheses", [])
        ],
        "capabilities": [
            {"id": item["id"], "status": item["status"]}
            for item in previous.get("capabilities", [])
        ],
    }


def build_publication(config: Config) -> "dict[str, Any]":
    catalog = load_catalog(config.catalog_path())
    scenarios = load_scenarios(config, catalog)
    bundle = collect_evidence(config)
    return ResearchStatusService().publish(
        catalog=catalog,
        scenarios=scenarios,
        evidence=bundle.evidence,
        previous=previous_projection(config),
        results=bundle.results,
    )
