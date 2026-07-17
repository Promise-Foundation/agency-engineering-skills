"""Normalized dashboard model (``dashboard-model.json``).

The dashboard consumes *this* -- validated, derived, with compound sufficiency
already expanded into explicit gate nodes and each view's graph precomputed --
never the raw permissive YAML. It also carries the model-health diagnostics so
the dashboard can reveal logical incompleteness rather than merely draw it.
"""

from __future__ import annotations

from ..enums import CLRState, Operator
from ..models import CausalClaim, LtpModel, ModelIndex, to_dict
from ..history import project_learning_history
from ..obligations import derive_obligations
from ..predictions import evaluate_all
from .views import derive_views

_REQUIRED_PASS = ("causality_existence", "cause_effect_reversal", "tautology")


def logic_status(claim: CausalClaim) -> str:
    """Derive a claim's logical standing from its CLR review (never asserted)."""
    if claim.clr is None:
        return "candidate"
    checks = claim.clr.checks()
    if any(checks[name].result == CLRState.FAIL for name in _REQUIRED_PASS):
        return "contradicted"
    if any(check.result == CLRState.OPEN for check in checks.values()):
        return "candidate"
    applicable = [c for c in checks.values() if c.result != CLRState.NOT_APPLICABLE]
    if applicable and all(c.result == CLRState.PASS for c in applicable):
        return "scrutinized"
    return "candidate"


def _gate_id(claim: CausalClaim) -> str:
    return f"{claim.id}#gate"


def _is_compound(claim: CausalClaim) -> bool:
    return len(claim.premises) > 1 or claim.operator != Operator.SINGLE


def _view_graph(view, model: LtpModel, index: ModelIndex) -> "dict[str, object]":
    node_ids: "list[str]" = list(view.entities)
    edges: "list[dict[str, str]]" = []

    for claim_id in view.causal_claims:
        claim = index.causal_claims[claim_id]
        if _is_compound(claim):
            gate = _gate_id(claim)
            if gate not in node_ids:
                node_ids.append(gate)
            for premise in claim.premises:
                edges.append({"source": premise, "target": gate, "relation": "premise", "claim": claim.id})
            edges.append({"source": gate, "target": claim.conclusion, "relation": "causes", "claim": claim.id})
        else:
            for premise in claim.premises:
                edges.append({"source": premise, "target": claim.conclusion, "relation": "causes", "claim": claim.id})

    for claim_id in view.necessity_claims:
        claim = index.necessity_claims[claim_id]
        edges.append(
            {"source": claim.prerequisite, "target": claim.objective, "relation": "necessary_for", "claim": claim.id}
        )

    for relation_id in view.semantic_relations:
        relation = index.semantic_relations[relation_id]
        edges.append(
            {
                "source": relation.source,
                "target": relation.target,
                "relation": relation.relation.value,
                "claim": relation.id,
            }
        )

    for cloud in model.clouds:
        if cloud.id not in view.clouds:
            continue
        edges.append({"source": cloud.need_b, "target": cloud.objective, "relation": "necessary_for", "claim": cloud.id})
        edges.append({"source": cloud.need_c, "target": cloud.objective, "relation": "necessary_for", "claim": cloud.id})
        edges.append({"source": cloud.action_d, "target": cloud.need_b, "relation": "necessary_for", "claim": cloud.id})
        edges.append({"source": cloud.action_d_prime, "target": cloud.need_c, "relation": "necessary_for", "claim": cloud.id})
        edges.append({"source": cloud.action_d, "target": cloud.action_d_prime, "relation": "conflict", "claim": cloud.id})

    for res_id in view.obstacle_resolutions:
        res = index.obstacle_resolutions[res_id]
        edges.append({"source": res.obstacle, "target": res.intermediate_objective, "relation": "overcome_by", "claim": res.id})

    for transition in model.transitions:
        if transition.id not in view.transitions:
            continue
        chain = [
            transition.existing_reality,
            transition.need,
            transition.action,
            transition.immediate_effect,
            transition.advances,
        ]
        present = [eid for eid in chain if eid and eid in index.entities]
        for source, target in zip(present, present[1:]):
            edges.append({"source": source, "target": target, "relation": "then", "claim": transition.id})

    return {"node_ids": node_ids, "edges": edges}


def build_dashboard(model: LtpModel, report=None, *, as_of: str | None = None) -> "dict[str, object]":
    index = ModelIndex(model)

    entity_nodes = [to_dict(entity, prune=False) for entity in model.entities]
    gate_nodes = [
        {
            "id": _gate_id(claim),
            "is_gate": True,
            "operator": claim.operator.value,
            "claim": claim.id,
            "logic_status": logic_status(claim),
        }
        for claim in model.causal_claims
        if _is_compound(claim)
    ]

    causal = []
    for claim in model.causal_claims:
        payload = to_dict(claim, prune=False)
        payload["logic_status"] = logic_status(claim)
        causal.append(payload)

    views_out = {}
    for key, view in derive_views(model).items():
        graph = _view_graph(view, model, index)
        views_out[key] = {
            "title": view.title,
            "empty": view.is_empty,
            "node_ids": graph["node_ids"],
            "edges": graph["edges"],
        }

    dashboard: "dict[str, object]" = {
        "schema_version": model.schema_version,
        "project": to_dict(model.project, prune=False),
        "analysis": to_dict(model.analysis, prune=False),
        "analysis_plan": to_dict(model.analysis_plan, prune=False),
        "entities": entity_nodes,
        "gates": gate_nodes,
        "evidence": [to_dict(e, prune=False) for e in model.evidence],
        "necessity_claims": [to_dict(c, prune=False) for c in model.necessity_claims],
        "causal_claims": causal,
        "semantic_relations": [to_dict(r, prune=False) for r in model.semantic_relations],
        "clouds": [to_dict(c, prune=False) for c in model.clouds],
        "conflict_claims": [to_dict(c, prune=False) for c in model.conflict_claims],
        "predicted_effects": [to_dict(p, prune=False) for p in model.predicted_effects],
        "observations": [to_dict(o, prune=False) for o in model.observations],
        "obstacle_resolutions": [to_dict(r, prune=False) for r in model.obstacle_resolutions],
        "transitions": [to_dict(t, prune=False) for t in model.transitions],
        "constraint_assessment": (
            to_dict(model.constraint_assessment, prune=False)
            if model.constraint_assessment is not None
            else None
        ),
        "views": views_out,
        "open_questions": model.open_questions,
        "contradictions": model.contradictions,
        "coverage_gaps": model.coverage_gaps,
    }
    if report is not None:
        dashboard["health"] = report.to_dict()
    temporal_errors = bool(
        report is not None
        and any(item.code == "TIME-001" for item in report.diagnostics)
    )
    if as_of is not None and not temporal_errors:
        evaluations = evaluate_all(model, as_of=as_of)
        dashboard["as_of"] = as_of
        dashboard["prediction_evaluations"] = [to_dict(item, prune=False) for item in evaluations]
        dashboard["learning_obligations"] = [
            to_dict(item, prune=False) for item in derive_obligations(model, as_of=as_of)
        ]
        dashboard["learning_history"] = project_learning_history(
            prediction_evaluations=evaluations
        ).to_dict()
    return dashboard
