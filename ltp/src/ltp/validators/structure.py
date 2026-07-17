"""Structural validation: every reference resolves to a record of the right
kind, and ids follow their conventions.

Parsing already guaranteed shapes, closed vocabularies, and globally unique ids.
This layer runs *after* a clean parse so that all dangling references surface in
one pass rather than aborting on the first one.
"""

from __future__ import annotations

from typing import Iterable, Optional

from ..diagnostics import Diagnostic, diagnostic
from ..enums import EntityKind, SemanticRelationType
from ..ids import prefix_matches_kind
from ..models import LtpModel, ModelIndex


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []

    def entity_ref(
        ref: Optional[str],
        owner: str,
        role: str,
        kinds: "Optional[Iterable[EntityKind]]" = None,
    ) -> None:
        if not ref:
            return
        entity = index.entities.get(ref)
        if entity is None:
            out.append(
                diagnostic(
                    "REF-001",
                    f"{role} references unknown entity {ref!r}",
                    target=owner,
                )
            )
            return
        if kinds is not None and entity.kind not in set(kinds):
            allowed = ", ".join(sorted(kind.value for kind in kinds))
            out.append(
                diagnostic(
                    "REF-002",
                    f"{role} references {ref!r} (kind {entity.kind.value}); "
                    f"expected one of: {allowed}",
                    target=owner,
                )
            )

    def evidence_ref(refs: "Iterable[str]", owner: str, role: str) -> None:
        for ref in refs:
            if ref not in index.evidence:
                out.append(
                    diagnostic(
                        "REF-001",
                        f"{role} references unknown evidence {ref!r}",
                        target=owner,
                    )
                )

    def record_ref(ref: Optional[str], table: dict, family: str, owner: str, role: str) -> None:
        if ref and ref not in table:
            out.append(
                diagnostic(
                    "REF-001",
                    f"{role} references unknown {family} {ref!r}",
                    target=owner,
                )
            )

    # -- entities -------------------------------------------------------- #
    for entity in model.entities:
        evidence_ref(entity.evidence_refs, entity.id, "entity")
        for ref in entity.assumption_refs:
            entity_ref(ref, entity.id, "entity assumption", [EntityKind.ASSUMPTION])
        if not prefix_matches_kind(entity.id, entity.kind):
            out.append(
                diagnostic(
                    "ID-001",
                    f"id {entity.id!r} does not use the conventional prefix for "
                    f"kind {entity.kind.value}",
                    target=entity.id,
                )
            )

    # -- project / analysis --------------------------------------------- #
    entity_ref(model.project.provisional_goal, "project", "project.provisional_goal", [EntityKind.GOAL])
    entity_ref(model.project.goal, "project", "project.goal", [EntityKind.GOAL])
    entity_ref(model.analysis.current_constraint, "analysis", "analysis.current_constraint")
    entity_ref(model.analysis.expected_effect, "analysis", "analysis.expected_effect")
    record_ref(
        model.analysis.recommended_next_action,
        index.transitions,
        "transition",
        "analysis",
        "analysis.recommended_next_action",
    )

    # -- necessity claims ------------------------------------------------ #
    for claim in model.necessity_claims:
        entity_ref(claim.prerequisite, claim.id, "necessity prerequisite")
        entity_ref(claim.objective, claim.id, "necessity objective")
        for ref in claim.assumption_refs:
            entity_ref(ref, claim.id, "necessity assumption", [EntityKind.ASSUMPTION])

    # -- causal claims --------------------------------------------------- #
    for claim in model.causal_claims:
        for premise in claim.premises:
            entity_ref(premise, claim.id, "causal premise")
        entity_ref(claim.conclusion, claim.id, "causal conclusion")
        for ref in claim.assumption_refs:
            entity_ref(ref, claim.id, "causal assumption", [EntityKind.ASSUMPTION])
        if claim.clr is not None:
            for name, check in claim.clr.checks().items():
                evidence_ref(check.evidence_refs, claim.id, f"CLR {name}")
                if check.proposed_additional_premise:
                    entity_ref(
                        check.proposed_additional_premise,
                        claim.id,
                        f"CLR {name} proposed premise",
                    )

        trimming_premises = [
            premise
            for premise in claim.premises
            if index.kind_of(premise) == EntityKind.TRIMMING_INJECTION
        ]
        if trimming_premises and index.kind_of(claim.conclusion) == EntityKind.NEGATIVE_BRANCH:
            out.append(
                diagnostic(
                    "REL-001",
                    f"causal claim {claim.id} says trimming injection "
                    f"{', '.join(trimming_premises)} causes negative branch {claim.conclusion}",
                    target=claim.id,
                    hint="replace it with a semantic_relation whose relation is neutralizes, mitigates, or prevents",
                )
            )

    # -- semantic, non-sufficiency relations --------------------------- #
    for relation in model.semantic_relations:
        entity_ref(relation.source, relation.id, "semantic relation source")
        entity_ref(relation.target, relation.id, "semantic relation target")
        evidence_ref(relation.evidence_refs, relation.id, "semantic relation")
        if relation.relation == SemanticRelationType.CAUSES:
            out.append(
                diagnostic(
                    "REL-002",
                    f"semantic relation {relation.id} uses causes without sufficiency semantics",
                    target=relation.id,
                    hint="use a causal_claim with premises, operator, conclusion, and CLR scrutiny",
                )
            )

    # -- clouds ---------------------------------------------------------- #
    for cloud in model.clouds:
        entity_ref(cloud.objective, cloud.id, "cloud objective", [EntityKind.CLOUD_OBJECTIVE])
        entity_ref(cloud.need_b, cloud.id, "cloud need B", [EntityKind.CLOUD_NEED])
        entity_ref(cloud.need_c, cloud.id, "cloud need C", [EntityKind.CLOUD_NEED])
        entity_ref(cloud.action_d, cloud.id, "cloud action D", [EntityKind.CLOUD_ACTION])
        entity_ref(cloud.action_d_prime, cloud.id, "cloud action D'", [EntityKind.CLOUD_ACTION])
        for label, ref in (
            ("a_requires_b", cloud.necessity_claims.a_requires_b),
            ("a_requires_c", cloud.necessity_claims.a_requires_c),
            ("b_requires_d", cloud.necessity_claims.b_requires_d),
            ("c_requires_d_prime", cloud.necessity_claims.c_requires_d_prime),
        ):
            record_ref(ref, index.necessity_claims, "necessity claim", cloud.id, f"cloud {label}")
        record_ref(cloud.conflict_claim, index.conflict_claims, "conflict claim", cloud.id, "cloud conflict")
        evidence_ref(cloud.persistence_evidence, cloud.id, "cloud persistence")
        for ref in cloud.injection_refs:
            entity_ref(ref, cloud.id, "cloud injection", [EntityKind.INJECTION])

    for conflict in model.conflict_claims:
        for ref in conflict.assumption_refs:
            entity_ref(ref, conflict.id, "conflict assumption", [EntityKind.ASSUMPTION])
        evidence_ref(conflict.evidence_refs, conflict.id, "conflict")

    # -- predicted effects ---------------------------------------------- #
    for pred in model.predicted_effects:
        record_ref(pred.source_claim, index.causal_claims, "causal claim", pred.id, "predicted-effect source")
        evidence_ref(pred.evidence_refs, pred.id, "predicted effect")
        if pred.waived and not pred.waiver_reason:
            out.append(
                diagnostic(
                    "PRED-003",
                    f"predicted effect {pred.id} is waived without a reason",
                    target=pred.id,
                )
            )

    for observation in model.observations:
        record_ref(
            observation.prediction,
            index.predicted_effects,
            "predicted effect",
            observation.id,
            "observation prediction",
        )
        evidence_ref(observation.evidence_refs, observation.id, "observation")

    # -- prerequisite tree ---------------------------------------------- #
    for resolution in model.obstacle_resolutions:
        entity_ref(resolution.obstacle, resolution.id, "obstacle", [EntityKind.OBSTACLE])
        entity_ref(
            resolution.intermediate_objective,
            resolution.id,
            "intermediate objective",
            [EntityKind.INTERMEDIATE_OBJECTIVE],
        )

    # -- transitions ----------------------------------------------------- #
    for transition in model.transitions:
        entity_ref(transition.action, transition.id, "transition action", [EntityKind.TRANSITION_ACTION])
        entity_ref(
            transition.advances,
            transition.id,
            "transition advances",
            [EntityKind.INTERMEDIATE_OBJECTIVE, EntityKind.INJECTION],
        )
        entity_ref(transition.existing_reality, transition.id, "transition existing reality", [EntityKind.EXISTING_REALITY])
        entity_ref(transition.need, transition.id, "transition need", [EntityKind.NEED])
        entity_ref(transition.immediate_effect, transition.id, "transition immediate effect", [EntityKind.IMMEDIATE_EFFECT])
        for ref in transition.precondition_refs:
            entity_ref(ref, transition.id, "transition precondition", [EntityKind.INTERMEDIATE_OBJECTIVE])
        for ref in transition.risk_refs:
            entity_ref(ref, transition.id, "transition risk", [EntityKind.RISK])

    # -- constraint assessment ------------------------------------------ #
    assessment = model.constraint_assessment
    if assessment is not None:
        entity_ref(assessment.entity, "constraint_assessment", "constraint entity", [EntityKind.CONSTRAINT])
        evidence_ref(assessment.evidence_refs, "constraint_assessment", "constraint")
        for alt in assessment.alternative_candidates:
            entity_ref(alt.entity, "constraint_assessment", "alternative constraint")

    # -- authored view overrides ---------------------------------------- #
    for name, view in model.views.items():
        for ref in view.entities:
            entity_ref(ref, f"views.{name}", "view entity")
        for ref in view.claims:
            if ref not in index.causal_claims and ref not in index.necessity_claims:
                out.append(
                    diagnostic("REF-001", f"view claim references unknown claim {ref!r}", target=f"views.{name}")
                )
        for ref in view.clouds:
            record_ref(ref, index.clouds, "cloud", f"views.{name}", "view cloud")
        for ref in view.transitions:
            record_ref(ref, index.transitions, "transition", f"views.{name}", "view transition")
        for ref in view.obstacle_resolutions:
            record_ref(ref, index.obstacle_resolutions, "obstacle resolution", f"views.{name}", "view obstacle resolution")
        for ref in view.relations:
            record_ref(ref, index.semantic_relations, "semantic relation", f"views.{name}", "view semantic relation")

    return out
