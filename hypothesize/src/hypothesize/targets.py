"""Render and write publication targets from a publication result.

Byte-compatible with the hand-written Graphist and Uptake generators:

* ``json`` — ``json.dumps(manifest, indent=2, sort_keys=True)`` + trailing newline.
* ``markdown_region`` — replace the ``BEGIN/END GENERATED: <marker>`` block.
* ``js`` — ``window.<variable> = <compact sorted json with < escaped>;`` + newline.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .config import Config, Target


def _marker_bounds(marker: str) -> "tuple[str, str]":
    return (
        f"<!-- BEGIN GENERATED: {marker} -->",
        f"<!-- END GENERATED: {marker} -->",
    )


def _replace_region(text: str, marker: str, content: str) -> str:
    start, end = _marker_bounds(marker)
    if start not in text or end not in text:
        raise ValueError(f"document is missing generated markers {start} / {end}")
    prefix, remainder = text.split(start, 1)
    _, suffix = remainder.split(end, 1)
    return f"{prefix}{start}\n{content.rstrip()}\n{end}{suffix}"


def render_target(target: Target, root: Path, publication: Mapping[str, Any]) -> str:
    manifest = publication["manifest"]
    if target.kind == "json":
        return json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if target.kind == "js":
        variable = target.variable or "RESEARCH_STATUS"
        safe_json = json.dumps(manifest, sort_keys=True).replace("<", "\\u003c")
        return f"window.{variable} = {safe_json};\n"
    if target.kind == "markdown_region":
        if not target.marker:
            raise ValueError(f"markdown_region target {target.path} needs a marker")
        content = (
            publication["use_case_markdown"]
            if target.render == "use_cases"
            else publication["markdown"]
        )
        existing = (root / target.path).read_text(encoding="utf-8")
        return _replace_region(existing, target.marker, str(content))
    raise ValueError(f"unknown target kind {target.kind!r}")


def target_files(config: Config, publication: Mapping[str, Any]) -> "dict[Path, str]":
    """Map each configured target's absolute path to its rendered content."""
    files: "dict[Path, str]" = {}
    for target in config.targets:
        files[config.root / target.path] = render_target(target, config.root, publication)
    return files


def write_targets(config: Config, publication: Mapping[str, Any]) -> "list[Path]":
    files = target_files(config, publication)
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return list(files)


def stale_targets(config: Config, publication: Mapping[str, Any]) -> "list[Path]":
    stale: "list[Path]" = []
    for path, expected in target_files(config, publication).items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            stale.append(path)
    return stale
