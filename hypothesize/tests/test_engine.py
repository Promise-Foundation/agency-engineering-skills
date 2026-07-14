"""Unit tests for the epistemic rules of the engine."""

from __future__ import annotations

import pytest

from hypothesize import ResearchStatusError, ResearchStatusService

HYP = "HYP-X"
CAP = "CAP-X"


def catalog(**extra):
    base = {
        "schema_version": 1,
        "title": "test",
        "thesis": "t",
        "hypotheses": [{"id": HYP, "tag": "hyp_x", "title": "X", "summary": ""}],
        "capabilities": [{"id": CAP, "tag": "cap_x", "title": "X", "hypotheses": [HYP]}],
    }
    base.update(extra)
    return base


def scenario(idx, status, *, kind="capability", caps=(CAP,), hyps=(HYP,)):
    return {
        "id": f"s{idx}",
        "capabilities": list(caps),
        "hypotheses": list(hyps),
        "evidence_kind": kind,
        "required": True,
        "status": status,
    }


def publish(scenarios=(), evidence=(), previous=None, results=None, **cat):
    return ResearchStatusService().publish(
        catalog=catalog(**cat),
        scenarios=list(scenarios),
        evidence=list(evidence),
        previous=previous,
        results=results,
    )


def cap_status(pub):
    return pub["manifest"]["capabilities"][0]["status"]


def hyp(pub):
    return pub["manifest"]["hypotheses"][0]


# -- capability status --------------------------------------------------------
def test_all_passed_is_implemented():
    assert cap_status(publish([scenario(1, "passed"), scenario(2, "passed")])) == "implemented"


def test_one_skipped_is_partial():
    assert cap_status(publish([scenario(1, "passed"), scenario(2, "skipped")])) == "partial"


def test_no_scenarios_is_specified():
    assert cap_status(publish([])) == "specified"


def test_only_skipped_is_specified():
    assert cap_status(publish([scenario(1, "skipped")])) == "specified"


def test_failure_is_failing_without_prior():
    assert cap_status(publish([scenario(1, "failed")])) == "failing"


def test_failure_after_implemented_is_regressed():
    previous = {"capabilities": [{"id": CAP, "status": "implemented"}], "hypotheses": []}
    assert cap_status(publish([scenario(1, "failed")], previous=previous)) == "regressed"


# -- scientific conclusion ----------------------------------------------------
def test_passing_scientific_contract_does_not_promote():
    pub = publish(
        [scenario(1, "passed", kind="scientific_contract")],
        evidence=[
            {
                "id": "E1",
                "hypotheses": [HYP],
                "kind": "scientific",
                "maturity": "mechanism",
                "qualified": False,
                "preregistered": False,
                "outcome": "not_tested",
            }
        ],
    )
    assert cap_status(pub) == "implemented"
    assert hyp(pub)["conclusion"] == "not_tested"


@pytest.mark.parametrize("outcome", ["supported", "falsified", "inconclusive"])
def test_qualified_preregistered_result_sets_conclusion(outcome):
    pub = publish(
        [scenario(1, "passed")],
        evidence=[
            {
                "id": "E1",
                "hypotheses": [HYP],
                "kind": "scientific",
                "maturity": "comparative_pilot",
                "qualified": True,
                "preregistered": True,
                "outcome": outcome,
            }
        ],
    )
    assert hyp(pub)["conclusion"] == outcome


def test_unqualified_outcome_is_quarantined_and_not_promoted():
    pub = publish(
        [scenario(1, "passed")],
        evidence=[
            {
                "id": "E1",
                "hypotheses": [HYP],
                "kind": "scientific",
                "maturity": "mechanism",
                "qualified": False,
                "preregistered": False,
                "outcome": "supported",
            }
        ],
    )
    assert hyp(pub)["conclusion"] == "not_tested"
    assert [q["id"] for q in pub["manifest"]["quarantined_evidence"]] == ["E1"]


# -- evidence maturity --------------------------------------------------------
def test_mechanism_evidence_sets_maturity():
    pub = publish(
        [scenario(1, "passed")],
        evidence=[{"id": "E1", "hypotheses": [HYP], "maturity": "mechanism", "outcome": "not_tested"}],
    )
    assert hyp(pub)["evidence_maturity"] == "mechanism"


def test_passed_scenario_without_evidence_falls_back_to_design():
    pub = publish([scenario(1, "passed", kind="capability")])
    assert hyp(pub)["evidence_maturity"] == "design"


def test_only_skipped_scenarios_stay_none_maturity():
    pub = publish([scenario(1, "skipped", kind="mechanism")])
    assert hyp(pub)["evidence_maturity"] == "none"


def test_evidence_mechanism_scenario_bumps_maturity():
    pub = publish([scenario(1, "passed", kind="mechanism")])
    assert hyp(pub)["evidence_maturity"] == "mechanism"


# -- validation & determinism -------------------------------------------------
def test_unknown_hypothesis_reference_is_rejected():
    with pytest.raises(ResearchStatusError):
        publish([scenario(1, "passed", hyps=("HYP-UNKNOWN",))])


def test_unknown_maturity_is_rejected():
    with pytest.raises(ResearchStatusError):
        publish(evidence=[{"id": "E1", "hypotheses": [HYP], "maturity": "bogus"}])


def test_source_hash_is_deterministic():
    a = publish([scenario(1, "passed")])
    b = publish([scenario(1, "passed")])
    assert a["manifest"]["build"]["source_hash"] == b["manifest"]["build"]["source_hash"]


# -- conditional manifest sections -------------------------------------------
def test_requirements_included_only_when_present():
    without = publish([scenario(1, "passed")])
    assert "requirements" not in without["manifest"]
    with_req = publish(
        [scenario(1, "passed")],
        requirements=[{"id": "REQ-1", "title": "r", "capabilities": [CAP], "hypotheses": [HYP]}],
    )
    assert [r["id"] for r in with_req["manifest"]["requirements"]] == ["REQ-1"]


def test_tracks_and_results_included_only_when_present():
    plain = publish([scenario(1, "passed")])
    assert "tracks" not in plain["manifest"]
    assert "results" not in plain["manifest"]
    rich = publish(
        [scenario(1, "passed")],
        results={"run": {"ok": True}},
        tracks=[{"id": "t1", "title": "T"}],
        hypotheses=[{"id": HYP, "tag": "hyp_x", "title": "X", "summary": "", "tracks": ["t1"]}],
    )
    assert "results" in rich["manifest"]
    assert rich["manifest"]["tracks"][0]["hypotheses"] == [HYP]
