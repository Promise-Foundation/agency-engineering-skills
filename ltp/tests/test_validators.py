"""Fixture-driven validator tests: bad logic must be rejected, good logic must pass.

This is the adversarial core -- changes are judged by their ability to reject bad
logic, not merely to render good examples.
"""

from __future__ import annotations

import yaml
import pytest

from conftest import fixture_cases
from ltp.store import load_model
from ltp.validators import validate


def _codes(report, severity):
    return {d.code for d in report.diagnostics if d.severity.value == severity}


@pytest.mark.parametrize("case", fixture_cases("valid"), ids=lambda p: p.name)
def test_valid_fixtures_are_publishable(case):
    model = load_model(case / "ltp-model.yaml")
    expected = yaml.safe_load((case / "expected.yaml").read_text(encoding="utf-8"))
    report = validate(model)
    assert not report.errors, f"{case.name} has errors: {[d.code for d in report.errors]}"
    assert report.is_publishable is True
    assert expected["publishable"] is True


@pytest.mark.parametrize("case", fixture_cases("invalid"), ids=lambda p: p.name)
def test_invalid_fixtures_raise_expected_codes(case):
    model = load_model(case / "ltp-model.yaml")
    expected = yaml.safe_load((case / "expected.yaml").read_text(encoding="utf-8"))
    report = validate(model)
    errors = _codes(report, "error")
    warnings = _codes(report, "warning")
    for code in expected["expected_errors"]:
        assert code in errors, f"{case.name}: expected error {code}, got {sorted(errors)}"
    for code in expected["expected_warnings"]:
        assert code in warnings, f"{case.name}: expected warning {code}, got {sorted(warnings)}"


def test_defective_model_fails_across_trees():
    """The Milestone-1 acceptance criterion: a broadly defective model fails with
    explicit Goal Tree, Cloud, FRT/CRT, PRT and TT diagnostics at once."""
    bad = {
        "project": {"name": "Defective", "provisional_goal": "G-1"},
        "entities": [
            {"id": "G-1", "kind": "goal", "statement": "Succeed"},
            {"id": "CSF-1", "kind": "critical_success_factor", "statement": "Thing works"},
            {"id": "UDE-4", "kind": "undesirable_effect", "statement": "Runs are non-reproducible", "basis": "observed"},
            {"id": "RC-1", "kind": "root_cause", "statement": "Findings are isolated"},
            {"id": "AC-3", "kind": "cause", "statement": "Aux cause"},
            {"id": "INJ-1", "kind": "injection", "statement": "Use a stable tree"},
            {"id": "A-1", "kind": "cloud_objective", "statement": "obj"},
            {"id": "B-1", "kind": "cloud_need", "statement": "need"},
            {"id": "OBS-1", "kind": "obstacle", "statement": "no addresses"},
            {"id": "IO-1", "kind": "intermediate_objective", "statement": "Add a tree"},
            {"id": "ACT-1", "kind": "transition_action", "statement": "do it"},
        ],
        "causal_claims": [
            {"id": "CLM-1", "premises": ["RC-1", "AC-3"], "operator": "single", "conclusion": "UDE-4"}
        ],
        "clouds": [
            {
                "id": "EC-1", "status": "validated_persistent_conflict",
                "objective": "A-1", "need_b": "B-1", "need_c": "B-1", "action_d": "A-1", "action_d_prime": "B-1",
                "necessity_claims": {"a_requires_b": "NEC-X", "a_requires_c": "NEC-X", "b_requires_d": "NEC-X", "c_requires_d_prime": "NEC-X"},
            }
        ],
        "transitions": [{"id": "TR-1", "action": "ACT-1", "advances": "INJ-1"}],
    }
    report = validate(load_model_from_dict(bad))
    families = {code.split("-")[0] for code in _codes(report, "error")}
    for family in ("GT", "CRT", "EC", "PRT", "TT"):
        assert family in families, f"missing {family} error; got {sorted(families)}"
    assert not report.is_publishable


def load_model_from_dict(data):
    from ltp.models import parse_model

    return parse_model(data)
