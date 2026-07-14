"""Normalize a pytest-json-report file into the engine's scenario model.

Consumes the report produced by the ``pytest-json-report`` plugin
(``pytest --json-report --json-report-file=REPORT``). Tests attach traceability
through markers, surfaced in each test's ``keywords``:

    @pytest.mark.hyp_ub_1
    @pytest.mark.cap_example
    @pytest.mark.evidence_mechanism
    def test_example(): ...

pytest outcomes map to scenario statuses: passed/failed/skipped as-is, and an
errored test maps to ``error``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import capability_tag_map, hypothesis_tag_map, resolve_scenario

_OUTCOME_TO_STATUS = {
    "passed": "passed",
    "failed": "failed",
    "skipped": "skipped",
    "error": "error",
    "xfailed": "passed",
    "xpassed": "passed",
}


def _keyword_tags(keywords: Any) -> "set[str]":
    # pytest-json-report emits keywords as a dict {name: count} or a list.
    if isinstance(keywords, Mapping):
        return {str(key) for key in keywords}
    if isinstance(keywords, (list, tuple, set)):
        return {str(key) for key in keywords}
    return set()


def load_scenarios(
    report_path: "str | Path", catalog: Mapping[str, Any]
) -> "list[dict[str, Any]]":
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    tests = report.get("tests") if isinstance(report, Mapping) else None
    if not isinstance(tests, list):
        raise ValueError("pytest report must contain a 'tests' list (pytest-json-report)")
    capability_tags = capability_tag_map(catalog)
    hypothesis_tags = hypothesis_tag_map(catalog)
    scenarios: "list[dict[str, Any]]" = []
    for test in tests:
        nodeid = str(test.get("nodeid", "unknown"))
        tags = _keyword_tags(test.get("keywords"))
        status = _OUTCOME_TO_STATUS.get(str(test.get("outcome", "untested")), "untested")
        name = nodeid.rsplit("::", 1)[-1]
        location = nodeid.rsplit("::", 1)[0] if "::" in nodeid else nodeid
        scenarios.append(
            resolve_scenario(
                tags=tags,
                scenario_id=nodeid,
                name=name,
                feature=location,
                location=location,
                status=status,
                capability_tags=capability_tags,
                hypothesis_tags=hypothesis_tags,
            )
        )
    return scenarios
