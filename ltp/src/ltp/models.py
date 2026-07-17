"""The typed LTP model -- the single source of truth.

Everything downstream (validators, renderers, dashboard, the hypothesize
bridge) reads *this*, not raw YAML. The model is authored as YAML but parsed
into closed, typed dataclasses so that a value outside a vocabulary, a missing
required field, an unknown field, or a duplicate id is a structural error with a
precise location -- not something that silently parses and drifts.

Relationships are *typed claims*, never generic edges:

* ``NecessityClaim`` -- "to achieve OBJECTIVE it is necessary that PREREQUISITE
  exist" (Goal Tree, Prerequisite Tree ordering, the four arrows of a Cloud).
* ``CausalClaim`` -- "PREMISES, combined by OPERATOR, are sufficient to cause
  CONCLUSION" (Current/Future Reality Trees). ``operator: all`` is one AND gate,
  never two independently-sufficient arrows.
* ``Cloud``, ``ObstacleResolution``, ``Transition`` -- first-class structures for
  the Evaporating Cloud, Prerequisite Tree, and Transition Tree, so none of them
  collapses into a single opaque node.

Implemented with the standard library only: dataclasses for the shapes and a
small annotation-driven deserializer (:func:`_build`) for the parsing.
"""

from __future__ import annotations

from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any, Optional, Union, get_args, get_origin, get_type_hints

from .enums import (
    AnalysisMode,
    AssessmentStatus,
    Basis,
    CloudStatus,
    CLRState,
    Confidence,
    ConflictAnalysisStatus,
    EmpiricalStatus,
    EntityKind,
    Expectation,
    FocusingStep,
    Influence,
    ImplementationStatus,
    OperatingMode,
    Operator,
    PlanStatus,
    PredictedResult,
    PredictionEvaluationResult,
    ReviewStatus,
    Satisfaction,
    SemanticRelationType,
    TransitionSize,
    VerificationRole,
)
from .errors import ModelError

CURRENT_SCHEMA_VERSION = 3


# --------------------------------------------------------------------------- #
# Leaf records
# --------------------------------------------------------------------------- #
@dataclass
class Evidence:
    id: str
    source: str
    observation: str
    lines: Optional[str] = None
    interpretation: Optional[str] = None
    kind: Optional[str] = None


@dataclass
class Measure:
    """A goal / progress measure -- what improvement would actually move."""

    name: str
    unit: str
    period: Optional[str] = None


@dataclass
class ClaimVerification:
    """Link from an LTP claim to a ``hypothesize`` hypothesis.

    ``role`` records what the empirical test can and cannot establish -- a
    passing ``entity_existence`` test proves an injection exists, not that it
    causes the modelled effect.
    """

    hypothesis_ref: str
    role: VerificationRole
    statement_hash: Optional[str] = None
    # Set by the hypothesize bridge; kept apart from the CLR-derived logic status.
    empirical_status: Optional[EmpiricalStatus] = None


@dataclass
class TransitionVerification:
    """How a transition's immediate effect is confirmed."""

    kind: str  # e.g. automated_test | manual_check | metric | review
    command: Optional[str] = None
    acceptance: Optional[str] = None


@dataclass
class CLRCheck:
    """One Category of Legitimate Reservation result."""

    result: CLRState = CLRState.UNTESTED
    evidence_refs: "list[str]" = field(default_factory=list)
    reservation: Optional[str] = None
    proposed_additional_premise: Optional[str] = None


@dataclass
class CLR:
    """The eight CLR checks a sufficiency claim is scrutinized against.

    These are construction-time tests, not optional after-the-fact commentary.
    The validator does not decide causality; it verifies the review happened and
    that its conclusion is represented honestly.
    """

    clarity: CLRCheck = field(default_factory=CLRCheck)
    entity_existence: CLRCheck = field(default_factory=CLRCheck)
    causality_existence: CLRCheck = field(default_factory=CLRCheck)
    cause_insufficiency: CLRCheck = field(default_factory=CLRCheck)
    additional_cause: CLRCheck = field(default_factory=CLRCheck)
    cause_effect_reversal: CLRCheck = field(default_factory=CLRCheck)
    predicted_effect_existence: CLRCheck = field(default_factory=CLRCheck)
    tautology: CLRCheck = field(default_factory=CLRCheck)

    def checks(self) -> "dict[str, CLRCheck]":
        return {f.name: getattr(self, f.name) for f in fields(self)}


# --------------------------------------------------------------------------- #
# Entities
# --------------------------------------------------------------------------- #
@dataclass
class Entity:
    """A node in the model. Assumptions are entities too (``kind: assumption``),
    so they carry stable ids and are referenced like anything else."""

    id: str
    kind: EntityKind
    statement: str
    basis: Basis = Basis.INFERRED
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED
    confidence: Confidence = Confidence.MEDIUM
    satisfaction: Satisfaction = Satisfaction.UNKNOWN
    influence: Influence = Influence.INFLUENCE
    evidence_refs: "list[str]" = field(default_factory=list)
    assumption_refs: "list[str]" = field(default_factory=list)
    reasoning: Optional[str] = None
    # Goal-Tree leaf handling
    atomic: bool = False
    atomic_justification: Optional[str] = None
    satisfaction_criterion: Optional[str] = None
    measure: Optional[Measure] = None


# --------------------------------------------------------------------------- #
# Typed claims
# --------------------------------------------------------------------------- #
@dataclass
class NecessityClaim:
    """To achieve ``objective`` it is necessary that ``prerequisite`` exist."""

    id: str
    prerequisite: str
    objective: str
    assumption_refs: "list[str]" = field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM


@dataclass
class CausalClaim:
    """``premises`` combined by ``operator`` are sufficient to cause
    ``conclusion``. Compound sufficiency (``operator: all``) is one joint claim,
    rendered as an AND gate -- not several independently-sufficient arrows."""

    id: str
    conclusion: str
    premises: "list[str]" = field(default_factory=list)
    operator: Operator = Operator.SINGLE
    mode: str = "sufficiency"
    assumption_refs: "list[str]" = field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM
    clr: Optional[CLR] = None
    verification: Optional[ClaimVerification] = None


@dataclass
class SemanticRelation:
    """A typed relationship that is not a sufficiency claim.

    In particular, prevention and neutralisation belong here rather than in a
    ``CausalClaim`` whose forward arrow would state the opposite semantics.
    """

    id: str
    source: str
    target: str
    relation: SemanticRelationType
    evidence_refs: "list[str]" = field(default_factory=list)
    reasoning: Optional[str] = None


# --------------------------------------------------------------------------- #
# Evaporating Cloud
# --------------------------------------------------------------------------- #
@dataclass
class CloudNecessity:
    """The four necessity arrows of a Cloud, by NecessityClaim id."""

    a_requires_b: str
    a_requires_c: str
    b_requires_d: str
    c_requires_d_prime: str


@dataclass
class ConflictClaim:
    """The D <-> D' incompatibility at the base of a Cloud."""

    id: str
    statement: str
    assumption_refs: "list[str]" = field(default_factory=list)
    evidence_refs: "list[str]" = field(default_factory=list)


@dataclass
class Cloud:
    id: str
    objective: str
    need_b: str
    need_c: str
    action_d: str
    action_d_prime: str
    necessity_claims: CloudNecessity
    status: CloudStatus = CloudStatus.CANDIDATE
    conflict_claim: Optional[str] = None
    persistence_evidence: "list[str]" = field(default_factory=list)
    injection_refs: "list[str]" = field(default_factory=list)


@dataclass
class RejectedCloud:
    candidate: str
    reason: str


@dataclass
class ConflictAnalysis:
    """Recorded when no persistent conflict was found -- so the absence of a
    Cloud is a deliberate, justified decision rather than a silent omission."""

    status: ConflictAnalysisStatus
    candidates_rejected: "list[RejectedCloud]" = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Predicted effects (root-cause tests)
# --------------------------------------------------------------------------- #
@dataclass
class PredictedEffect:
    id: str
    source_claim: str
    statement: str
    expectation: Expectation = Expectation.SHOULD_EXIST
    result: PredictedResult = PredictedResult.UNTESTED
    evidence_refs: "list[str]" = field(default_factory=list)
    indicator: Optional[str] = None
    baseline: Optional[float] = None
    expected_change_percent: Optional[float] = None
    tolerance_percent: float = 0.0
    expected_by: Optional[str] = None
    review_by: Optional[str] = None
    expected_lag_days: Optional[int] = None
    owner: Optional[str] = None
    implementation_status: ImplementationStatus = ImplementationStatus.NOT_STARTED
    implemented_at: Optional[str] = None
    implementation_fidelity: Optional[float] = None
    minimum_fidelity: Optional[float] = None
    observation_valid_for_days: Optional[int] = None
    waived: bool = False
    waiver_reason: Optional[str] = None


@dataclass
class Observation:
    """An admitted observation about one prediction; never a logical verdict."""

    id: str
    prediction: str
    observed_at: str
    result: PredictedResult = PredictedResult.UNTESTED
    value: Optional[float] = None
    change_percent: Optional[float] = None
    source: Optional[str] = None
    evidence_refs: "list[str]" = field(default_factory=list)
    notes: Optional[str] = None


@dataclass(frozen=True)
class PredictionEvaluation:
    """A deterministic read-model record derived from a prediction and observations."""

    id: str
    prediction: str
    as_of: str
    result: PredictionEvaluationResult
    observation: Optional[str] = None
    explanation: Optional[str] = None


# --------------------------------------------------------------------------- #
# Prerequisite Tree
# --------------------------------------------------------------------------- #
@dataclass
class ObstacleResolution:
    id: str
    obstacle: str
    intermediate_objective: str


# --------------------------------------------------------------------------- #
# Transition Tree
# --------------------------------------------------------------------------- #
@dataclass
class Transition:
    id: str
    action: str
    advances: str
    existing_reality: Optional[str] = None
    need: Optional[str] = None
    immediate_effect: Optional[str] = None
    precondition_refs: "list[str]" = field(default_factory=list)
    verification: Optional[TransitionVerification] = None
    likely_scope: "list[str]" = field(default_factory=list)
    owner: Optional[str] = None
    estimated_size: Optional[TransitionSize] = None
    risk_refs: "list[str]" = field(default_factory=list)
    rollback: Optional[str] = None


# --------------------------------------------------------------------------- #
# Constraint assessment
# --------------------------------------------------------------------------- #
@dataclass
class AlternativeConstraint:
    entity: str
    rejected_because: str


@dataclass
class FocusingStepState:
    current: FocusingStep


@dataclass
class ConstraintAssessment:
    entity: str
    limiting_mechanism: str
    goal_measure: Optional[Measure] = None
    status: AssessmentStatus = AssessmentStatus.CANDIDATE
    evidence_refs: "list[str]" = field(default_factory=list)
    alternative_candidates: "list[AlternativeConstraint]" = field(default_factory=list)
    focusing_step: Optional[FocusingStepState] = None
    exploit_direction: Optional[str] = None
    subordinate_direction: Optional[str] = None
    elevation_direction: Optional[str] = None


# --------------------------------------------------------------------------- #
# Project-level records
# --------------------------------------------------------------------------- #
@dataclass
class Project:
    name: str
    analyzed_path: Optional[str] = None
    analysis_mode: AnalysisMode = AnalysisMode.FORWARD
    provisional_goal: Optional[str] = None
    goal: Optional[str] = None


@dataclass
class Analysis:
    current_constraint: Optional[str] = None
    recommended_next_action: Optional[str] = None
    expected_effect: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class PlanItem:
    status: PlanStatus = PlanStatus.DEFERRED
    reason: Optional[str] = None


@dataclass
class AnalysisPlan:
    """Which tools this analysis judged warranted. A full analysis decides which
    views are needed; it does not manufacture every diagram."""

    mode: Optional[OperatingMode] = None
    goal_tree: PlanItem = field(default_factory=PlanItem)
    current_reality_tree: PlanItem = field(default_factory=PlanItem)
    evaporating_cloud: PlanItem = field(default_factory=PlanItem)
    future_reality_tree: PlanItem = field(default_factory=PlanItem)
    prerequisite_tree: PlanItem = field(default_factory=PlanItem)
    transition_tree: PlanItem = field(default_factory=PlanItem)

    def by_view(self) -> "dict[str, PlanItem]":
        return {
            "goal-tree": self.goal_tree,
            "current-reality": self.current_reality_tree,
            "evaporating-cloud": self.evaporating_cloud,
            "future-reality": self.future_reality_tree,
            "prerequisite-tree": self.prerequisite_tree,
            "transition-tree": self.transition_tree,
        }


@dataclass
class View:
    """An optional authored override of a derived view. When absent, the view is
    derived deterministically from entity kinds and claims (see renderers)."""

    title: Optional[str] = None
    purpose: Optional[str] = None
    entities: "list[str]" = field(default_factory=list)
    claims: "list[str]" = field(default_factory=list)
    clouds: "list[str]" = field(default_factory=list)
    transitions: "list[str]" = field(default_factory=list)
    obstacle_resolutions: "list[str]" = field(default_factory=list)
    relations: "list[str]" = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Top-level model
# --------------------------------------------------------------------------- #
@dataclass
class LtpModel:
    project: Project
    schema_version: int = CURRENT_SCHEMA_VERSION
    analysis: Analysis = field(default_factory=Analysis)
    analysis_plan: AnalysisPlan = field(default_factory=AnalysisPlan)
    entities: "list[Entity]" = field(default_factory=list)
    evidence: "list[Evidence]" = field(default_factory=list)
    necessity_claims: "list[NecessityClaim]" = field(default_factory=list)
    causal_claims: "list[CausalClaim]" = field(default_factory=list)
    semantic_relations: "list[SemanticRelation]" = field(default_factory=list)
    clouds: "list[Cloud]" = field(default_factory=list)
    conflict_claims: "list[ConflictClaim]" = field(default_factory=list)
    conflict_analysis: Optional[ConflictAnalysis] = None
    predicted_effects: "list[PredictedEffect]" = field(default_factory=list)
    observations: "list[Observation]" = field(default_factory=list)
    obstacle_resolutions: "list[ObstacleResolution]" = field(default_factory=list)
    transitions: "list[Transition]" = field(default_factory=list)
    constraint_assessment: Optional[ConstraintAssessment] = None
    views: "dict[str, View]" = field(default_factory=dict)
    open_questions: "list[str]" = field(default_factory=list)
    contradictions: "list[str]" = field(default_factory=list)
    coverage_gaps: "list[str]" = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Any) -> "LtpModel":
        return parse_model(data)

    def to_dict(self, *, prune: bool = True) -> "dict[str, Any]":
        return to_dict(self, prune=prune)


# --------------------------------------------------------------------------- #
# Deserializer -- annotation-driven, standard library only
# --------------------------------------------------------------------------- #
_HINTS_CACHE: "dict[type, dict[str, Any]]" = {}


def _hints(cls: type) -> "dict[str, Any]":
    cached = _HINTS_CACHE.get(cls)
    if cached is None:
        cached = get_type_hints(cls)
        _HINTS_CACHE[cls] = cached
    return cached


def _typename(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true/false"
    return type(value).__name__


def _is_optional(tp: Any) -> bool:
    return get_origin(tp) is Union and type(None) in get_args(tp)


def _optional_inner(tp: Any) -> Any:
    args = [arg for arg in get_args(tp) if arg is not type(None)]
    return args[0] if len(args) == 1 else Union[tuple(args)]  # type: ignore[misc]


def _coerce_enum(enum_cls: type, value: Any, where: str) -> Any:
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        try:
            return enum_cls(value)
        except ValueError:
            pass
    allowed = ", ".join(enum_cls.values())  # type: ignore[attr-defined]
    raise ModelError(
        f"{where}: {value!r} is not a valid {enum_cls.__name__}; allowed: {allowed}"
    )


def _coerce(tp: Any, value: Any, where: str) -> Any:
    if _is_optional(tp):
        if value is None:
            return None
        return _coerce(_optional_inner(tp), value, where)

    origin = get_origin(tp)
    if origin is list:
        if not isinstance(value, list):
            raise ModelError(f"{where}: expected a list, got {_typename(value)}")
        inner = get_args(tp)[0]
        result = []
        for index, element in enumerate(value):
            label = f"{where}[{index}]"
            if isinstance(element, dict) and isinstance(element.get("id"), str):
                label = f"{where}[{element['id']}]"
            result.append(_coerce(inner, element, label))
        return result
    if origin is dict:
        if not isinstance(value, dict):
            raise ModelError(f"{where}: expected a mapping, got {_typename(value)}")
        value_type = get_args(tp)[1]
        return {
            str(key): _coerce(value_type, sub, f"{where}.{key}")
            for key, sub in value.items()
        }

    if isinstance(tp, type) and issubclass(tp, Enum):
        return _coerce_enum(tp, value, where)
    if is_dataclass(tp):
        return _build(tp, value, where)
    if tp is Any:
        return value
    if tp is str:
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        raise ModelError(f"{where}: expected text, got {_typename(value)}")
    if tp is bool:
        if isinstance(value, bool):
            return value
        raise ModelError(f"{where}: expected true or false, got {_typename(value)}")
    if tp is int:
        if isinstance(value, bool):
            raise ModelError(f"{where}: expected a number, got true/false")
        if isinstance(value, int):
            return value
        raise ModelError(f"{where}: expected a number, got {_typename(value)}")
    if tp is float:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        raise ModelError(f"{where}: expected a number, got {_typename(value)}")
    return value


def _build(cls: type, data: Any, where: str) -> Any:
    if isinstance(data, cls):
        return data
    if not isinstance(data, dict):
        label = where or cls.__name__
        raise ModelError(f"{label}: expected a mapping, got {_typename(data)}")
    hints = _hints(cls)
    allowed = set(hints)
    for key in data:
        if key not in allowed:
            raise ModelError(
                f"{where or cls.__name__}: unknown field {key!r}; "
                f"allowed: {', '.join(sorted(allowed))}"
            )
    kwargs: "dict[str, Any]" = {}
    for f in fields(cls):
        tp = hints[f.name]
        prefix = f"{where}." if where else ""
        if f.name in data and data[f.name] is not None:
            kwargs[f.name] = _coerce(tp, data[f.name], f"{prefix}{f.name}")
        elif f.default is MISSING and f.default_factory is MISSING:  # type: ignore[misc]
            raise ModelError(
                f"{where or cls.__name__}: missing required field {f.name!r}"
            )
    return cls(**kwargs)


# Every record family that owns an id, for global-uniqueness checking.
_ID_FAMILIES = (
    ("entities", "entity"),
    ("evidence", "evidence"),
    ("necessity_claims", "necessity claim"),
    ("causal_claims", "causal claim"),
    ("semantic_relations", "semantic relation"),
    ("clouds", "cloud"),
    ("conflict_claims", "conflict claim"),
    ("predicted_effects", "predicted effect"),
    ("observations", "observation"),
    ("obstacle_resolutions", "obstacle resolution"),
    ("transitions", "transition"),
)


def _check_unique_ids(model: LtpModel) -> None:
    seen: "dict[str, str]" = {}
    for attr, label in _ID_FAMILIES:
        for record in getattr(model, attr):
            record_id = record.id
            if record_id in seen:
                raise ModelError(
                    f"duplicate id {record_id!r} (used by {seen[record_id]} "
                    f"and {label})"
                )
            seen[record_id] = label


def parse_model(data: Any) -> LtpModel:
    """Parse a plain dict (from YAML) into a typed, id-unique :class:`LtpModel`."""
    if not isinstance(data, dict):
        raise ModelError(f"model must be a mapping, got {_typename(data)}")
    model = _build(LtpModel, data, "")
    _check_unique_ids(model)
    return model


# --------------------------------------------------------------------------- #
# Serialization
# --------------------------------------------------------------------------- #
_UNSET = object()


def _default_value(f: Any) -> Any:
    if f.default is not MISSING:
        return f.default
    if f.default_factory is not MISSING:  # type: ignore[misc]
        return f.default_factory()
    return _UNSET


def to_dict(obj: Any, *, prune: bool = True) -> Any:
    """Convert a model (or any part) to plain data.

    ``prune=True`` (for authored YAML / migration output) omits ``None``, empty
    collections, and fields equal to their default, keeping files small.
    ``prune=False`` (for source hashing) emits every field so the hash is a pure
    function of the model regardless of which defaults were written out.
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        result: "dict[str, Any]" = {}
        for f in fields(obj):
            plain = to_dict(getattr(obj, f.name), prune=prune)
            if prune:
                if plain is None:
                    continue
                if isinstance(plain, (list, dict)) and not plain:
                    continue
                default = _default_value(f)
                if default is not _UNSET and to_dict(default, prune=prune) == plain:
                    continue
            result[f.name] = plain
        return result
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, list):
        return [to_dict(item, prune=prune) for item in obj]
    if isinstance(obj, dict):
        return {key: to_dict(value, prune=prune) for key, value in obj.items()}
    return obj


# --------------------------------------------------------------------------- #
# Index -- fast id lookup for validators, renderers, and ``explain``
# --------------------------------------------------------------------------- #
class ModelIndex:
    """Id -> record lookup across every family, plus kind-filtered helpers."""

    def __init__(self, model: LtpModel) -> None:
        self.model = model
        self.entities = {entity.id: entity for entity in model.entities}
        self.evidence = {item.id: item for item in model.evidence}
        self.necessity_claims = {claim.id: claim for claim in model.necessity_claims}
        self.causal_claims = {claim.id: claim for claim in model.causal_claims}
        self.semantic_relations = {
            relation.id: relation for relation in model.semantic_relations
        }
        self.clouds = {cloud.id: cloud for cloud in model.clouds}
        self.conflict_claims = {claim.id: claim for claim in model.conflict_claims}
        self.predicted_effects = {pred.id: pred for pred in model.predicted_effects}
        self.observations = {item.id: item for item in model.observations}
        self.obstacle_resolutions = {
            res.id: res for res in model.obstacle_resolutions
        }
        self.transitions = {transition.id: transition for transition in model.transitions}

    def entity(self, entity_id: str) -> "Optional[Entity]":
        return self.entities.get(entity_id)

    def kind_of(self, entity_id: str) -> "Optional[EntityKind]":
        entity = self.entities.get(entity_id)
        return entity.kind if entity else None

    def of_kind(self, *kinds: EntityKind) -> "list[Entity]":
        wanted = set(kinds)
        return [entity for entity in self.model.entities if entity.kind in wanted]

    def exists(self, record_id: str) -> bool:
        return (
            record_id in self.entities
            or record_id in self.evidence
            or record_id in self.necessity_claims
            or record_id in self.causal_claims
            or record_id in self.semantic_relations
            or record_id in self.clouds
            or record_id in self.conflict_claims
            or record_id in self.predicted_effects
            or record_id in self.observations
            or record_id in self.obstacle_resolutions
            or record_id in self.transitions
        )

    def any_record(self, record_id: str) -> Any:
        for table in (
            self.entities,
            self.evidence,
            self.necessity_claims,
            self.causal_claims,
            self.semantic_relations,
            self.clouds,
            self.conflict_claims,
            self.predicted_effects,
            self.observations,
            self.obstacle_resolutions,
            self.transitions,
        ):
            if record_id in table:
                return table[record_id]
        return None
