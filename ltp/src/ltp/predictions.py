"""Pure causal-outcome evaluation.

This module deliberately has no clock or I/O dependency.  Callers supply the
as-of date and admitted observations; the resulting record can therefore be
recomputed byte-for-byte in CI and in historical projections.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, Optional

from .enums import PredictedResult, PredictionEvaluationResult
from .models import Observation, PredictedEffect, PredictionEvaluation


def parse_date(value: str) -> date:
    """Parse an ISO date or datetime, accepting the common trailing ``Z``."""
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return date.fromisoformat(normalized)
    except ValueError:
        return datetime.fromisoformat(normalized).date()


def _latest(
    observations: Iterable[Observation],
    prediction: str,
    as_of: date,
    *,
    floor: Optional[date] = None,
) -> Optional[Observation]:
    """The newest admitted observation in ``[floor, as_of]``.

    ``floor`` excludes readings taken before the intervention could have had any
    effect (its implementation date): a measurement from before the cause was in
    place is not evidence of the cause's outcome.
    """
    eligible = [
        item
        for item in observations
        if item.prediction == prediction
        and parse_date(item.observed_at) <= as_of
        and (floor is None or parse_date(item.observed_at) >= floor)
    ]
    return max(eligible, key=lambda item: (parse_date(item.observed_at), item.id), default=None)


def prediction_due_date(prediction: PredictedEffect) -> Optional[date]:
    """Resolve the expected-outcome date from explicit date or implementation lag."""
    if prediction.expected_by:
        return parse_date(prediction.expected_by)
    if prediction.implemented_at and prediction.expected_lag_days is not None:
        return parse_date(prediction.implemented_at) + timedelta(days=prediction.expected_lag_days)
    if prediction.review_by:
        return parse_date(prediction.review_by)
    return None


def _numeric_result(prediction: PredictedEffect, observed: float) -> PredictionEvaluationResult:
    expected = prediction.expected_change_percent
    if expected is None:
        return PredictionEvaluationResult.INCONCLUSIVE
    tolerance = max(0.0, prediction.tolerance_percent)
    if expected < 0:
        # A predicted decrease is supported only by an actual decrease. Tolerance
        # widens the magnitude bar but can never push it across zero into an
        # increase, so a wrong-direction reading can never read "supported".
        if observed <= min(0.0, expected + tolerance):
            return PredictionEvaluationResult.SUPPORTED
        if observed < 0:
            return PredictionEvaluationResult.INCONCLUSIVE
        return PredictionEvaluationResult.CONTRADICTED
    if expected > 0:
        if observed >= max(0.0, expected - tolerance):
            return PredictionEvaluationResult.SUPPORTED
        if observed > 0:
            return PredictionEvaluationResult.INCONCLUSIVE
        return PredictionEvaluationResult.CONTRADICTED
    return (
        PredictionEvaluationResult.SUPPORTED
        if abs(observed) <= tolerance
        else PredictionEvaluationResult.CONTRADICTED
    )


def evaluate_prediction(
    prediction: PredictedEffect,
    observations: Iterable[Observation],
    *,
    as_of: str,
) -> PredictionEvaluation:
    """Evaluate one prediction without changing the model or its CLR state."""
    current = parse_date(as_of)
    due = prediction_due_date(prediction)
    if due and current < due:
        return PredictionEvaluation(
            id=f"EVAL-{prediction.id}",
            prediction=prediction.id,
            as_of=current.isoformat(),
            result=PredictionEvaluationResult.NOT_YET_DUE,
            explanation=f"expected outcome is not due until {due.isoformat()}",
        )

    observation = _latest(
        observations,
        prediction.id,
        current,
        floor=parse_date(prediction.implemented_at) if prediction.implemented_at else None,
    )
    if observation is None:
        return PredictionEvaluation(
            id=f"EVAL-{prediction.id}",
            prediction=prediction.id,
            as_of=current.isoformat(),
            result=PredictionEvaluationResult.INCONCLUSIVE,
            explanation="no qualifying observation has been admitted",
        )

    if prediction.minimum_fidelity is not None:
        fidelity = prediction.implementation_fidelity
        if fidelity is None or fidelity < prediction.minimum_fidelity:
            return PredictionEvaluation(
                id=f"EVAL-{prediction.id}",
                prediction=prediction.id,
                observation=observation.id,
                as_of=current.isoformat(),
                result=PredictionEvaluationResult.INCONCLUSIVE,
                explanation="implementation fidelity does not satisfy the prediction conditions",
            )

    if observation.change_percent is not None and prediction.expected_change_percent is not None:
        result = _numeric_result(prediction, observation.change_percent)
    elif observation.result == PredictedResult.OBSERVED:
        result = PredictionEvaluationResult.SUPPORTED
    elif observation.result == PredictedResult.ABSENT:
        result = PredictionEvaluationResult.CONTRADICTED
    else:
        result = PredictionEvaluationResult.INCONCLUSIVE
    return PredictionEvaluation(
        id=f"EVAL-{prediction.id}",
        prediction=prediction.id,
        observation=observation.id,
        as_of=current.isoformat(),
        result=result,
        explanation="derived from the latest qualifying observation",
    )


def evaluate_all(model, *, as_of: str) -> "list[PredictionEvaluation]":
    return [
        evaluate_prediction(prediction, model.observations, as_of=as_of)
        for prediction in sorted(model.predicted_effects, key=lambda item: item.id)
    ]
