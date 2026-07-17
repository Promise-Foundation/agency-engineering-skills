"""Cross-tree consistency (XTR-*).

The trees are views of one model, so the model has to hold together across them:
injections connect to the diagnosed problem, the recommended action has a real
path to the goal, and nothing is left floating.
"""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..enums import EntityKind
from ..models import LtpModel, ModelIndex
from . import graph


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []
    combined = graph.combined_adjacency(model)
    goal = graph.selected_goal(model, index)

    # XTR-003: an injection must connect back to the diagnosed problem -- either
    # it resolves a cloud, or it breaks an assumption that a CRT claim relies on.
    udes_present = bool(index.of_kind(EntityKind.UNDESIRABLE_EFFECT))
    clouds_present = bool(model.clouds)
    if udes_present or clouds_present:
        crt_assumptions: "set[str]" = set()
        for claim in model.causal_claims:
            if index.kind_of(claim.conclusion) == EntityKind.UNDESIRABLE_EFFECT:
                crt_assumptions.update(claim.assumption_refs)
        cloud_injections: "set[str]" = set()
        for cloud in model.clouds:
            cloud_injections.update(cloud.injection_refs)
        injection_assumptions: "dict[str, set[str]]" = {}
        for claim in model.causal_claims:
            for premise in claim.premises:
                if index.kind_of(premise) == EntityKind.INJECTION:
                    injection_assumptions.setdefault(premise, set()).update(
                        claim.assumption_refs
                    )
        for injection in index.of_kind(EntityKind.INJECTION):
            grounded = (
                injection.id in cloud_injections
                or bool(injection_assumptions.get(injection.id, set()) & crt_assumptions)
            )
            if not grounded:
                out.append(
                    diagnostic(
                        "XTR-003",
                        f"injection {injection.id} resolves no cloud and breaks no "
                        "assumption the current reality relies on",
                        target=injection.id,
                        hint="tie it to a cloud (injection_refs) or share an "
                        "assumption with a CRT claim",
                    )
                )

    # XTR-004: the recommended next action must reach the goal.
    action_id = model.analysis.recommended_next_action
    if action_id and goal:
        transition = index.transitions.get(action_id)
        if transition is not None:
            reach = graph.reachable(combined, transition.advances)
            reach.add(transition.advances)
            if goal not in reach:
                out.append(
                    diagnostic(
                        "XTR-004",
                        f"recommended action {action_id} advances "
                        f"{transition.advances}, which has no complete path to goal "
                        f"{goal}",
                        target=action_id,
                    )
                )

    # XTR-005: an entity that participates in nothing.
    used: "set[str]" = set()
    for claim in model.causal_claims:
        used.update(claim.premises)
        used.add(claim.conclusion)
        used.update(claim.assumption_refs)
    for claim in model.necessity_claims:
        used.add(claim.prerequisite)
        used.add(claim.objective)
        used.update(claim.assumption_refs)
    for cloud in model.clouds:
        used.update(
            [cloud.objective, cloud.need_b, cloud.need_c, cloud.action_d, cloud.action_d_prime]
        )
        used.update(cloud.injection_refs)
    for conflict in model.conflict_claims:
        used.update(conflict.assumption_refs)
    for resolution in model.obstacle_resolutions:
        used.add(resolution.obstacle)
        used.add(resolution.intermediate_objective)
    for relation in model.semantic_relations:
        used.add(relation.source)
        used.add(relation.target)
    for transition in model.transitions:
        used.update(
            filter(
                None,
                [
                    transition.action,
                    transition.advances,
                    transition.existing_reality,
                    transition.need,
                    transition.immediate_effect,
                ],
            )
        )
        used.update(transition.precondition_refs)
        used.update(transition.risk_refs)
    for pred in model.predicted_effects:
        pass  # predicted effects reference claims, not entities directly
    for entity in model.entities:
        used.update(entity.assumption_refs)
    assessment = model.constraint_assessment
    if assessment is not None:
        used.add(assessment.entity)
        used.update(alt.entity for alt in assessment.alternative_candidates)
    for value in (
        model.project.goal,
        model.project.provisional_goal,
        model.analysis.current_constraint,
        model.analysis.expected_effect,
    ):
        if value:
            used.add(value)

    for entity in model.entities:
        if entity.id not in used:
            out.append(
                diagnostic(
                    "XTR-005",
                    f"entity {entity.id} ({entity.kind.value}) participates in no "
                    "claim, cloud, transition, or analysis field",
                    target=entity.id,
                )
            )

    return out
