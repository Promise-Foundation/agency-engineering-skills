#!/usr/bin/env python3
"""Publish Promisify's shared domain context without deriving host skill models.

LTP and Hypothesize own and publish their own domain-addressed artifacts. This
builder deliberately does not convert promises into LTP necessary conditions or
hypotheses. Future exporters may persist plugin `promiseTypes` contributions as
Promisify subdomains while preserving the host object's identity and meaning.

In addition to this repository's own normative model, this builder folds in
each project listed in `content-sources.json` as a sibling domain rooted at
`/projects/<id>`, by re-running the same `norms.py explorer` command against
that project's own `.norms/` tree and re-prefixing every domain-path-bearing
field. The promisify-plugin itself is untouched: it still just reads one
`explorer.json`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = REPOSITORY_ROOT / "agency-ui"
EXPLORER_PATH = UI_ROOT / "apps/web/public/api/promisify/explorer.json"
PROMISIFY_CLI = REPOSITORY_ROOT / "promisify/scripts/norms.py"
CONTENT_SOURCES_PATH = UI_ROOT / "content-sources.json"

PROJECTS_DOMAIN = "/projects"


def run_explorer(repository: Path) -> dict[str, Any]:
    """Validate `repository` and return its parsed `norms.py explorer` output."""
    subprocess.run(
        [sys.executable, str(PROMISIFY_CLI), "validate", str(repository)],
        check=True,
    )
    result = subprocess.run(
        [sys.executable, str(PROMISIFY_CLI), "explorer", str(repository)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def remap_path(value: "str | None", prefix: str) -> "str | None":
    """Re-root a domain path or promise address under `prefix`.

    A promise address is always `domain + "/" + name` (or `"/" + name` when
    `domain == "/"`), so the same string-prepend rule that re-roots a domain
    path also re-roots an address built from it -- both are handled by one
    function.
    """
    if value is None:
        return None
    if value == "/":
        return prefix
    return prefix + value


def remap_project(explorer: dict[str, Any], project_id: str) -> dict[str, Any]:
    """Re-root every domain-path-bearing field in `explorer` under `/projects/<id>`."""
    prefix = f"{PROJECTS_DOMAIN}/{project_id}"

    domains = []
    for domain in explorer.get("domains", []):
        old_domain, old_parent = domain["domain"], domain["parent"]
        domains.append(
            {
                **domain,
                "domain": remap_path(old_domain, prefix),
                # The project's own root (parent None) is re-parented onto the
                # synthetic /projects node instead of being remapped, since it
                # had no real parent to begin with.
                "parent": PROJECTS_DOMAIN if old_parent is None else remap_path(old_parent, prefix),
                "children": [remap_path(child, prefix) for child in domain["children"]],
            }
        )

    effective = {
        remap_path(domain, prefix): [
            {
                **entry,
                "promise": remap_path(entry["promise"], prefix),
                "declaredAt": remap_path(entry["declaredAt"], prefix),
            }
            for entry in entries
        ]
        for domain, entries in explorer.get("effective", {}).items()
    }

    promises = [
        {
            **promise,
            "address": remap_path(promise["address"], prefix),
            "domain": remap_path(promise["domain"], prefix),
        }
        for promise in explorer.get("promises", [])
    ]

    assessments = [
        {
            **assessment,
            "id": f"{project_id}:{assessment['id']}" if assessment.get("id") else assessment.get("id"),
            "promise": remap_path(assessment["promise"], prefix),
            "effectiveDomain": remap_path(assessment["effectiveDomain"], prefix),
        }
        for assessment in explorer.get("assessments", [])
    ]

    views = [
        {**view, "domain": remap_path(view["domain"], prefix)}
        for view in explorer.get("views", [])
    ]

    trust = [
        {
            **entry,
            "domain": remap_path(entry["domain"], prefix),
            "selectedAssessmentIds": [f"{project_id}:{aid}" for aid in entry.get("selectedAssessmentIds", [])],
            "unresolved": [remap_path(address, prefix) for address in entry.get("unresolved", [])],
            "results": [
                {
                    **result,
                    "promise": remap_path(result["promise"], prefix),
                    "assessmentIds": [f"{project_id}:{aid}" for aid in result.get("assessmentIds", [])],
                }
                for result in entry.get("results", [])
            ],
        }
        for entry in explorer.get("trust", [])
    ]

    return {
        "domains": domains,
        "effective": effective,
        "promises": promises,
        "assessments": assessments,
        "views": views,
        "trust": trust,
    }


def merge_external_projects(merged: dict[str, Any]) -> None:
    if not CONTENT_SOURCES_PATH.exists():
        return
    sources = json.loads(CONTENT_SOURCES_PATH.read_text(encoding="utf-8"))

    project_domain_names = []
    for source in sources:
        project_id, path = source["id"], source["path"]
        repository = (UI_ROOT / path).resolve()
        print(f"processing external project '{project_id}' at {repository}")
        explorer = run_explorer(repository)
        remapped = remap_project(explorer, project_id)

        merged["domains"].extend(remapped["domains"])
        merged["effective"].update(remapped["effective"])
        merged["promises"].extend(remapped["promises"])
        merged["assessments"].extend(remapped["assessments"])
        merged["views"].extend(remapped["views"])
        merged["trust"].extend(remapped["trust"])
        project_domain_names.append(f"{PROJECTS_DOMAIN}/{project_id}")

    if not project_domain_names:
        return

    merged["domains"].append(
        {
            "domain": PROJECTS_DOMAIN,
            "parent": "/",
            "depth": 1,
            "children": sorted(project_domain_names),
            "subjects": [],
            "declaredCount": 0,
            "effectivePromiseCount": 0,
        }
    )
    for domain in merged["domains"]:
        if domain["domain"] == "/":
            domain["children"] = sorted({*domain["children"], PROJECTS_DOMAIN})


def main() -> int:
    merged = run_explorer(REPOSITORY_ROOT)
    merge_external_projects(merged)

    EXPLORER_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPLORER_PATH.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"wrote {EXPLORER_PATH.relative_to(REPOSITORY_ROOT)}")
    print("LTP and Hypothesize artifacts remain owned by their generators")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
