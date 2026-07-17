"""Current and Future Reality Tree validation (CRT-*, FRT-*).

Both trees are built from the same ``causal_claims``. The CRT checks explain
observed effects; the FRT checks (which run only when the model contains
injections) test that a proposed change actually produces desirable effects that
reach the goal, and that its negative branches are handled.
"""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..enums import Basis, EntityKind, Operator, ReviewStatus
from ..models import LtpModel, ModelIndex
from . import graph

_GOAL_TREE_KINDS = {
    EntityKind.NECESSARY_CONDITION,
    EntityKind.CRITICAL_SUCCESS_FACTOR,
    EntityKind.GOAL,
}


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []
    udes = index.of_kind(EntityKind.UNDESIRABLE_EFFECT)
    injections = index.of_kind(EntityKind.INJECTION)
    nbrs = index.of_kind(EntityKind.NEGATIVE_BRANCH)
    # A negative branch is a reality-tree construct: its disposition (FRT-006) must
    # be checked even in a model with no causal claims, UDEs, or injections.
    if not model.causal_claims and not udes and not injections and not nbrs:
        return out

    causal_adj = graph.causal_adjacency(model)
    combined_adj = graph.combined_adjacency(model)
    concludes = graph.causal_in(model)
    premise_of = graph.causal_premise_of(model)

    # -- Current Reality Tree ------------------------------------------- #
    for ude in udes:
        if graph.looks_like_missing_feature(ude.statement):
            out.append(
                diagnostic(
                    "CRT-001",
                    f"UDE {ude.id} is written as a missing feature, not a harmful "
                    f"effect: {ude.statement!r}",
                    target=ude.id,
                    hint="state the harm it causes now (e.g. 'users cannot complete "
                    "checkout'), not the absent capability",
                )
            )
        if ude.id not in concludes:
            out.append(
                diagnostic(
                    "CRT-002",
                    f"UDE {ude.id} has no cause leading into it",
                    target=ude.id,
                    hint="add a causal_claim whose conclusion is this UDE",
                )
            )
        if ude.basis != Basis.OBSERVED:
            out.append(
                diagnostic(
                    "CRT-003",
                    f"UDE {ude.id} has basis {ude.basis.value}; an undesirable "
                    "effect should be an observed, present-tense condition",
                    target=ude.id,
                )
            )

    cycle = graph.find_cycle(causal_adj)
    if cycle is not None:
        out.append(
            diagnostic(
                "CRT-004",
                "causal cycle: " + " -> ".join(cycle),
                target=cycle[0],
                hint="break the cycle, or model it deliberately as a feedback loop",
            )
        )

    # CRT-005: prefer root causes that explain more than one UDE.
    if len(udes) >= 2:
        ude_ids = {ude.id for ude in udes}
        for root in index.of_kind(EntityKind.ROOT_CAUSE):
            explained = graph.reachable(causal_adj, root.id) & ude_ids
            if len(explained) == 1:
                out.append(
                    diagnostic(
                        "CRT-005",
                        f"root cause {root.id} explains only one UDE "
                        f"({next(iter(explained))}); prefer a cause that explains "
                        "several",
                        target=root.id,
                    )
                )

    # CRT-007 / CRT-008: claim shape and scrutiny.
    for claim in model.causal_claims:
        if len(claim.premises) > 1 and claim.operator == Operator.SINGLE:
            out.append(
                diagnostic(
                    "CRT-007",
                    f"claim {claim.id} has {len(claim.premises)} premises but "
                    "operator 'single'; declare all/any/exclusive_any/magnitudinal",
                    target=claim.id,
                    hint="compound sufficiency must say how the premises combine",
                )
            )
        into_ude = index.kind_of(claim.conclusion) == EntityKind.UNDESIRABLE_EFFECT
        if into_ude and not claim.assumption_refs and claim.clr is None:
            out.append(
                diagnostic(
                    "CRT-008",
                    f"claim {claim.id} into a UDE has neither assumptions nor a CLR "
                    "review",
                    target=claim.id,
                )
            )

    # FRT-006: negative branches must be dispositioned -- independent of whether
    # any injection exists, since a negative branch is itself an FRT construct and
    # an undispositioned one is a defect regardless of injection presence.
    trimming_relations = {
        relation.target
        for relation in model.semantic_relations
        if index.kind_of(relation.source) == EntityKind.TRIMMING_INJECTION
        and relation.relation.value in {"prevents", "mitigates", "neutralizes"}
    }
    for nbr in index.of_kind(EntityKind.NEGATIVE_BRANCH):
        accepted = nbr.review_status in (ReviewStatus.INVALIDATED, ReviewStatus.SUPERSEDED)
        if nbr.id not in trimming_relations and not accepted:
            out.append(
                diagnostic(
                    "FRT-006",
                    f"negative branch {nbr.id} is not dispositioned by a trimming "
                    "injection or explicitly accepted",
                    target=nbr.id,
                    hint="add a trimming_injection that neutralizes it, or mark it "
                    "review_status: superseded with a reason",
                )
            )

    # -- Future Reality Tree (injection-specific checks) --------------- #
    if not injections:
        return out

    goal = graph.selected_goal(model, index)
    for injection in injections:
        if injection.id not in premise_of:
            out.append(
                diagnostic(
                    "FRT-001",
                    f"injection {injection.id} enters no causal claim; it produces "
                    "nothing",
                    target=injection.id,
                )
            )
            continue
        reach = graph.reachable(causal_adj, injection.id)
        if goal and goal in causal_adj.get(injection.id, set()):
            out.append(
                diagnostic(
                    "FRT-004",
                    f"injection {injection.id} is claimed to cause the goal "
                    f"{goal} directly; insert the desirable effects it works through",
                    target=injection.id,
                )
            )
        if not any(
            index.kind_of(node) == EntityKind.DESIRABLE_EFFECT for node in reach
        ):
            out.append(
                diagnostic(
                    "FRT-003",
                    f"injection {injection.id} has no explicit desirable-effect path",
                    target=injection.id,
                    hint="trace it through DE-* effects, not straight to a condition",
                )
            )

    # FRT-005: desirable effects must eventually support a condition.
    for de in index.of_kind(EntityKind.DESIRABLE_EFFECT):
        reach = graph.reachable(combined_adj, de.id)
        if not any(index.kind_of(node) in _GOAL_TREE_KINDS for node in reach):
            out.append(
                diagnostic(
                    "FRT-005",
                    f"desirable effect {de.id} supports no NC, CSF, or goal",
                    target=de.id,
                )
            )

    return out
