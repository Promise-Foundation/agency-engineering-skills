#!/usr/bin/env python3
"""Generate the validator fixtures under ``evals/fixtures/{valid,invalid}/``.

Each fixture is a *committed* ``ltp-model.yaml`` plus an ``expected.yaml`` listing
the diagnostic codes it must produce. They are generated programmatically from
one pristine base model so a planted defect is the only difference from a clean
model -- and the generator self-checks that the intended codes actually fire
before writing. The committed YAML (not this script) is what the test suite
reads; re-run this only to regenerate.

    python evals/build_fixtures.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from ltp.models import parse_model  # noqa: E402
from ltp.store import dump_model  # noqa: E402
from ltp.validators import validate  # noqa: E402

FIXTURES = ROOT / "evals" / "fixtures"

_CLR_CHECKS = (
    "clarity",
    "entity_existence",
    "causality_existence",
    "cause_insufficiency",
    "additional_cause",
    "cause_effect_reversal",
    "predicted_effect_existence",
    "tautology",
)


def passing_clr() -> dict:
    return {name: {"result": "pass"} for name in _CLR_CHECKS}


def base() -> dict:
    """A pristine, fully publishable model exercising five trees + a constraint."""
    return {
        "schema_version": 2,
        "project": {"name": "Remote-work evidence review", "goal": "G-1", "analysis_mode": "forward"},
        "analysis": {
            "current_constraint": "CONSTRAINT-1",
            "recommended_next_action": "TR-1",
            "expected_effect": "DE-1",
        },
        "analysis_plan": {
            "mode": "full",
            "goal_tree": {"status": "done"},
            "current_reality_tree": {"status": "done"},
            "future_reality_tree": {"status": "done"},
            "prerequisite_tree": {"status": "done"},
            "transition_tree": {"status": "done"},
            "evaporating_cloud": {"status": "skipped", "reason": "no persistent conflict found"},
        },
        "entities": [
            {"id": "G-1", "kind": "goal", "statement": "Remote-work decisions reflect evidence and context", "basis": "inferred", "evidence_refs": ["EVD-1"]},
            {"id": "CSF-1", "kind": "critical_success_factor", "statement": "Productivity claims are scoped by worker and task", "basis": "observed", "evidence_refs": ["EVD-1"], "satisfaction_criterion": "each claim names its population and task"},
            {"id": "NC-1", "kind": "necessary_condition", "statement": "New evidence accumulates against stable questions", "basis": "observed", "evidence_refs": ["EVD-1"], "satisfaction_criterion": "each finding maps to a question node"},
            {"id": "RC-1", "kind": "root_cause", "statement": "Findings arrive as isolated claims instead of accumulating against a scaffold", "basis": "inferred", "evidence_refs": ["EVD-1"]},
            {"id": "AC-1", "kind": "cause", "statement": "Notes give findings no stable node addresses", "basis": "observed", "evidence_refs": ["EVD-1"]},
            {"id": "UDE-1", "kind": "undesirable_effect", "statement": "A 13% local gain is read as a universal remote-work effect", "basis": "observed", "evidence_refs": ["EVD-1"]},
            {"id": "UDE-2", "kind": "undesirable_effect", "statement": "Call-centre evidence is generalized to unlike roles", "basis": "observed", "evidence_refs": ["EVD-1"]},
            {"id": "ASM-1", "kind": "assumption", "statement": "Isolated claims cannot carry their own scope limits", "basis": "inferred", "evidence_refs": ["EVD-1"]},
            {"id": "INJ-1", "kind": "injection", "statement": "Attach each finding to a stable issue tree", "basis": "inferred"},
            {"id": "DE-1", "kind": "desirable_effect", "statement": "Readers see the gain together with its role and task limits", "basis": "inferred"},
            {"id": "OBS-1", "kind": "obstacle", "statement": "The current notes give findings no stable addresses", "basis": "observed", "evidence_refs": ["EVD-1"]},
            {"id": "IO-1", "kind": "intermediate_objective", "statement": "A validated remote-work question tree exists", "satisfaction": "unsatisfied"},
            {"id": "ER-1", "kind": "existing_reality", "statement": "Findings live in flat, unaddressed notes"},
            {"id": "NEED-1", "kind": "need", "statement": "Findings need stable addresses to accumulate"},
            {"id": "ACT-1", "kind": "transition_action", "statement": "Map the three Ctrip findings to the question tree"},
            {"id": "IE-1", "kind": "immediate_effect", "statement": "Each finding shows a visible scope, relation, and source"},
            {"id": "CONSTRAINT-1", "kind": "constraint", "statement": "No stable scaffold admits accumulating remote-work evidence", "basis": "inferred", "evidence_refs": ["EVD-1"]},
        ],
        "evidence": [
            {"id": "EVD-1", "source": "claim-tree-annotation.md", "lines": "1-24", "kind": "readme", "observation": "The process defines a stable claim tree to which fragments are mapped"},
        ],
        "necessity_claims": [
            {"id": "NEC-1", "prerequisite": "CSF-1", "objective": "G-1"},
            {"id": "NEC-2", "prerequisite": "NC-1", "objective": "CSF-1"},
            {"id": "NEC-3", "prerequisite": "IO-1", "objective": "INJ-1"},
        ],
        "causal_claims": [
            {"id": "CLM-1", "premises": ["RC-1", "AC-1"], "operator": "all", "conclusion": "UDE-1", "assumption_refs": ["ASM-1"], "clr": passing_clr()},
            {"id": "CLM-2", "premises": ["RC-1"], "operator": "single", "conclusion": "UDE-2", "assumption_refs": ["ASM-1"], "clr": passing_clr()},
            {"id": "CLM-3", "premises": ["INJ-1"], "operator": "single", "conclusion": "DE-1", "assumption_refs": ["ASM-1"], "clr": passing_clr()},
            {"id": "CLM-4", "premises": ["DE-1"], "operator": "single", "conclusion": "NC-1", "clr": passing_clr()},
        ],
        "predicted_effects": [
            {"id": "PRED-1", "source_claim": "CLM-1", "statement": "Unqualified generalizations recur across reports", "expectation": "should_exist", "result": "observed", "evidence_refs": ["EVD-1"]},
        ],
        "obstacle_resolutions": [{"id": "OR-1", "obstacle": "OBS-1", "intermediate_objective": "IO-1"}],
        "transitions": [
            {"id": "TR-1", "existing_reality": "ER-1", "need": "NEED-1", "action": "ACT-1", "immediate_effect": "IE-1", "advances": "IO-1", "likely_scope": ["notes/tree.md"], "estimated_size": "small", "verification": {"kind": "manual_check", "acceptance": "each finding shows its scope"}},
        ],
        "constraint_assessment": {
            "entity": "CONSTRAINT-1",
            "status": "candidate",
            "limiting_mechanism": "No scaffold admits accumulating evidence, so each study restarts the debate",
            "goal_measure": {"name": "Qualified comparisons completed", "unit": "comparisons", "period": "month"},
            "evidence_refs": ["EVD-1"],
            "alternative_candidates": [{"entity": "RC-1", "rejected_because": "addressing isolation alone does not admit evidence"}],
            "focusing_step": {"current": "exploit"},
            "exploit_direction": "Use the existing question tree before building new tooling",
        },
        "open_questions": ["Which productivity measure matters most to the decision-maker?"],
        "coverage_gaps": ["No long-term or collaborative-role evidence is in the toy source set"],
    }


def entity(model: dict, entity_id: str) -> dict:
    return next(e for e in model["entities"] if e["id"] == entity_id)


def claim(model: dict, claim_id: str) -> dict:
    return next(c for c in model["causal_claims"] if c["id"] == claim_id)


# --------------------------------------------------------------------------- #
# Valid fixtures
# --------------------------------------------------------------------------- #
def valid_simple_complete() -> dict:
    return base()


def valid_no_cloud_warranted() -> dict:
    model = base()
    # The cloud analysis was *done* and concluded no conflict -- not skipped.
    model["analysis_plan"]["evaporating_cloud"] = {"status": "done", "reason": "analysed; no persistent conflict"}
    model["conflict_analysis"] = {
        "status": "no_validated_persistent_conflict",
        "candidates_rejected": [
            {"candidate": "simplicity-vs-nuance", "reason": "a one-time editorial choice, not a chronic conflict"}
        ],
    }
    return model


def valid_compound_cause() -> dict:
    model = base()
    # A second compound cause, fully scrutinised, with its own predicted effect.
    entity(model, "AC-1")  # ensure present
    model["entities"].append(
        {"id": "AC-2", "kind": "cause", "statement": "Reviewers trust a single headline number", "basis": "observed", "evidence_refs": ["EVD-1"]}
    )
    claim(model, "CLM-2")["premises"] = ["RC-1", "AC-2"]
    claim(model, "CLM-2")["operator"] = "all"
    return model


# --------------------------------------------------------------------------- #
# Invalid fixtures (one planted defect each)
# --------------------------------------------------------------------------- #
def invalid_missing_additional_cause() -> dict:
    model = base()
    clr = claim(model, "CLM-2")["clr"]
    clr["cause_insufficiency"] = {"result": "fail", "proposed_additional_premise": "AC-1"}
    return model


def invalid_reversed_causality() -> dict:
    model = base()
    claim(model, "CLM-2")["clr"]["cause_effect_reversal"] = {
        "result": "fail",
        "reservation": "the effect plausibly drives the cause here",
    }
    return model


def invalid_tautology() -> dict:
    model = base()
    claim(model, "CLM-2")["clr"]["tautology"] = {"result": "fail", "reservation": "the cause restates the effect"}
    return model


def invalid_absent_predicted_effect() -> dict:
    model = base()
    model.pop("predicted_effects")
    return model


def invalid_missing_feature_as_ude() -> dict:
    model = base()
    entity(model, "UDE-1")["statement"] = "We do not have a realistic learned model in the comparison"
    return model


def invalid_nice_to_have_as_nc() -> dict:
    model = base()
    model["entities"].append(
        {"id": "NC-2", "kind": "necessary_condition", "statement": "A polished dark-mode dashboard exists", "basis": "provisional", "satisfaction_criterion": "the toggle works"}
    )
    model["necessity_claims"].append({"id": "NEC-4", "prerequisite": "NC-2", "objective": "CSF-1"})
    return model


def invalid_cloud_as_text_blob() -> dict:
    model = base()
    model["entities"].append({"id": "A-1", "kind": "cloud_objective", "statement": "Make a timely, defensible decision", "basis": "inferred"})
    # All five roles point at one entity -> collapsed cloud.
    model["necessity_claims"] += [
        {"id": "NEC-C1", "prerequisite": "A-1", "objective": "A-1"},
    ]
    model["clouds"] = [
        {
            "id": "EC-1",
            "status": "candidate",
            "objective": "A-1",
            "need_b": "A-1",
            "need_c": "A-1",
            "action_d": "A-1",
            "action_d_prime": "A-1",
            "necessity_claims": {"a_requires_b": "NEC-C1", "a_requires_c": "NEC-C1", "b_requires_d": "NEC-C1", "c_requires_d_prime": "NEC-C1"},
        }
    ]
    model["analysis_plan"]["evaporating_cloud"] = {"status": "done"}
    return model


def invalid_manufactured_cloud() -> dict:
    model = base()
    model["entities"] += [
        {"id": "A-2", "kind": "cloud_objective", "statement": "Ship the analysis on schedule", "basis": "inferred", "evidence_refs": ["EVD-1"]},
        {"id": "B-2", "kind": "cloud_need", "statement": "Cover every context", "basis": "inferred", "evidence_refs": ["EVD-1"]},
        {"id": "C-2", "kind": "cloud_need", "statement": "Finish quickly", "basis": "inferred", "evidence_refs": ["EVD-1"]},
        {"id": "D-2", "kind": "cloud_action", "statement": "Keep researching", "basis": "inferred"},
        {"id": "DP-2", "kind": "cloud_action", "statement": "Stop and write", "basis": "inferred"},
        {"id": "ASM-C", "kind": "assumption", "statement": "The two cannot proceed together", "basis": "inferred"},
    ]
    model["necessity_claims"] += [
        {"id": "NEC-C1", "prerequisite": "B-2", "objective": "A-2", "assumption_refs": ["ASM-C"]},
        {"id": "NEC-C2", "prerequisite": "C-2", "objective": "A-2", "assumption_refs": ["ASM-C"]},
        {"id": "NEC-C3", "prerequisite": "D-2", "objective": "B-2", "assumption_refs": ["ASM-C"]},
        {"id": "NEC-C4", "prerequisite": "DP-2", "objective": "C-2", "assumption_refs": ["ASM-C"]},
    ]
    model["conflict_claims"] = [
        {"id": "CON-1", "statement": "We have finite time, so we cannot do both", "assumption_refs": ["ASM-C"], "evidence_refs": ["EVD-1"]}
    ]
    model["clouds"] = [
        {
            "id": "EC-1",
            "status": "validated_persistent_conflict",
            "objective": "A-2",
            "need_b": "B-2",
            "need_c": "C-2",
            "action_d": "D-2",
            "action_d_prime": "DP-2",
            "necessity_claims": {"a_requires_b": "NEC-C1", "a_requires_c": "NEC-C2", "b_requires_d": "NEC-C3", "c_requires_d_prime": "NEC-C4"},
            "conflict_claim": "CON-1",
            "injection_refs": ["INJ-1"],
        }
    ]
    model["analysis_plan"]["evaporating_cloud"] = {"status": "done"}
    return model


def invalid_untrimmed_negative_branch() -> dict:
    model = base()
    model["entities"].append({"id": "NBR-1", "kind": "negative_branch", "statement": "The tree becomes rigid and discourages new questions", "basis": "inferred"})
    model["causal_claims"].append(
        {"id": "CLM-5", "premises": ["INJ-1"], "operator": "single", "conclusion": "NBR-1", "clr": passing_clr()}
    )
    return model


def invalid_disconnected_prt() -> dict:
    model = base()
    # An unsatisfied IO with an obstacle but no ordering toward the injection.
    model["entities"] += [
        {"id": "OBS-2", "kind": "obstacle", "statement": "Reviewers lack a shared vocabulary", "basis": "observed", "evidence_refs": ["EVD-1"]},
        {"id": "IO-2", "kind": "intermediate_objective", "statement": "A shared review vocabulary is agreed", "satisfaction": "unsatisfied"},
    ]
    model["obstacle_resolutions"].append({"id": "OR-2", "obstacle": "OBS-2", "intermediate_objective": "IO-2"})
    return model


def invalid_compound_transition() -> dict:
    model = base()
    entity(model, "ACT-1")["statement"] = "Add the schema and refactor the encoder and migrate the store"
    model["transitions"][0]["likely_scope"] = ["src/schema.py", "src/encoder/model.py", "db/migrations/001.sql"]
    return model


def invalid_root_cause_labelled_constraint() -> dict:
    model = base()
    model["analysis"]["current_constraint"] = "RC-1"
    model.pop("constraint_assessment")
    # Remove the now-dangling constraint entity to keep the model otherwise clean.
    model["entities"] = [e for e in model["entities"] if e["id"] != "CONSTRAINT-1"]
    return model


def invalid_untraceable_action() -> dict:
    model = base()
    # A transition that advances an IO with no onward path to the goal.
    model["entities"].append({"id": "IO-9", "kind": "intermediate_objective", "statement": "A tangential cleanup is done", "satisfaction": "unsatisfied"})
    model["entities"].append({"id": "ACT-9", "kind": "transition_action", "statement": "Tidy unrelated helper code"})
    model["transitions"].append({"id": "TR-9", "action": "ACT-9", "advances": "IO-9", "immediate_effect": "IE-1", "likely_scope": ["src/helpers.py"], "verification": {"kind": "manual_check"}})
    model["analysis"]["recommended_next_action"] = "TR-9"
    return model


VALID = [
    ("simple-complete", "A complete, publishable analysis across five trees.", valid_simple_complete, [], []),
    ("no-cloud-warranted", "No persistent conflict; recorded as conflict_analysis, not forced into a Cloud.", valid_no_cloud_warranted, [], []),
    ("compound-cause", "Two compound (AND) sufficiency claims, fully scrutinised.", valid_compound_cause, [], []),
]

INVALID = [
    ("missing-additional-cause", "CLR marks a cause insufficient.", invalid_missing_additional_cause, [], ["CRT-006"]),
    ("reversed-causality", "CLR concludes cause and effect are reversed.", invalid_reversed_causality, ["CLR-006"], []),
    ("tautology", "CLR concludes the claim restates itself.", invalid_tautology, ["CLR-007"], []),
    ("absent-predicted-effect", "A root cause with no predicted effect.", invalid_absent_predicted_effect, [], ["PRED-001"]),
    ("missing-feature-as-ude", "A UDE written as a missing feature.", invalid_missing_feature_as_ude, [], ["CRT-001"]),
    ("nice-to-have-as-nc", "An NC asserted necessary with no justification.", invalid_nice_to_have_as_nc, [], ["GT-010"]),
    ("cloud-as-text-blob", "A Cloud whose five roles collapse to one entity.", invalid_cloud_as_text_blob, ["EC-002"], []),
    ("manufactured-cloud", "A Cloud resting only on generic resource finitude.", invalid_manufactured_cloud, [], ["EC-009"]),
    ("untrimmed-negative-branch", "A negative branch left undispositioned.", invalid_untrimmed_negative_branch, ["FRT-006"], []),
    ("disconnected-prt", "An unsatisfied IO with no path to the injection.", invalid_disconnected_prt, ["PRT-006"], []),
    ("compound-transition", "An action bundling several independent changes.", invalid_compound_transition, [], ["TT-003"]),
    ("root-cause-labelled-constraint", "A root cause used as the constraint without demonstration.", invalid_root_cause_labelled_constraint, ["CON-002"], ["CON-006"]),
    ("untraceable-action", "A recommended action with no path to the goal.", invalid_untraceable_action, ["XTR-004"], []),
]


def _write(kind: str, name: str, description: str, model_dict: dict, exp_err, exp_warn) -> str:
    model = parse_model(model_dict)
    report = validate(model)
    actual_err = {d.code for d in report.diagnostics if d.severity.value == "error"}
    actual_warn = {d.code for d in report.diagnostics if d.severity.value == "warning"}

    problems = []
    for code in exp_err:
        if code not in actual_err:
            problems.append(f"expected error {code} not raised")
    for code in exp_warn:
        if code not in actual_warn:
            problems.append(f"expected warning {code} not raised")
    if kind == "valid" and actual_err:
        problems.append(f"valid fixture has errors: {sorted(actual_err)}")

    directory = FIXTURES / kind / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "ltp-model.yaml").write_text(dump_model(model), encoding="utf-8")
    expected = {
        "description": description,
        "publishable": report.is_publishable,
        "expected_errors": sorted(exp_err),
        "expected_warnings": sorted(exp_warn),
    }
    (directory / "expected.yaml").write_text(
        yaml.safe_dump(expected, sort_keys=True, default_flow_style=False), encoding="utf-8"
    )
    status = "OK  " if not problems else "FAIL"
    detail = "" if not problems else " -- " + "; ".join(problems)
    print(f"  [{status}] {kind}/{name}  err={sorted(actual_err)} warn={sorted(actual_warn)}{detail}")
    return "" if not problems else f"{kind}/{name}: {'; '.join(problems)}"


def main() -> int:
    failures = []
    print("valid fixtures:")
    for name, desc, fn, exp_err, exp_warn in VALID:
        failures.append(_write("valid", name, desc, fn(), exp_err, exp_warn))
    print("invalid fixtures:")
    for name, desc, fn, exp_err, exp_warn in INVALID:
        failures.append(_write("invalid", name, desc, fn(), exp_err, exp_warn))
    failures = [f for f in failures if f]
    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("\nall fixtures generated and self-checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
