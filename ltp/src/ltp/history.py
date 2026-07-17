"""Semantic learning-history read model.

The projector consumes records that already exist (model revisions, Promisify
assessments, Hypothesize snapshots, and prediction evaluations).  It owns no
write path and copies no source into a second authoritative journal.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from .models import LtpModel, PredictionEvaluation, to_dict
from .predictions import parse_date


@dataclass(frozen=True)
class ModelRevision:
    occurred_at: str
    revision: str
    model: LtpModel


@dataclass(frozen=True)
class LearningEvent:
    id: str
    occurred_at: str
    kind: str
    subject: str
    summary: str
    source: str
    actor: Optional[str] = None
    reason: Optional[str] = None
    previous: Optional[Any] = None
    current: Optional[Any] = None
    metadata: "dict[str, Any]" = field(default_factory=dict, compare=False, hash=False)

    def to_dict(self) -> "dict[str, Any]":
        return {
            key: value
            for key, value in {
                "id": self.id,
                "occurred_at": self.occurred_at,
                "kind": self.kind,
                "subject": self.subject,
                "summary": self.summary,
                "source": self.source,
                "actor": self.actor,
                "reason": self.reason,
                "previous": self.previous,
                "current": self.current,
                "metadata": self.metadata,
            }.items()
            if value not in (None, {}, [])
        }


@dataclass(frozen=True)
class LearningHistory:
    events: "tuple[LearningEvent, ...]"

    def as_of(self, value: str) -> "LearningHistory":
        cutoff = parse_date(value)
        return LearningHistory(
            tuple(event for event in self.events if parse_date(event.occurred_at) <= cutoff)
        )

    def diff(self, from_date: str, to_date: str) -> "tuple[LearningEvent, ...]":
        start, end = parse_date(from_date), parse_date(to_date)
        return tuple(
            event
            for event in self.events
            if start < parse_date(event.occurred_at) <= end
        )

    def to_dict(self) -> "dict[str, Any]":
        return {"events": [event.to_dict() for event in self.events], "digest": self.digest}

    @property
    def digest(self) -> str:
        payload = json.dumps(
            [event.to_dict() for event in self.events],
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def _records(model: LtpModel) -> "dict[str, tuple[str, dict[str, Any]]]":
    result: "dict[str, tuple[str, dict[str, Any]]]" = {}
    for family in ("entities", "causal_claims", "semantic_relations", "predicted_effects"):
        for record in getattr(model, family):
            result[record.id] = (family, to_dict(record, prune=False))
    return result


def _model_events(revisions: Iterable[ModelRevision]) -> "list[LearningEvent]":
    events: "list[LearningEvent]" = []
    previous: "dict[str, tuple[str, dict[str, Any]]]" = {}
    for revision in sorted(revisions, key=lambda item: (item.occurred_at, item.revision)):
        current = _records(revision.model)
        for subject in sorted(current.keys() - previous.keys()):
            family, value = current[subject]
            events.append(
                LearningEvent(
                    id=f"git:{revision.revision}:{subject}:added",
                    occurred_at=revision.occurred_at,
                    kind="model_record_added",
                    subject=subject,
                    summary=f"{family.rstrip('s').replace('_', ' ')} {subject} added",
                    source=f"git:{revision.revision}",
                    current=value,
                )
            )
        for subject in sorted(previous.keys() - current.keys()):
            family, value = previous[subject]
            events.append(
                LearningEvent(
                    id=f"git:{revision.revision}:{subject}:removed",
                    occurred_at=revision.occurred_at,
                    kind="model_record_removed",
                    subject=subject,
                    summary=f"{family.rstrip('s').replace('_', ' ')} {subject} removed",
                    source=f"git:{revision.revision}",
                    previous=value,
                )
            )
        for subject in sorted(current.keys() & previous.keys()):
            family, value = current[subject]
            old_family, old_value = previous[subject]
            if (family, value) != (old_family, old_value):
                events.append(
                    LearningEvent(
                        id=f"git:{revision.revision}:{subject}:revised",
                        occurred_at=revision.occurred_at,
                        kind="model_record_revised",
                        subject=subject,
                        summary=f"{family.rstrip('s').replace('_', ' ')} {subject} revised",
                        source=f"git:{revision.revision}",
                        previous=old_value,
                        current=value,
                    )
                )
        previous = current
    return events


def _assessment_events(assessments: Iterable[dict[str, Any]]) -> "list[LearningEvent]":
    events: "list[LearningEvent]" = []
    for assessment in assessments:
        observed = assessment.get("observed_at") or assessment.get("observedAt")
        subject = (
            assessment.get("subject")
            or assessment.get("promise")
            or assessment.get("effectiveDomain")
            or assessment.get("effective_domain")
        )
        if not observed or not subject:
            continue
        assessment_id = str(assessment.get("id") or f"{subject}:{observed}")
        verdict = assessment.get("verdict") or assessment.get("position") or "assessed"
        actor = assessment.get("assessor") or assessment.get("actor")
        events.append(
            LearningEvent(
                id=f"assessment:{assessment_id}",
                occurred_at=str(observed),
                kind="stakeholder_assessment",
                subject=str(subject),
                summary=f"{actor or 'stakeholder'} assessed {subject} as {verdict}",
                source=f"promisify:{assessment_id}",
                actor=str(actor) if actor else None,
                reason=assessment.get("rationale") or assessment.get("reservation"),
                current=verdict,
                metadata={
                    "domain": assessment.get("effectiveDomain")
                    or assessment.get("effective_domain")
                },
            )
        )
    return events


def _research_events(snapshots: Iterable[dict[str, Any]]) -> "list[LearningEvent]":
    events: "list[LearningEvent]" = []
    previous: "dict[str, Any]" = {}
    for snapshot in sorted(
        snapshots,
        key=lambda item: str(item.get("observed_at") or item.get("generated_at") or ""),
    ):
        occurred = snapshot.get("observed_at") or snapshot.get("generated_at")
        if not occurred:
            continue
        source = str(snapshot.get("revision") or snapshot.get("source") or occurred)
        for hypothesis in snapshot.get("hypotheses", []):
            subject = hypothesis.get("id")
            conclusion = hypothesis.get("conclusion")
            if not subject or conclusion is None or previous.get(subject) == conclusion:
                continue
            events.append(
                LearningEvent(
                    id=f"research:{source}:{subject}",
                    occurred_at=str(occurred),
                    kind="hypothesis_conclusion_changed",
                    subject=str(subject),
                    summary=f"hypothesis {subject} conclusion changed to {conclusion}",
                    source=f"hypothesize:{source}",
                    previous=previous.get(subject),
                    current=conclusion,
                )
            )
            previous[str(subject)] = conclusion
    return events


def project_learning_history(
    *,
    model_revisions: Iterable[ModelRevision] = (),
    assessments: Iterable[dict[str, Any]] = (),
    research_snapshots: Iterable[dict[str, Any]] = (),
    prediction_evaluations: Iterable[PredictionEvaluation] = (),
) -> LearningHistory:
    events = _model_events(model_revisions)
    events.extend(_assessment_events(assessments))
    events.extend(_research_events(research_snapshots))
    for evaluation in prediction_evaluations:
        events.append(
            LearningEvent(
                id=f"prediction:{evaluation.id}:{evaluation.as_of}",
                occurred_at=evaluation.as_of,
                kind="prediction_evaluated",
                subject=evaluation.prediction,
                summary=(
                    f"prediction {evaluation.prediction} evaluated as "
                    f"{evaluation.result.value}"
                ),
                source=evaluation.observation or evaluation.id,
                current=evaluation.result.value,
                reason=evaluation.explanation,
            )
        )
    ordered = tuple(
        sorted(events, key=lambda event: (event.occurred_at, event.kind, event.id))
    )
    return LearningHistory(ordered)
