"""The hypothesize bridge keeps logical and empirical status separate."""

from __future__ import annotations

import json

from ltp.enums import EmpiricalStatus, VerificationRole
from ltp.integrations import hypothesize
from ltp.models import ClaimVerification, parse_model

MODEL = {
    "project": {"name": "T", "goal": "G-1"},
    "entities": [
        {"id": "G-1", "kind": "goal", "statement": "goal"},
        {"id": "RC-1", "kind": "root_cause", "statement": "cause"},
        {"id": "UDE-1", "kind": "undesirable_effect", "statement": "effect", "basis": "observed"},
    ],
    "causal_claims": [
        {
            "id": "CLM-1",
            "premises": ["RC-1"],
            "conclusion": "UDE-1",
            "clr": {"causality_existence": {"result": "pass"}},
            "verification": {"hypothesis_ref": "HYP-1", "role": "causal_outcome"},
        }
    ],
}


def test_export_links():
    model = parse_model(MODEL)
    links = hypothesize.export_links(model)
    assert links == [
        {
            "claim": "CLM-1",
            "conclusion": "UDE-1",
            "hypothesis_ref": "HYP-1",
            "role": "causal_outcome",
            "empirical_status": "not_tested",
        }
    ]


def test_check_links_flags_unresolved():
    model = parse_model(MODEL)
    assert hypothesize.check_links(model, known_ids={"HYP-1"}) == []
    problems = hypothesize.check_links(model, known_ids={"HYP-OTHER"})
    assert problems and "HYP-1" in problems[0]


def test_falsified_import_sets_empirical_status_not_logic(tmp_path):
    model = parse_model(MODEL)
    research = tmp_path / "research-status.json"
    research.write_text(json.dumps({"hypotheses": [{"id": "HYP-1", "conclusion": "falsified"}]}))

    changes = hypothesize.import_evidence(model, research)

    claim = model.causal_claims[0]
    assert claim.verification.empirical_status == EmpiricalStatus.FALSIFIED
    # logical status (CLR) is untouched
    assert claim.clr.causality_existence.result.value == "pass"
    # a contradiction was recorded
    assert any("falsified" in note for note in model.contradictions)
    assert changes
