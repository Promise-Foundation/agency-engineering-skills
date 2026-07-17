"""Derive the six tree views from the typed model.

Views are *derived*, not authored. The model holds entities and typed claims;
each view is a deterministic projection of them. This is what kills the old
"author the same membership list in YAML and again in Markdown" drift -- there
is only one place a condition lives, and every view is computed from it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..enums import VIEW_KEYS, EntityKind
from ..models import LtpModel, ModelIndex

_CRT_KINDS = {
    EntityKind.UNDESIRABLE_EFFECT,
    EntityKind.CAUSE,
    EntityKind.ROOT_CAUSE,
    EntityKind.CONSTRAINT,
}
_FRT_KINDS = {
    EntityKind.INJECTION,
    EntityKind.DESIRABLE_EFFECT,
    EntityKind.NEGATIVE_BRANCH,
    EntityKind.TRIMMING_INJECTION,
}
_GOAL_KINDS = {
    EntityKind.GOAL,
    EntityKind.CRITICAL_SUCCESS_FACTOR,
    EntityKind.NECESSARY_CONDITION,
}


@dataclass
class DerivedView:
    key: str
    title: str
    entities: "list[str]" = field(default_factory=list)
    causal_claims: "list[str]" = field(default_factory=list)
    necessity_claims: "list[str]" = field(default_factory=list)
    clouds: "list[str]" = field(default_factory=list)
    conflict_claims: "list[str]" = field(default_factory=list)
    obstacle_resolutions: "list[str]" = field(default_factory=list)
    semantic_relations: "list[str]" = field(default_factory=list)
    transitions: "list[str]" = field(default_factory=list)
    predicted_effects: "list[str]" = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (
            self.entities
            or self.causal_claims
            or self.necessity_claims
            or self.clouds
            or self.transitions
            or self.semantic_relations
        )


VIEW_TITLES = {
    "goal-tree": "Goal Tree - what must be true",
    "current-reality": "Current Reality Tree - why it is stuck",
    "evaporating-cloud": "Evaporating Cloud - what is in tension",
    "future-reality": "Future Reality Tree - what resolves it",
    "prerequisite-tree": "Prerequisite Tree - what comes first",
    "transition-tree": "Transition Tree - what to do now",
}


def _causal_touches(claim, index: ModelIndex, kinds: "set[EntityKind]") -> bool:
    ids = list(claim.premises) + [claim.conclusion]
    return any(index.kind_of(entity_id) in kinds for entity_id in ids)


def _entities_of_causal(claims, index: ModelIndex) -> "list[str]":
    seen: "list[str]" = []
    for claim in claims:
        for entity_id in list(claim.premises) + [claim.conclusion]:
            if entity_id in index.entities and entity_id not in seen:
                seen.append(entity_id)
    return seen


def derive_views(model: LtpModel) -> "dict[str, DerivedView]":
    index = ModelIndex(model)
    views: "dict[str, DerivedView]" = {}

    # -- goal tree ------------------------------------------------------- #
    goal_entities = [e.id for e in model.entities if e.kind in _GOAL_KINDS]
    goal_set = set(goal_entities)
    goal_nec = [
        claim.id
        for claim in model.necessity_claims
        if claim.prerequisite in goal_set and claim.objective in goal_set
    ]
    views["goal-tree"] = DerivedView(
        key="goal-tree",
        title=VIEW_TITLES["goal-tree"],
        entities=goal_entities,
        necessity_claims=goal_nec,
    )

    # -- current reality ------------------------------------------------- #
    crt_claims = [c for c in model.causal_claims if _causal_touches(c, index, _CRT_KINDS)]
    crt_entities = _entities_of_causal(crt_claims, index)
    views["current-reality"] = DerivedView(
        key="current-reality",
        title=VIEW_TITLES["current-reality"],
        entities=crt_entities,
        causal_claims=[c.id for c in crt_claims],
    )

    # -- evaporating cloud ---------------------------------------------- #
    cloud_entities: "list[str]" = []
    cloud_nec: "list[str]" = []
    for cloud in model.clouds:
        for role in (
            cloud.objective,
            cloud.need_b,
            cloud.need_c,
            cloud.action_d,
            cloud.action_d_prime,
        ):
            if role not in cloud_entities:
                cloud_entities.append(role)
        cloud_nec.extend(
            [
                cloud.necessity_claims.a_requires_b,
                cloud.necessity_claims.a_requires_c,
                cloud.necessity_claims.b_requires_d,
                cloud.necessity_claims.c_requires_d_prime,
            ]
        )
    views["evaporating-cloud"] = DerivedView(
        key="evaporating-cloud",
        title=VIEW_TITLES["evaporating-cloud"],
        entities=cloud_entities,
        clouds=[cloud.id for cloud in model.clouds],
        conflict_claims=[c.id for c in model.conflict_claims],
        necessity_claims=cloud_nec,
    )

    # -- future reality -------------------------------------------------- #
    frt_claims = [c for c in model.causal_claims if _causal_touches(c, index, _FRT_KINDS)]
    frt_entities = _entities_of_causal(frt_claims, index)
    frt_relations = [
        relation
        for relation in model.semantic_relations
        if index.kind_of(relation.source) in _FRT_KINDS
        or index.kind_of(relation.target) in _FRT_KINDS
    ]
    for relation in frt_relations:
        for endpoint in (relation.source, relation.target):
            if endpoint in index.entities and endpoint not in frt_entities:
                frt_entities.append(endpoint)
    views["future-reality"] = DerivedView(
        key="future-reality",
        title=VIEW_TITLES["future-reality"],
        entities=frt_entities,
        causal_claims=[c.id for c in frt_claims],
        predicted_effects=[p.id for p in model.predicted_effects],
        semantic_relations=[relation.id for relation in frt_relations],
    )

    # -- prerequisite tree ---------------------------------------------- #
    prt_kinds = {
        EntityKind.OBSTACLE,
        EntityKind.INTERMEDIATE_OBJECTIVE,
        EntityKind.INJECTION,
    }
    prt_entities = [e.id for e in model.entities if e.kind in prt_kinds]
    prt_set = set(prt_entities)
    prt_nec = [
        claim.id
        for claim in model.necessity_claims
        if claim.prerequisite in prt_set and claim.objective in prt_set
    ]
    views["prerequisite-tree"] = DerivedView(
        key="prerequisite-tree",
        title=VIEW_TITLES["prerequisite-tree"],
        entities=prt_entities,
        obstacle_resolutions=[r.id for r in model.obstacle_resolutions],
        necessity_claims=prt_nec,
    )

    # -- transition tree ------------------------------------------------- #
    tt_entities: "list[str]" = []
    for transition in model.transitions:
        for entity_id in (
            transition.existing_reality,
            transition.need,
            transition.action,
            transition.immediate_effect,
            transition.advances,
        ):
            if entity_id and entity_id in index.entities and entity_id not in tt_entities:
                tt_entities.append(entity_id)
    views["transition-tree"] = DerivedView(
        key="transition-tree",
        title=VIEW_TITLES["transition-tree"],
        entities=tt_entities,
        transitions=[transition.id for transition in model.transitions],
    )

    return {key: views[key] for key in VIEW_KEYS}


def non_empty_views(model: LtpModel) -> "list[DerivedView]":
    return [view for view in derive_views(model).values() if not view.is_empty]
