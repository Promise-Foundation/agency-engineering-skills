"""Read Gherkin source as specified-only research traceability.

This adapter never executes a scenario and can never license implementation or
empirical evidence. It exists so planned ``@wip`` requirements can be matched to
registered capabilities and hypotheses before an executable suite exists.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import capability_tag_map, hypothesis_tag_map, resolve_scenario

_TAGS = re.compile(r"@[A-Za-z0-9_:-]+")
_FEATURE = re.compile(r"^\s*Feature:\s*(.+?)\s*$", re.IGNORECASE)
_SCENARIO = re.compile(r"^\s*Scenario(?: Outline)?:\s*(.+?)\s*$", re.IGNORECASE)


def _feature_paths(path: Path) -> "list[Path]":
    if path.is_dir():
        return sorted(path.rglob("*.feature"))
    if path.suffix == ".feature":
        return [path]
    raise ValueError("gherkin source must be a .feature file or directory")


def load_scenarios(
    report_path: "str | Path", catalog: Mapping[str, Any]
) -> "list[dict[str, Any]]":
    capability_tags = capability_tag_map(catalog)
    hypothesis_tags = hypothesis_tag_map(catalog)
    scenarios: "list[dict[str, Any]]" = []

    source = Path(report_path)
    location_root = source.parent
    for path in _feature_paths(source):
        pending_tags: "set[str]" = set()
        feature_tags: "set[str]" = set()
        feature_name = ""
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("@"):
                pending_tags.update(tag[1:] for tag in _TAGS.findall(stripped))
                continue
            feature_match = _FEATURE.match(line)
            if feature_match:
                feature_name = feature_match.group(1)
                feature_tags = set(pending_tags)
                pending_tags.clear()
                continue
            scenario_match = _SCENARIO.match(line)
            if scenario_match:
                name = scenario_match.group(1)
                tags = feature_tags | pending_tags
                pending_tags.clear()
                location = f"{path.relative_to(location_root)}:{line_number}"
                scenarios.append(
                    resolve_scenario(
                        tags=tags,
                        scenario_id=f"{location}::{name}",
                        name=name,
                        feature=feature_name,
                        location=location,
                        status="skipped" if "wip" in tags else "untested",
                        capability_tags=capability_tags,
                        hypothesis_tags=hypothesis_tags,
                    )
                )

    return scenarios
