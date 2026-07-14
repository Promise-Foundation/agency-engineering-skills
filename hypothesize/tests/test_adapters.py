"""Adapter tests: behave and pytest reports normalize to one scenario model."""

from __future__ import annotations

import json

import pytest

from hypothesize.adapters import TraceabilityError
from hypothesize.adapters.behave import load_scenarios as load_behave
from hypothesize.adapters.pytest import load_scenarios as load_pytest

# Graphist derives hypothesis tags from ids (no explicit tag); uptake uses
# explicit tags. Cover both.
CATALOG = {
    "hypotheses": [
        {"id": "GH-VER", "title": "derived-tag"},          # -> hyp_gh_ver
        {"id": "HYP-1", "tag": "hyp_ub_1", "title": "explicit"},
    ],
    "capabilities": [{"id": "CAP-X", "tag": "cap_x", "title": "c"}],
}


def _behave_report():
    return [
        {
            "name": "F",
            "tags": ["application", "cap_x"],
            "elements": [
                {
                    "type": "scenario",
                    "name": "derived",
                    "location": "f.feature:3",
                    "status": "passed",
                    "tags": ["hyp_gh_ver", "evidence_mechanism"],
                },
                {
                    "type": "scenario",
                    "name": "explicit",
                    "location": "f.feature:9",
                    "status": "skipped",
                    "tags": ["hyp_ub_1", "wip"],
                },
            ],
        }
    ]


def test_behave_resolves_derived_and_explicit_tags(tmp_path):
    report = tmp_path / "behave.json"
    report.write_text(json.dumps(_behave_report()), encoding="utf-8")
    scenarios = load_behave(report, CATALOG)
    assert scenarios[0]["hypotheses"] == ["GH-VER"]
    assert scenarios[0]["capabilities"] == ["CAP-X"]
    assert scenarios[0]["evidence_kind"] == "mechanism"
    assert scenarios[0]["status"] == "passed"
    assert scenarios[1]["hypotheses"] == ["HYP-1"]
    assert scenarios[1]["status"] == "skipped"


def test_behave_rejects_unknown_tag(tmp_path):
    report = tmp_path / "behave.json"
    bad = _behave_report()
    bad[0]["elements"][0]["tags"] = ["hyp_nope"]
    report.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(TraceabilityError):
        load_behave(report, CATALOG)


def test_pytest_report_normalizes(tmp_path):
    report = tmp_path / "pytest.json"
    report.write_text(
        json.dumps(
            {
                "tests": [
                    {
                        "nodeid": "tests/test_x.py::test_ver",
                        "outcome": "passed",
                        "keywords": {"hyp_gh_ver": 1, "cap_x": 1, "evidence_mechanism": 1},
                    },
                    {
                        "nodeid": "tests/test_x.py::test_skip",
                        "outcome": "skipped",
                        "keywords": ["hyp_ub_1"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    scenarios = load_pytest(report, CATALOG)
    assert scenarios[0]["hypotheses"] == ["GH-VER"]
    assert scenarios[0]["capabilities"] == ["CAP-X"]
    assert scenarios[0]["evidence_kind"] == "mechanism"
    assert scenarios[0]["status"] == "passed"
    assert scenarios[1]["status"] == "skipped"
