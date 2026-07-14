"""Render every generated projection from one model.

``render_all`` returns a map of *relative path -> content* for the whole
``generated/`` tree: the ten Markdown documents, one Mermaid diagram per
non-empty view, and the normalized dashboard model. It is a pure function of the
model, which is what makes ``ltp check`` able to detect drift by re-rendering and
comparing.
"""

from __future__ import annotations

import json

from ..models import LtpModel
from ..provenance import GENERATOR, MARKDOWN_HEADER, MERMAID_HEADER, source_hash
from . import dashboard, markdown, mermaid

GENERATED_DIR = "generated"


def render_all(model: LtpModel, report=None) -> "dict[str, str]":
    if report is None:
        from ..validators import validate

        report = validate(model)

    files: "dict[str, str]" = {}
    for name, content in markdown.render_documents(model, report).items():
        files[f"{GENERATED_DIR}/{name}"] = MARKDOWN_HEADER + content
    for key, source in mermaid.render_diagrams(model).items():
        files[f"{GENERATED_DIR}/diagrams/{key}.mmd"] = MERMAID_HEADER + source

    dash = dashboard.build_dashboard(model, report)
    dash["build"] = {"source_hash": source_hash(model), "generator": GENERATOR}
    files[f"{GENERATED_DIR}/dashboard-model.json"] = (
        json.dumps(dash, indent=2, sort_keys=True) + "\n"
    )
    return files


__all__ = ["GENERATED_DIR", "render_all", "dashboard", "markdown", "mermaid"]
