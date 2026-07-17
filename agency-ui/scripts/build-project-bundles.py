#!/usr/bin/env python3
"""Assemble the LTP and Hypothesize multi-domain artifact bundles.

Both `ltp-plugin` and `hypothesize-plugin` already read a bundle shaped
`{"artifacts": [{"domain": ..., "manifest": ...}, ...]}` -- this script is the
one generator for both files. It never re-derives anything: it only reads
files each project's own `ltp sync` / `hypothesize sync` already produced
(`ltp/generated/dashboard-model.json`, `research/generated/research-status.json`,
or this repository's own `self-model/generated/...` and `research/generated/...`)
and republishes them, namespaced per project, exactly as `ltp-plugin` and
`hypothesize-plugin` already expect. No plugin code changes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = REPOSITORY_ROOT / "agency-ui"
CONTENT_SOURCES_PATH = UI_ROOT / "content-sources.json"

LTP_BUNDLE_PATH = UI_ROOT / "apps/web/public/api/ltp/artifacts.json"
HYPOTHESIZE_BUNDLE_PATH = UI_ROOT / "apps/web/public/api/hypothesize/artifacts.json"

PROJECTS_DOMAIN = "/projects"


def load_json(path: Path) -> "dict[str, Any] | None":
    if not path.exists():
        print(f"  skip: {path} does not exist", file=sys.stderr)
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_bundle(entries: "list[tuple[str, Path]]") -> dict[str, Any]:
    artifacts = []
    for domain, manifest_path in entries:
        manifest = load_json(manifest_path)
        if manifest is None:
            continue
        artifacts.append({"domain": domain, "manifest": manifest})
    return {"schemaVersion": 1, "artifacts": artifacts}


def write_bundle(path: Path, bundle: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(REPOSITORY_ROOT)} ({len(bundle['artifacts'])} artifact(s))")


def main() -> int:
    sources = []
    if CONTENT_SOURCES_PATH.exists():
        sources = json.loads(CONTENT_SOURCES_PATH.read_text(encoding="utf-8"))

    ltp_entries: "list[tuple[str, Path]]" = [
        ("/", REPOSITORY_ROOT / "self-model/generated/dashboard-model.json"),
    ]
    hypothesize_entries: "list[tuple[str, Path]]" = [
        ("/", REPOSITORY_ROOT / "research/generated/research-status.json"),
    ]

    for source in sources:
        project_id, path = source["id"], source["path"]
        repository = (UI_ROOT / path).resolve()
        domain = f"{PROJECTS_DOMAIN}/{project_id}"
        ltp_entries.append((domain, repository / "ltp/generated/dashboard-model.json"))
        hypothesize_entries.append((domain, repository / "research/generated/research-status.json"))

    write_bundle(LTP_BUNDLE_PATH, build_bundle(ltp_entries))
    write_bundle(HYPOTHESIZE_BUNDLE_PATH, build_bundle(hypothesize_entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
