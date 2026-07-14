"""Evidence collection: admitted evidence artifacts and run-derived results.

Evidence can come from two places, merged by the CLI:

* ``evidence_dir`` — a directory of ``*.toml`` files, each an ``[[evidence]]``
  array (or a single artifact table). Good for static, hand-authored evidence.
* a project ``collector`` — a ``"module:function"`` that returns an
  ``EvidenceBundle``. Good for evidence derived by running the project's own
  experiments, which a generic tool cannot know how to do.
"""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass
class EvidenceBundle:
    """What a project collector returns: admitted evidence and optional results.

    ``evidence`` is a list of artifact records the engine scores against
    hypotheses. ``results`` is an opaque map of raw run outputs echoed into the
    manifest for provenance; pass ``None`` to omit the ``results`` section.
    """

    evidence: "list[dict[str, Any]]" = field(default_factory=list)
    results: Optional["dict[str, Any]"] = None


def load_evidence_dir(directory: "str | Path") -> "list[dict[str, Any]]":
    path = Path(directory)
    evidence: "list[dict[str, Any]]" = []
    if not path.is_dir():
        return evidence
    for toml_path in sorted(path.glob("*.toml")):
        with toml_path.open("rb") as handle:
            document = tomllib.load(handle)
        entries = document.get("evidence")
        if isinstance(entries, list):
            evidence.extend(entries)
        elif document.get("id"):
            evidence.append(document)
    return evidence


def load_collector(spec: str) -> EvidenceBundle:
    """Import ``"module:function"``, call it, and coerce the result to a bundle."""
    if ":" not in spec:
        raise ValueError(f"collector must be 'module:function', got {spec!r}")
    module_name, function_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    function = getattr(module, function_name)
    result = function()
    if isinstance(result, EvidenceBundle):
        return result
    if isinstance(result, Mapping):
        return EvidenceBundle(
            evidence=list(result.get("evidence", [])),
            results=result.get("results"),
        )
    raise TypeError(f"collector {spec} must return an EvidenceBundle or mapping")
