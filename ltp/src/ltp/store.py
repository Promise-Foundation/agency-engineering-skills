"""Load and save the model, and read/write the generated tree.

Conventional layout inside a target project::

    <project>/ltp/ltp-model.yaml        # the one authored source of truth
    <project>/ltp/generated/            # everything ltp writes (never hand-edited)
      00-coverage-and-evidence.md ...
      diagrams/*.mmd
      dashboard-model.json
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from .errors import ModelError
from .models import LtpModel, parse_model, to_dict

HOME_DIRNAME = "ltp"
MODEL_FILENAME = "ltp-model.yaml"


class _NoTimestampLoader(yaml.SafeLoader):
    """SafeLoader that leaves ISO timestamps as strings.

    The model treats every value as authored text; a field like
    ``updated_at: 2026-07-12T14:32:00Z`` should round-trip as the string it was
    written as, not become a ``datetime`` the typed model would reject.
    """


_NoTimestampLoader.yaml_implicit_resolvers = {
    first_char: [
        (tag, regexp)
        for tag, regexp in resolvers
        if tag != "tag:yaml.org,2002:timestamp"
    ]
    for first_char, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def yaml_load(text: str) -> Any:
    """Parse YAML with timestamps kept as strings."""
    return yaml.load(text, Loader=_NoTimestampLoader)


@dataclass(frozen=True)
class Workspace:
    home: Path  # directory that holds ltp-model.yaml (usually <project>/ltp)
    model_path: Path

    @property
    def generated(self) -> Path:
        return self.home / "generated"


def locate(root: "str | Path", *, model: "Optional[str | Path]" = None) -> Workspace:
    """Find the workspace for a project root, or an explicit model path."""
    if model is not None:
        model_path = Path(model).expanduser().resolve()
        return Workspace(home=model_path.parent, model_path=model_path)
    root_path = Path(root).expanduser().resolve()
    # Accept either <root>/ltp/ltp-model.yaml or <root>/ltp-model.yaml.
    for candidate in (root_path / HOME_DIRNAME / MODEL_FILENAME, root_path / MODEL_FILENAME):
        if candidate.exists():
            return Workspace(home=candidate.parent, model_path=candidate)
    # Default (creation) location.
    home = root_path / HOME_DIRNAME
    return Workspace(home=home, model_path=home / MODEL_FILENAME)


def load_model(path: "str | Path") -> LtpModel:
    file_path = Path(path)
    if not file_path.exists():
        raise ModelError(f"model not found: {file_path}")
    try:
        raw = yaml_load(file_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ModelError(f"{file_path}: invalid YAML: {error}") from error
    if raw is None:
        raise ModelError(f"{file_path}: model is empty")
    try:
        return parse_model(raw)
    except ModelError as error:
        raise ModelError(f"{file_path}: {error}") from error


def dump_model(model: LtpModel) -> str:
    """Serialize to compact, deterministic, human-readable YAML (defaults pruned)."""
    data = to_dict(model, prune=True)
    data.setdefault("schema_version", model.schema_version)
    return yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=100,
    )


def save_model(path: "str | Path", model: LtpModel) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(dump_model(model), encoding="utf-8")


def write_generated(workspace: Workspace, files: "dict[str, str]") -> "list[Path]":
    written: "list[Path]" = []
    for relpath, content in files.items():
        target = workspace.home / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            target.write_text(content, encoding="utf-8")
            written.append(target)
    return written


def stale_generated(workspace: Workspace, files: "dict[str, str]") -> "list[Path]":
    stale: "list[Path]" = []
    for relpath, content in files.items():
        target = workspace.home / relpath
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            stale.append(target)
    return stale
