"""Normalize a behave JSON report into the engine's scenario model."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import capability_tag_map, hypothesis_tag_map, resolve_scenario


def load_scenarios(
    report_path: "str | Path", catalog: Mapping[str, Any]
) -> "list[dict[str, Any]]":
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if not isinstance(report, list):
        raise ValueError("behave report must contain a JSON feature list")
    capability_tags = capability_tag_map(catalog)
    hypothesis_tags = hypothesis_tag_map(catalog)
    scenarios: "list[dict[str, Any]]" = []
    for feature in report:
        feature_tags = {str(tag) for tag in feature.get("tags", [])}
        for element in feature.get("elements", []):
            if element.get("type") not in {"scenario", "scenario_outline"}:
                continue
            tags = feature_tags | {str(tag) for tag in element.get("tags", [])}
            location = str(element.get("location", "unknown"))
            name = str(element.get("name", "unnamed scenario"))
            scenarios.append(
                resolve_scenario(
                    tags=tags,
                    scenario_id=f"{location}::{name}",
                    name=name,
                    feature=str(feature.get("name", "")),
                    location=location,
                    status=str(element.get("status", "untested")),
                    capability_tags=capability_tags,
                    hypothesis_tags=hypothesis_tags,
                )
            )
    return scenarios
