"""Derive the attention queue and blocking learning obligations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from .enums import ImplementationStatus, PredictionEvaluationResult
from .models import LtpModel
from .predictions import evaluate_prediction, parse_date, prediction_due_date


@dataclass(frozen=True)
class LearningObligation:
    id: str
    kind: str
    target: str
    due_at: str
    next_action: str
    owner: Optional[str] = None
    blocking: bool = True


def derive_obligations(model: LtpModel, *, as_of: str) -> "list[LearningObligation]":
    current = parse_date(as_of)
    obligations: "list[LearningObligation]" = []
    for prediction in sorted(model.predicted_effects, key=lambda item: item.id):
        if prediction.waived:
            continue
        evaluation = evaluate_prediction(prediction, model.observations, as_of=as_of)
        review = parse_date(prediction.review_by) if prediction.review_by else None
        matching = [
            item
            for item in model.observations
            if item.prediction == prediction.id and parse_date(item.observed_at) <= current
        ]
        latest = max(matching, key=lambda item: parse_date(item.observed_at), default=None)

        if (
            review is not None
            and current > review
            and evaluation.observation is None
            and evaluation.result == PredictionEvaluationResult.INCONCLUSIVE
        ):
            obligations.append(
                LearningObligation(
                    id=f"OBL-{prediction.id}-EVALUATE",
                    kind="prediction_overdue",
                    target=prediction.id,
                    due_at=review.isoformat(),
                    owner=prediction.owner,
                    next_action="admit a qualifying observation and evaluate the prediction",
                )
            )

        due = prediction_due_date(prediction)
        if (
            prediction.implementation_status == ImplementationStatus.COMPLETE
            and prediction.implemented_at
            and evaluation.observation is None
            and due is not None
            and current >= due
        ):
            obligations.append(
                LearningObligation(
                    id=f"OBL-{prediction.id}-VERIFY",
                    kind="intervention_unverified",
                    target=prediction.id,
                    due_at=due.isoformat(),
                    owner=prediction.owner,
                    next_action="record an outcome observation after implementation",
                )
            )

        if latest is not None and prediction.observation_valid_for_days is not None:
            stale_at = parse_date(latest.observed_at) + timedelta(
                days=prediction.observation_valid_for_days
            )
            if current > stale_at:
                obligations.append(
                    LearningObligation(
                        id=f"OBL-{prediction.id}-REFRESH",
                        kind="observation_stale",
                        target=prediction.id,
                        due_at=stale_at.isoformat(),
                        owner=prediction.owner,
                        next_action="refresh the operational observation",
                    )
                )
    unique = {item.id: item for item in obligations}
    return sorted(unique.values(), key=lambda item: (item.due_at, item.kind, item.id))
