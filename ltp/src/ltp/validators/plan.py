"""Analysis-plan consistency (PLAN-*).

The plan records which tools an analysis judged warranted. A tree marked
``required`` must have content; a tree marked ``skipped`` that nonetheless has
content is a contradiction worth noting.
"""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..enums import EntityKind, PlanStatus
from ..models import LtpModel, ModelIndex


def _content(model: LtpModel, index: ModelIndex) -> "dict[str, bool]":
    return {
        "goal-tree": bool(
            index.of_kind(
                EntityKind.GOAL,
                EntityKind.CRITICAL_SUCCESS_FACTOR,
                EntityKind.NECESSARY_CONDITION,
            )
        ),
        "current-reality": bool(
            index.of_kind(EntityKind.UNDESIRABLE_EFFECT) or model.causal_claims
        ),
        "evaporating-cloud": bool(model.clouds or model.conflict_analysis),
        "future-reality": bool(index.of_kind(EntityKind.INJECTION)),
        "prerequisite-tree": bool(
            index.of_kind(EntityKind.OBSTACLE, EntityKind.INTERMEDIATE_OBJECTIVE)
            or model.obstacle_resolutions
        ),
        "transition-tree": bool(model.transitions),
    }


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []
    content = _content(model, index)
    for name, item in model.analysis_plan.by_view().items():
        present = content[name]
        if item.status == PlanStatus.REQUIRED and not present:
            out.append(
                diagnostic(
                    "PLAN-002",
                    f"analysis plan marks {name} required, but the model has no "
                    f"{name} content",
                    target=f"analysis_plan.{name}",
                )
            )
        if item.status == PlanStatus.SKIPPED and present:
            out.append(
                diagnostic(
                    "PLAN-001",
                    f"analysis plan marks {name} skipped, but the model contains "
                    f"{name} content",
                    target=f"analysis_plan.{name}",
                )
            )
    return out
