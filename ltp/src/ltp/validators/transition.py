"""Transition Tree validation (TT-*).

A transition is existing reality -> need -> action -> immediate effect ->
advanced IO. Its granularity matters: an action that bundles several
independently verifiable changes, or that implements a whole injection at once,
is flagged. The model may hold many transitions while ``recommended_next_action``
selects exactly one.
"""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..enums import EntityKind
from ..models import LtpModel, ModelIndex
from . import graph


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []
    if not model.transitions:
        return out

    combined = graph.combined_adjacency(model)
    goal = graph.selected_goal(model, index)
    injection_ids = {inj.id for inj in index.of_kind(EntityKind.INJECTION)}

    for transition in model.transitions:
        action = index.entities.get(transition.action)

        # TT-007: an immediate observable effect is mandatory.
        if not transition.immediate_effect:
            out.append(
                diagnostic(
                    "TT-007",
                    f"transition {transition.id} has no immediate observable effect",
                    target=transition.id,
                    hint="add an immediate_effect entity the action produces at once",
                )
            )

        # TT-004: a transition advances an IO, not a whole injection.
        if index.kind_of(transition.advances) == EntityKind.INJECTION:
            out.append(
                diagnostic(
                    "TT-004",
                    f"transition {transition.id} advances injection "
                    f"{transition.advances} directly; a transition should advance an "
                    "intermediate objective",
                    target=transition.id,
                )
            )
        elif action is not None and "implement the injection" in action.statement.lower():
            out.append(
                diagnostic(
                    "TT-004",
                    f"transition {transition.id} action implements the whole "
                    "injection in one step",
                    target=transition.id,
                )
            )

        # TT-003: the action must be a single reviewable change.
        if action is not None and graph.looks_multi_change(
            action.statement, transition.likely_scope
        ):
            out.append(
                diagnostic(
                    "TT-003",
                    f"transition {transition.id} action contains multiple "
                    f"independently verifiable changes: {action.statement!r}",
                    target=transition.id,
                    hint="split it into one transition per reviewable change",
                )
            )

        # TT-005 / TT-006: reviewability signals.
        if transition.verification is None:
            out.append(
                diagnostic(
                    "TT-005",
                    f"transition {transition.id} has no verification method",
                    target=transition.id,
                )
            )
        if not transition.likely_scope:
            out.append(
                diagnostic(
                    "TT-006",
                    f"transition {transition.id} names no likely scope (files or "
                    "components)",
                    target=transition.id,
                )
            )

        # TT-002: what the transition advances must lead onward to the goal or an
        # injection -- otherwise it advances a dead end.
        if goal or injection_ids:
            reach = graph.reachable(combined, transition.advances)
            reach.add(transition.advances)
            reaches_goal = bool(goal) and goal in reach
            reaches_injection = bool(reach & injection_ids)
            if not reaches_goal and not reaches_injection:
                out.append(
                    diagnostic(
                        "TT-002",
                        f"transition {transition.id} advances {transition.advances}, "
                        "which has no onward path to an injection or the goal",
                        target=transition.id,
                    )
                )

    return out
