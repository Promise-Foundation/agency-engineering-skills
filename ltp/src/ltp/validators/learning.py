"""Temporal learning-obligation validation against an explicit as-of date."""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..models import LtpModel, ModelIndex
from ..obligations import derive_obligations
from ..predictions import parse_date


def validate(
    model: LtpModel, index: ModelIndex, *, as_of: str | None = None
) -> "list[Diagnostic]":
    del index
    out: "list[Diagnostic]" = []
    temporal = []
    for prediction in model.predicted_effects:
        temporal.extend(
            (prediction.id, label, value)
            for label, value in (
                ("expected_by", prediction.expected_by),
                ("review_by", prediction.review_by),
                ("implemented_at", prediction.implemented_at),
            )
            if value
        )
    temporal.extend(
        (observation.id, "observed_at", observation.observed_at)
        for observation in model.observations
    )
    if as_of:
        temporal.append(("validation", "as_of", as_of))
    for owner, field, value in temporal:
        try:
            parse_date(value)
        except (TypeError, ValueError):
            out.append(
                diagnostic(
                    "TIME-001",
                    f"{field} value {value!r} is not an ISO date or datetime",
                    target=owner,
                )
            )
    if not as_of or out:
        return out
    for obligation in derive_obligations(model, as_of=as_of):
        code = {
            "prediction_overdue": "PRED-OVERDUE",
            "observation_stale": "OBS-STALE",
            "intervention_unverified": "INT-UNVERIFIED",
        }[obligation.kind]
        out.append(
            diagnostic(
                code,
                f"{obligation.kind.replace('_', ' ')}; due {obligation.due_at}",
                target=obligation.target,
                hint=obligation.next_action,
            )
        )
    return out
