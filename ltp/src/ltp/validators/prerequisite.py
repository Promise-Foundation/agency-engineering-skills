"""Prerequisite Tree validation (PRT-*).

Every obstacle is overcome by an intermediate objective; every IO is a
*condition* (not an imperative action); IOs are ordered by necessity, and each
unsatisfied IO has a path to the injection it enables.
"""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..enums import EntityKind, Satisfaction
from ..models import LtpModel, ModelIndex
from . import graph


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []
    obstacles = index.of_kind(EntityKind.OBSTACLE)
    ios = index.of_kind(EntityKind.INTERMEDIATE_OBJECTIVE)
    if not obstacles and not ios and not model.obstacle_resolutions:
        return out

    resolved_obstacles = {res.obstacle for res in model.obstacle_resolutions}
    ios_with_resolution = {res.intermediate_objective for res in model.obstacle_resolutions}
    necessity = graph.necessity_adjacency(model)
    prereqs = {claim.prerequisite for claim in model.necessity_claims}
    objectives = {claim.objective for claim in model.necessity_claims}
    injection_ids = {inj.id for inj in index.of_kind(EntityKind.INJECTION)}
    advanced = {transition.advances for transition in model.transitions}

    # PRT-001: every obstacle needs an intermediate objective.
    for obstacle in obstacles:
        if obstacle.id not in resolved_obstacles:
            out.append(
                diagnostic(
                    "PRT-001",
                    f"obstacle {obstacle.id} has no intermediate objective to "
                    "overcome it",
                    target=obstacle.id,
                    hint="add an obstacle_resolution pairing it with an IO",
                )
            )

    for io in ios:
        # PRT-002: a mid-tree IO should overcome a named obstacle.
        if io.id not in ios_with_resolution and io.id in prereqs:
            out.append(
                diagnostic(
                    "PRT-002",
                    f"IO {io.id} overcomes no named obstacle",
                    target=io.id,
                )
            )
        # PRT-003: an IO is a condition, not an imperative action.
        if graph.looks_imperative(io.statement):
            out.append(
                diagnostic(
                    "PRT-003",
                    f"IO {io.id} reads as an action, not a condition: "
                    f"{io.statement!r}",
                    target=io.id,
                    hint="state the condition that will hold (e.g. 'the encoder is "
                    "deterministic'), not the task",
                )
            )
        # PRT-004: an IO connected to nothing at all.
        connected = (
            io.id in prereqs
            or io.id in objectives
            or io.id in ios_with_resolution
            or io.id in advanced
        )
        if not connected:
            out.append(
                diagnostic(
                    "PRT-004",
                    f"IO {io.id} is disconnected: no obstacle, no ordering, and no "
                    "transition advances it",
                    target=io.id,
                )
            )

    # PRT-006: every unsatisfied IO must have a dependency path to an injection.
    if injection_ids:
        for io in ios:
            if io.satisfaction == Satisfaction.SATISFIED:
                continue
            if not (graph.reachable(necessity, io.id) & injection_ids):
                out.append(
                    diagnostic(
                        "PRT-006",
                        f"unsatisfied IO {io.id} has no dependency path to any "
                        "injection",
                        target=io.id,
                        hint="add necessity_claims ordering it toward the injection "
                        "it enables",
                    )
                )

    return out
