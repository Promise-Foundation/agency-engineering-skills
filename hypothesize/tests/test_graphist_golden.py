"""Backward-compatibility: the engine reproduces Graphist's committed publication.

Graphist is the golden fixture. Feeding its recovered inputs (portfolio, behave
report, admitted evidence, run results, and its own fixed-point projection) back
through the extracted engine must reproduce its committed manifest and every
projection byte-for-byte. This proves the extraction did not change the
semantics of a real, sophisticated portfolio.
"""

from __future__ import annotations

import json
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    import tomli as tomllib

import pytest

from hypothesize.adapters.behave import load_scenarios
from hypothesize.core import ResearchStatusService

FIXTURES = Path(__file__).parent / "fixtures" / "graphist"


@pytest.fixture(scope="module")
def publication():
    catalog = tomllib.loads((FIXTURES / "portfolio.toml").read_text(encoding="utf-8"))
    committed = json.loads((FIXTURES / "research-status.json").read_text(encoding="utf-8"))
    scenarios = load_scenarios(FIXTURES / "behave.json", catalog)
    previous = {
        "hypotheses": [
            {"id": h["id"], "conclusion": h["conclusion"]} for h in committed["hypotheses"]
        ],
        "capabilities": [
            {"id": c["id"], "status": c["status"]} for c in committed["capabilities"]
        ],
    }
    pub = ResearchStatusService().publish(
        catalog=catalog,
        scenarios=scenarios,
        evidence=committed["evidence"],
        previous=previous,
        results=committed.get("results"),
    )
    return pub, committed


def test_manifest_is_byte_identical(publication):
    pub, committed = publication
    got = json.dumps(pub["manifest"], sort_keys=True, indent=2)
    expected = json.dumps(committed, sort_keys=True, indent=2)
    assert got == expected


def test_readme_hypothesis_table_matches(publication):
    pub, _ = publication
    expected = (FIXTURES / "readme-block.md").read_text(encoding="utf-8").strip("\n")
    assert pub["markdown"].strip("\n") == expected


def test_use_case_table_matches(publication):
    pub, _ = publication
    text = (FIXTURES / "use-cases-README.md").read_text(encoding="utf-8")
    start = "<!-- BEGIN GENERATED: use-case-status -->"
    end = "<!-- END GENERATED: use-case-status -->"
    expected = text.split(start, 1)[1].split(end, 1)[0].strip("\n")
    assert pub["use_case_markdown"].strip("\n") == expected


def test_website_js_matches(publication):
    pub, _ = publication
    expected = (FIXTURES / "research-data.js").read_text(encoding="utf-8")
    safe = json.dumps(pub["manifest"], sort_keys=True).replace("<", "\\u003c")
    assert f"window.GRAPHIST_RESEARCH_STATUS = {safe};\n" == expected
