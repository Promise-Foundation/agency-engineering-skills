"""The controlled vocabularies of the LTP model.

Every enum here is closed: an authored model that uses a value outside these
sets is a *structural* error, surfaced with the list of allowed values. This is
the first thing the old permissive schema got wrong -- ``type``, ``relation``,
and ``logic`` were free strings, so a model could name anything and still parse.
"""

from __future__ import annotations

from enum import Enum


class _Vocabulary(str, Enum):
    """A string enum whose members render as their plain string value.

    Subclassing ``str`` means ``json.dumps`` and YAML emit the value directly
    and ``member == "value"`` holds, which keeps serialization boring.
    """

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return str(self.value)

    @classmethod
    def values(cls) -> "list[str]":
        return [member.value for member in cls]


class EntityKind(_Vocabulary):
    """What a node *is*. Structure and semantics both key off the kind."""

    GOAL = "goal"
    CRITICAL_SUCCESS_FACTOR = "critical_success_factor"
    NECESSARY_CONDITION = "necessary_condition"
    UNDESIRABLE_EFFECT = "undesirable_effect"
    CAUSE = "cause"
    ROOT_CAUSE = "root_cause"
    CONSTRAINT = "constraint"
    CLOUD_OBJECTIVE = "cloud_objective"
    CLOUD_NEED = "cloud_need"
    CLOUD_ACTION = "cloud_action"
    INJECTION = "injection"
    DESIRABLE_EFFECT = "desirable_effect"
    NEGATIVE_BRANCH = "negative_branch"
    TRIMMING_INJECTION = "trimming_injection"
    OBSTACLE = "obstacle"
    INTERMEDIATE_OBJECTIVE = "intermediate_objective"
    EXISTING_REALITY = "existing_reality"
    NEED = "need"
    TRANSITION_ACTION = "transition_action"
    IMMEDIATE_EFFECT = "immediate_effect"
    ASSUMPTION = "assumption"
    RISK = "risk"


# Goal-Tree condition kinds: the enduring conditions a goal decomposes into.
GOAL_TREE_KINDS = frozenset(
    {
        EntityKind.GOAL,
        EntityKind.CRITICAL_SUCCESS_FACTOR,
        EntityKind.NECESSARY_CONDITION,
    }
)
# Kinds that legitimately participate as a cause or effect in a sufficiency claim.
CAUSAL_KINDS = frozenset(
    {
        EntityKind.UNDESIRABLE_EFFECT,
        EntityKind.CAUSE,
        EntityKind.ROOT_CAUSE,
        EntityKind.CONSTRAINT,
        EntityKind.INJECTION,
        EntityKind.DESIRABLE_EFFECT,
        EntityKind.NEGATIVE_BRANCH,
        EntityKind.TRIMMING_INJECTION,
        EntityKind.IMMEDIATE_EFFECT,
    }
)


class Basis(_Vocabulary):
    """Epistemic origin -- where the statement came from.

    Deliberately separate from :class:`ReviewStatus`: how a claim entered the
    model is not the same as what later scrutiny concluded about it.
    """

    OBSERVED = "observed"
    INFERRED = "inferred"
    PROVISIONAL = "provisional"


class ReviewStatus(_Vocabulary):
    """What scrutiny (self, peer, or user) has concluded so far."""

    UNREVIEWED = "unreviewed"
    CORROBORATED = "corroborated"
    USER_CONFIRMED = "user_confirmed"
    DISPUTED = "disputed"
    INVALIDATED = "invalidated"
    SUPERSEDED = "superseded"


class Confidence(_Vocabulary):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Satisfaction(_Vocabulary):
    """Whether a condition currently holds. Distinct from confidence in it."""

    UNKNOWN = "unknown"
    SATISFIED = "satisfied"
    PARTIAL = "partial"
    UNSATISFIED = "unsatisfied"
    NOT_APPLICABLE = "not_applicable"


class Influence(_Vocabulary):
    """Controllability. A necessary condition is not excluded for being
    outside the project's control; it is kept and marked ``monitor``/``outside``."""

    CONTROL = "control"
    INFLUENCE = "influence"
    MONITOR = "monitor"
    OUTSIDE = "outside"


class Operator(_Vocabulary):
    """How premises combine to deliver an effect in a sufficiency claim.

    ``all`` is the load-bearing one: sufficiency means *all* contributing
    causes together deliver the effect, which the renderer draws as a single
    AND gate -- never as two independent arrows that each look sufficient.
    """

    SINGLE = "single"
    ALL = "all"
    ANY = "any"
    EXCLUSIVE_ANY = "exclusive_any"
    MAGNITUDINAL = "magnitudinal"


class CLRState(_Vocabulary):
    """Result of one Category of Legitimate Reservation check."""

    NOT_APPLICABLE = "not_applicable"
    UNTESTED = "untested"
    OPEN = "open"
    PASS = "pass"
    FAIL = "fail"


class Expectation(_Vocabulary):
    SHOULD_EXIST = "should_exist"
    SHOULD_NOT_EXIST = "should_not_exist"


class PredictedResult(_Vocabulary):
    UNTESTED = "untested"
    OBSERVED = "observed"
    ABSENT = "absent"
    MIXED = "mixed"


class SemanticRelationType(_Vocabulary):
    """Non-sufficiency relationships that must not masquerade as causal arrows."""

    CAUSES = "causes"
    REQUIRES = "requires"
    ENABLES = "enables"
    CONTRIBUTES_TO = "contributes_to"
    PREVENTS = "prevents"
    MITIGATES = "mitigates"
    NEUTRALIZES = "neutralizes"
    DETECTS = "detects"
    RESPONDS_TO = "responds_to"
    EVIDENCES = "evidences"
    TESTS = "tests"
    IMPLEMENTS = "implements"
    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"


class PredictionEvaluationResult(_Vocabulary):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"
    NOT_YET_DUE = "not_yet_due"


class ImplementationStatus(_Vocabulary):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class AnalysisMode(_Vocabulary):
    FORWARD = "forward"
    REVERSE = "reverse"
    RECONCILIATION = "reconciliation"


class OperatingMode(_Vocabulary):
    """Which tools an analysis plans to build. A full analysis decides which
    views are *warranted*; it does not manufacture every diagram."""

    DIAGNOSE = "diagnose"
    RESOLVE_CONFLICT = "resolve_conflict"
    PLAN_CHANGE = "plan_change"
    FULL = "full"
    RECONCILE = "reconcile"


class PlanStatus(_Vocabulary):
    REQUIRED = "required"
    DONE = "done"
    DEFERRED = "deferred"
    SKIPPED = "skipped"


class CloudStatus(_Vocabulary):
    CANDIDATE = "candidate"
    VALIDATED_PERSISTENT_CONFLICT = "validated_persistent_conflict"
    REJECTED = "rejected"


class ConflictAnalysisStatus(_Vocabulary):
    NO_VALIDATED_PERSISTENT_CONFLICT = "no_validated_persistent_conflict"
    VALIDATED_PERSISTENT_CONFLICT = "validated_persistent_conflict"


class AssessmentStatus(_Vocabulary):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"


class FocusingStep(_Vocabulary):
    """The Five Focusing Steps posture toward the constraint."""

    IDENTIFY = "identify"
    EXPLOIT = "exploit"
    SUBORDINATE = "subordinate"
    ELEVATE = "elevate"
    INERTIA = "inertia"


class TransitionSize(_Vocabulary):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class EmpiricalStatus(_Vocabulary):
    """The empirical standing of a claim, imported from ``hypothesize``.

    Kept strictly apart from a claim's *logical* status (derived from CLR): a
    passing test proves behavior exists, never that the modelled causation holds.
    """

    NOT_TESTED = "not_tested"
    SUPPORTED = "supported"
    FALSIFIED = "falsified"
    INCONCLUSIVE = "inconclusive"


class VerificationRole(_Vocabulary):
    """The role a linked ``hypothesize`` hypothesis plays for an LTP claim.

    A green test may prove an injection *exists*; it does not prove the
    injection *causes* the modelled effect. The role keeps that honest.
    """

    ENTITY_EXISTENCE = "entity_existence"
    MECHANISM = "mechanism"
    CAUSAL_OUTCOME = "causal_outcome"
    SCIENTIFIC_OUTCOME = "scientific_outcome"
    NEGATIVE_BRANCH_GUARDRAIL = "negative_branch_guardrail"
    PREREQUISITE_READINESS = "prerequisite_readiness"
    TRANSITION_ACCEPTANCE = "transition_acceptance"


# Canonical view keys the renderer and dashboard understand.
VIEW_KEYS = (
    "goal-tree",
    "current-reality",
    "evaporating-cloud",
    "future-reality",
    "prerequisite-tree",
    "transition-tree",
)
