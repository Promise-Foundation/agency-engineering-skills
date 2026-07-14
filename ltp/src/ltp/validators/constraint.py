"""Constraint validation (CON-*).

A root cause explains undesirable effects; a constraint limits throughput toward
the goal. They can coincide, but only if demonstrated. ``current_constraint``
must point at a constraint-kind entity backed by a limiting-mechanism argument
against a stated goal measure, with alternatives considered.
"""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..enums import EntityKind
from ..models import LtpModel, ModelIndex


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []
    current = model.analysis.current_constraint
    assessment = model.constraint_assessment
    if not current and assessment is None:
        return out

    ties_current = (
        assessment is not None
        and current is not None
        and assessment.entity == current
        and bool(assessment.limiting_mechanism)
    )

    if current:
        kind = index.kind_of(current)
        if kind == EntityKind.ROOT_CAUSE:
            if not ties_current:
                out.append(
                    diagnostic(
                        "CON-006",
                        f"root cause {current} is used as the constraint without a "
                        "constraint_assessment demonstrating it limits the goal "
                        "measure",
                        target=current,
                    )
                )
        elif kind is not None and kind != EntityKind.CONSTRAINT:
            out.append(
                diagnostic(
                    "CON-001",
                    f"current_constraint {current} has kind {kind.value}, not "
                    "constraint",
                    target=current,
                )
            )

        # CON-002: a constraint needs a limiting-mechanism argument.
        if not ties_current:
            out.append(
                diagnostic(
                    "CON-002",
                    f"current constraint {current} is not backed by a "
                    "limiting-mechanism argument",
                    target=current,
                    hint="add a constraint_assessment with entity="
                    f"{current} and a limiting_mechanism",
                )
            )

    if assessment is not None:
        if assessment.goal_measure is None:
            out.append(
                diagnostic(
                    "CON-003",
                    "constraint assessment has no goal/progress measure",
                    target=assessment.entity,
                    hint="state what improvement would actually move (name, unit, "
                    "period)",
                )
            )
        if not assessment.alternative_candidates:
            out.append(
                diagnostic(
                    "CON-004",
                    "constraint assessment considered no alternative constraints",
                    target=assessment.entity,
                    hint="a constraint claim is only credible against rejected "
                    "alternatives",
                )
            )
        if assessment.focusing_step is None:
            out.append(
                diagnostic(
                    "CON-005",
                    "constraint assessment states no Five Focusing Steps posture",
                    target=assessment.entity,
                    hint="record focusing_step.current: identify|exploit|subordinate|"
                    "elevate",
                )
            )

    return out
