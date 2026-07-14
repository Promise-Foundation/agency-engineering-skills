"""Load ``[tool.hypothesize]`` from pyproject.toml or a standalone hypothesize.toml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    import tomli as tomllib  # type: ignore[no-redef]


class ConfigError(ValueError):
    """The hypothesize configuration is missing or malformed."""


@dataclass
class Target:
    kind: str  # "json" | "markdown_region" | "js"
    path: str
    marker: Optional[str] = None
    render: str = "hypotheses"  # "hypotheses" | "use_cases"
    variable: Optional[str] = None


@dataclass
class Config:
    root: Path
    catalog: str = "research/portfolio.toml"
    evidence_dir: Optional[str] = None
    adapter: str = "behave"
    report: str = "artifacts/research/behave.json"
    collector: Optional[str] = None
    targets: "list[Target]" = field(default_factory=list)

    # convenience absolute paths
    def catalog_path(self) -> Path:
        return self.root / self.catalog

    def report_path(self) -> Path:
        return self.root / self.report

    def generated_json_target(self) -> Optional[Target]:
        for target in self.targets:
            if target.kind == "json":
                return target
        return None


def _read_toml(path: Path) -> "dict[str, Any]":
    with path.open("rb") as handle:
        return tomllib.load(handle)


def find_config(root: Path) -> "dict[str, Any]":
    """Return the ``[tool.hypothesize]`` table from the repo, or raise."""
    hypothesize_toml = root / "hypothesize.toml"
    if hypothesize_toml.exists():
        return _read_toml(hypothesize_toml)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        data = _read_toml(pyproject)
        tool = data.get("tool", {})
        if "hypothesize" in tool:
            return tool["hypothesize"]
    raise ConfigError(
        "no hypothesize configuration found "
        "(expected hypothesize.toml or [tool.hypothesize] in pyproject.toml)"
    )


def load_config(root: "str | Path") -> Config:
    root_path = Path(root).resolve()
    table = find_config(root_path)
    runner = table.get("runner", {})
    evidence = table.get("evidence", {})
    targets = [
        Target(
            kind=str(entry["kind"]),
            path=str(entry["path"]),
            marker=entry.get("marker"),
            render=str(entry.get("render", "hypotheses")),
            variable=entry.get("variable"),
        )
        for entry in table.get("targets", [])
    ]
    return Config(
        root=root_path,
        catalog=str(table.get("catalog", "research/portfolio.toml")),
        evidence_dir=table.get("evidence_dir"),
        adapter=str(runner.get("adapter", "behave")),
        report=str(runner.get("report", "artifacts/research/behave.json")),
        collector=evidence.get("collector"),
        targets=targets,
    )
