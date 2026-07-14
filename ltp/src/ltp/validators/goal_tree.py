"""Goal Tree validation (GT-*).

A Goal Tree is the enduring conditions success requires -- not a feature list.
Project-specific detail belongs at the Necessary Condition level, so a Goal Tree
with critical success factors but no NCs (the common failure) is flagged loudly.
"""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..enums import Basis, EntityKind
from ..models import LtpModel, ModelIndex
from . import graph

MAX_TOP_LEVEL_CSFS = 5


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []

    goals = index.of_kind(EntityKind.GOAL)
    csfs = index.of_kind(EntityKind.CRITICAL_SUCCESS_FACTOR)
    ncs = index.of_kind(EntityKind.NECESSARY_CONDITION)
    if not goals and not csfs and not ncs:
        return out  # no Goal Tree in this analysis

    selected = graph.selected_goal(model, index)
    if selected is None:
        out.append(
            diagnostic(
                "GT-001",
                "no goal is selected; set project.provisional_goal (or project.goal) "
                "to a goal-kind entity",
                target="project",
            )
        )
        return out
    if index.kind_of(selected) != EntityKind.GOAL:
        out.append(
            diagnostic(
                "GT-002",
                f"selected goal {selected!r} has kind "
                f"{index.kind_of(selected).value}, not goal",  # type: ignore[union-attr]
                target=selected,
            )
        )

    necessity = graph.necessity_adjacency(model)
    # objective -> list of prerequisite entity ids (children of a condition)
    children: "dict[str, list[str]]" = {}
    for claim in model.necessity_claims:
        children.setdefault(claim.objective, []).append(claim.prerequisite)

    csf_ids = {csf.id for csf in csfs}

    # GT-003: each CSF must reach the goal by necessity.
    for csf in csfs:
        if selected not in graph.reachable(necessity, csf.id):
            out.append(
                diagnostic(
                    "GT-003",
                    f"CSF {csf.id} has no necessity path to goal {selected}",
                    target=csf.id,
                    hint="add a necessity_claim with prerequisite="
                    f"{csf.id}, objective={selected}",
                )
            )

    # GT-004: each CSF needs a child NC, or an atomic justification.
    for csf in csfs:
        child_kinds = {index.kind_of(child) for child in children.get(csf.id, [])}
        has_nc_child = EntityKind.NECESSARY_CONDITION in child_kinds
        if not has_nc_child and not csf.atomic:
            out.append(
                diagnostic(
                    "GT-004",
                    f"CSF {csf.id} has no necessary-condition child and is not "
                    "marked atomic",
                    target=csf.id,
                    hint="decompose it into NCs, or set atomic: true with an "
                    "atomic_justification",
                )
            )
        if csf.atomic and not csf.atomic_justification:
            out.append(
                diagnostic(
                    "GT-004",
                    f"CSF {csf.id} is marked atomic without an atomic_justification",
                    target=csf.id,
                )
            )

    # GT-005: each NC must reach a CSF or the goal by necessity.
    for nc in ncs:
        reach = graph.reachable(necessity, nc.id)
        if not (reach & csf_ids) and selected not in reach:
            out.append(
                diagnostic(
                    "GT-005",
                    f"NC {nc.id} has no necessity path to any CSF or the goal",
                    target=nc.id,
                )
            )

    # GT-006: every leaf condition needs an observable satisfaction criterion.
    for entity in csfs + ncs:
        is_leaf = not children.get(entity.id)
        if is_leaf and not entity.satisfaction_criterion:
            out.append(
                diagnostic(
                    "GT-006",
                    f"leaf condition {entity.id} has no observable "
                    "satisfaction_criterion",
                    target=entity.id,
                )
            )

    # GT-007: too many top-level CSFs.
    top_level = [csf for csf in csfs if selected in necessity.get(csf.id, set())]
    if len(top_level) > MAX_TOP_LEVEL_CSFS:
        out.append(
            diagnostic(
                "GT-007",
                f"{len(top_level)} CSFs sit directly under the goal "
                f"(> {MAX_TOP_LEVEL_CSFS}); high-level CSFs should be few",
                target=selected,
                hint="push project-specific detail down to the NC level",
            )
        )

    # GT-008: a CSF that is necessary for another CSF rather than the goal.
    for claim in model.necessity_claims:
        if (
            index.kind_of(claim.prerequisite) == EntityKind.CRITICAL_SUCCESS_FACTOR
            and index.kind_of(claim.objective) == EntityKind.CRITICAL_SUCCESS_FACTOR
        ):
            out.append(
                diagnostic(
                    "GT-008",
                    f"CSF {claim.prerequisite} is necessary for CSF "
                    f"{claim.objective} rather than independently for the goal",
                    target=claim.prerequisite,
                    hint="consider making it an NC beneath "
                    f"{claim.objective}",
                )
            )

    # GT-010: an NC whose necessity is unsupported by evidence or assumption.
    nc_assumptions: "dict[str, bool]" = {}
    for claim in model.necessity_claims:
        if index.kind_of(claim.prerequisite) == EntityKind.NECESSARY_CONDITION:
            nc_assumptions[claim.prerequisite] = nc_assumptions.get(
                claim.prerequisite, False
            ) or bool(claim.assumption_refs)
    for nc in ncs:
        unjustified = (
            nc.basis in (Basis.INFERRED, Basis.PROVISIONAL)
            and not nc.evidence_refs
            and not nc.assumption_refs
            and not nc_assumptions.get(nc.id, False)
        )
        if unjustified:
            out.append(
                diagnostic(
                    "GT-010",
                    f"NC {nc.id} is asserted necessary with no evidence and no "
                    "assumption; is it actually necessary, or a nice-to-have?",
                    target=nc.id,
                )
            )

    return out
