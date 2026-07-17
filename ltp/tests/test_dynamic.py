"""Dynamic-LTP contracts: polarity, prediction loop, obligations, and history."""

from __future__ import annotations

from ltp.history import ModelRevision, project_learning_history
from ltp.models import parse_model, to_dict
from ltp.obligations import derive_obligations
from ltp.predictions import evaluate_all, evaluate_prediction
from ltp.renderers.dashboard import build_dashboard
from ltp.validators import validate


def prediction_model(**prediction_overrides):
    prediction = {
        "id": "PRED-1",
        "source_claim": "CLM-1",
        "statement": "Expedites fall",
        "indicator": "expedites_per_week",
        "baseline": 20,
        "expected_change_percent": -40,
        "tolerance_percent": 5,
        "expected_by": "2026-02-12",
        "review_by": "2026-02-15",
        "owner": "operations",
    }
    prediction.update(prediction_overrides)
    return parse_model(
        {
            "project": {"name": "T"},
            "entities": [
                {"id": "RC-1", "kind": "root_cause", "statement": "cause"},
                {"id": "UDE-1", "kind": "undesirable_effect", "statement": "effect"},
            ],
            "causal_claims": [
                {
                    "id": "CLM-1",
                    "premises": ["RC-1"],
                    "conclusion": "UDE-1",
                    "clr": {"causality_existence": {"result": "pass"}},
                }
            ],
            "predicted_effects": [prediction],
        }
    )


def test_trimming_relation_is_not_a_causal_arrow_and_renders_truthfully():
    model = parse_model(
        {
            "project": {"name": "T"},
            "entities": [
                {"id": "TRIM-1", "kind": "trimming_injection", "statement": "guard"},
                {"id": "NBR-1", "kind": "negative_branch", "statement": "risk"},
            ],
            "semantic_relations": [
                {
                    "id": "REL-1",
                    "source": "TRIM-1",
                    "target": "NBR-1",
                    "relation": "neutralizes",
                }
            ],
        }
    )
    codes = {item.code for item in validate(model).diagnostics}
    assert "FRT-006" not in codes and "REL-001" not in codes
    edges = build_dashboard(model)["views"]["future-reality"]["edges"]
    assert {"source": "TRIM-1", "target": "NBR-1", "relation": "neutralizes", "claim": "REL-1"} in edges


def test_prevention_encoded_as_sufficiency_is_rejected():
    model = parse_model(
        {
            "project": {"name": "T"},
            "entities": [
                {"id": "TRIM-1", "kind": "trimming_injection", "statement": "guard"},
                {"id": "NBR-1", "kind": "negative_branch", "statement": "risk"},
            ],
            "causal_claims": [
                {"id": "CLM-1", "premises": ["TRIM-1"], "conclusion": "NBR-1"}
            ],
        }
    )
    assert "REL-001" in {item.code for item in validate(model).errors}


def test_prediction_evaluation_is_deterministic_and_does_not_touch_clr():
    model = prediction_model()
    model.observations.append(
        parse_model(
            {
                "project": {"name": "observation factory"},
                "predicted_effects": [
                    {"id": "PRED-X", "source_claim": "CLM-X", "statement": "unused"}
                ],
                "observations": [
                    {
                        "id": "OBS-1",
                        "prediction": "PRED-1",
                        "observed_at": "2026-02-15",
                        "change_percent": -10,
                    }
                ],
            }
        ).observations[0]
    )
    before = to_dict(model.causal_claims[0], prune=False)
    first = evaluate_prediction(model.predicted_effects[0], model.observations, as_of="2026-02-15")
    second = evaluate_prediction(model.predicted_effects[0], model.observations, as_of="2026-02-15")
    assert first == second
    assert first.result.value == "inconclusive"
    assert to_dict(model.causal_claims[0], prune=False) == before


def test_expected_lag_is_resolved_from_implementation_date():
    model = prediction_model(
        expected_by=None,
        review_by=None,
        implemented_at="2026-01-01",
        expected_lag_days=42,
    )
    evaluation = evaluate_prediction(
        model.predicted_effects[0], model.observations, as_of="2026-02-01"
    )
    assert evaluation.result.value == "not_yet_due"
    assert "2026-02-12" in (evaluation.explanation or "")


def test_explicit_as_of_date_turns_overdue_obligation_into_a_gate():
    model = prediction_model()
    assert not derive_obligations(model, as_of="2026-02-10")
    due = derive_obligations(model, as_of="2026-02-16")
    assert [item.kind for item in due] == ["prediction_overdue"]
    assert "PRED-OVERDUE" not in {item.code for item in validate(model, as_of="2026-02-10").errors}
    assert "PRED-OVERDUE" in {item.code for item in validate(model, as_of="2026-02-16").errors}


def test_waiver_clears_obligation_without_touching_logical_status():
    model = prediction_model(waived=True, waiver_reason="indicator retired")
    before = to_dict(model.causal_claims[0].clr, prune=False)
    assert not derive_obligations(model, as_of="2026-02-20")
    assert to_dict(model.causal_claims[0].clr, prune=False) == before


def test_learning_history_unifies_sources_and_supports_semantic_diff():
    before = prediction_model()
    after = prediction_model()
    after.entities[0].statement = "revised cause"
    evaluations = evaluate_all(after, as_of="2026-02-10")
    history = project_learning_history(
        model_revisions=[
            ModelRevision("2026-02-01", "aaa", before),
            ModelRevision("2026-02-12", "bbb", after),
        ],
        assessments=[
            {
                "id": "ASMNT-1",
                "observedAt": "2026-02-13",
                "subject": "CLM-1",
                "assessor": "sales",
                "verdict": "disputed",
                "rationale": "seasonality",
            }
        ],
        research_snapshots=[
            {
                "generated_at": "2026-02-14",
                "revision": "rrr",
                "hypotheses": [{"id": "HYP-1", "conclusion": "inconclusive"}],
            }
        ],
        prediction_evaluations=evaluations,
    )
    assert history.digest == project_learning_history(
        model_revisions=[ModelRevision("2026-02-01", "aaa", before), ModelRevision("2026-02-12", "bbb", after)],
        assessments=[{"id": "ASMNT-1", "observedAt": "2026-02-13", "subject": "CLM-1", "assessor": "sales", "verdict": "disputed", "rationale": "seasonality"}],
        research_snapshots=[{"generated_at": "2026-02-14", "revision": "rrr", "hypotheses": [{"id": "HYP-1", "conclusion": "inconclusive"}]}],
        prediction_evaluations=evaluations,
    ).digest
    kinds = {event.kind for event in history.diff("2026-02-11", "2026-02-14")}
    assert {"model_record_revised", "stakeholder_assessment", "hypothesis_conclusion_changed"} <= kinds
    assert all("+++" not in event.summary and "---" not in event.summary for event in history.events)


# --------------------------------------------------------------------------- #
# Regression tests for the correctness bugs the first suite missed. Each fails
# on the pre-fix engine and passes after it, so "green" now certifies the
# temporal/ontology logic is right -- not merely that the happy path runs.
# --------------------------------------------------------------------------- #
def _add_observation(model, oid, observed_at, **fields):
    obs = parse_model(
        {
            "project": {"name": "obs"},
            "observations": [
                {"id": oid, "prediction": "PRED-1", "observed_at": observed_at, **fields}
            ],
        }
    ).observations[0]
    model.observations.append(obs)
    return model


def test_numeric_verdicts_respect_direction_not_just_tolerance():
    # A decrease within tolerance of the -40% target is supported.
    supported = _add_observation(prediction_model(), "OBS-1", "2026-02-13", change_percent=-42)
    assert (
        evaluate_prediction(
            supported.predicted_effects[0], supported.observations, as_of="2026-02-15"
        ).result.value
        == "supported"
    )
    # A wrong-direction reading is never "supported", even when the tolerance band
    # is wider than the expected magnitude (the pre-fix direction-inversion bug).
    increased = _add_observation(
        prediction_model(tolerance_percent=50), "OBS-1", "2026-02-13", change_percent=2
    )
    assert (
        evaluate_prediction(
            increased.predicted_effects[0], increased.observations, as_of="2026-02-15"
        ).result.value
        == "contradicted"
    )


def test_intervention_unverified_waits_for_the_effect_to_be_due():
    model = prediction_model(
        expected_by=None,
        review_by=None,
        implemented_at="2026-01-01",
        expected_lag_days=90,  # effect due 2026-04-01
        implementation_status="complete",
    )
    # Complete with no observation, but the effect is not due yet: the evaluator
    # itself says not_yet_due, so the blocking gate must not fire.
    assert not derive_obligations(model, as_of="2026-02-01")
    # Past the due date with still no observation: now it is a real obligation.
    assert [item.kind for item in derive_obligations(model, as_of="2026-04-02")] == [
        "intervention_unverified"
    ]


def test_premature_observation_is_not_treated_as_the_outcome():
    model = prediction_model(
        expected_by=None,
        review_by=None,
        implemented_at="2026-01-15",
        expected_lag_days=28,  # effect due 2026-02-12
    )
    _add_observation(model, "OBS-EARLY", "2026-01-01", change_percent=3)  # before implementation
    evaluation = evaluate_prediction(
        model.predicted_effects[0], model.observations, as_of="2026-03-01"
    )
    assert evaluation.observation is None
    assert evaluation.result.value == "inconclusive"


def test_multi_premise_prevention_encoded_as_sufficiency_is_rejected():
    model = parse_model(
        {
            "project": {"name": "T"},
            "entities": [
                {"id": "TRIM-1", "kind": "trimming_injection", "statement": "guard"},
                {"id": "RC-1", "kind": "root_cause", "statement": "cause"},
                {"id": "NBR-1", "kind": "negative_branch", "statement": "risk"},
            ],
            "causal_claims": [
                {
                    "id": "CLM-1",
                    "premises": ["TRIM-1", "RC-1"],
                    "operator": "all",
                    "conclusion": "NBR-1",
                }
            ],
        }
    )
    assert "REL-001" in {item.code for item in validate(model).errors}


def test_undispositioned_negative_branch_is_flagged_without_an_injection():
    model = parse_model(
        {
            "project": {"name": "T"},
            "entities": [{"id": "NBR-1", "kind": "negative_branch", "statement": "risk"}],
        }
    )
    assert "FRT-006" in {item.code for item in validate(model).diagnostics}


def test_stale_observation_is_flagged_after_its_validity_window():
    model = prediction_model(observation_valid_for_days=30)
    _add_observation(model, "OBS-1", "2026-02-13", change_percent=-42)  # valid until 2026-03-15
    assert "observation_stale" not in {
        item.kind for item in derive_obligations(model, as_of="2026-03-01")
    }
    assert "observation_stale" in {
        item.kind for item in derive_obligations(model, as_of="2026-04-01")
    }


def test_waiver_is_what_clears_the_overdue_obligation():
    # Baseline: the un-waived prediction really is overdue at this date...
    assert [
        item.kind for item in derive_obligations(prediction_model(), as_of="2026-02-16")
    ] == ["prediction_overdue"]
    # ...so an empty queue under a waiver proves the waiver did the clearing.
    assert not derive_obligations(
        prediction_model(waived=True, waiver_reason="indicator retired"), as_of="2026-02-16"
    )
