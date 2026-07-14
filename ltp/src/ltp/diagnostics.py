"""Coded logical diagnostics.

A :class:`Diagnostic` is a *logical* finding about a model that parsed cleanly --
distinct from a :class:`~ltp.errors.ModelError`, which stops the model from
loading at all. Every finding carries a stable code (``GT-004``, ``EC-008``,
...), a severity, a human message, and usually the id it attaches to.

Codes are registered in :data:`CATALOG` so severities stay consistent and a
typo in a code raises immediately. ``ltp explain`` and the dashboard's
model-health panel both read the same codes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def rank(self) -> int:
        return {"error": 0, "warning": 1, "info": 2}[self.value]


# code -> (severity, one-line title). The title documents intent; the concrete
# message is built at the call site with specifics (which id, which check).
CATALOG: "dict[str, tuple[Severity, str]]" = {
    # Reference integrity (checked after parse so all danglers surface at once)
    "REF-001": (Severity.ERROR, "reference to an unknown id"),
    "REF-002": (Severity.ERROR, "reference to an id of the wrong kind for its role"),
    # Id conventions
    "ID-001": (Severity.INFO, "entity id prefix does not match its kind"),
    # Goal Tree
    "GT-001": (Severity.ERROR, "no goal is selected"),
    "GT-002": (Severity.ERROR, "the selected goal is not a goal-kind entity"),
    "GT-003": (Severity.ERROR, "CSF has no necessity path to the goal"),
    "GT-004": (Severity.WARNING, "CSF has no NC and is not justified as atomic"),
    "GT-005": (Severity.ERROR, "NC has no necessity path to a CSF or the goal"),
    "GT-006": (Severity.WARNING, "goal-tree leaf has no observable satisfaction criterion"),
    "GT-007": (Severity.WARNING, "more than five top-level CSFs without justification"),
    "GT-008": (Severity.WARNING, "CSF appears necessary for another CSF, not the goal"),
    "GT-010": (Severity.WARNING, "necessary condition's necessity is unjustified"),
    # Current Reality Tree
    "CRT-001": (Severity.WARNING, "UDE is written as a missing feature, not a harmful effect"),
    "CRT-002": (Severity.ERROR, "UDE has no cause leading into it"),
    "CRT-003": (Severity.WARNING, "UDE is not observed / present-tense"),
    "CRT-004": (Severity.ERROR, "causal cycle (not modelled as a feedback loop)"),
    "CRT-005": (Severity.WARNING, "root-cause candidate explains only one UDE"),
    "CRT-006": (Severity.WARNING, "causal claim may require an additional premise"),
    "CRT-007": (Severity.ERROR, "compound premises without an explicit operator"),
    "CRT-008": (Severity.WARNING, "important causal claim has no assumptions and no CLR"),
    # Future Reality Tree
    "FRT-001": (Severity.ERROR, "injection enters no causal claim"),
    "FRT-003": (Severity.ERROR, "injection has no explicit desirable-effect path"),
    "FRT-004": (Severity.ERROR, "injection jumps directly to goal achieved"),
    "FRT-005": (Severity.WARNING, "desirable effect supports no NC, CSF, or goal"),
    "FRT-006": (Severity.ERROR, "negative branch is not dispositioned"),
    # Evaporating Cloud
    "EC-002": (Severity.ERROR, "cloud lacks distinct A/B/C/D/D' roles"),
    "EC-003": (Severity.ERROR, "cloud does not wire four necessity claims"),
    "EC-004": (Severity.ERROR, "cloud has no explicit D-D' incompatibility"),
    "EC-005": (Severity.WARNING, "cloud necessity claim has no assumption"),
    "EC-006": (Severity.WARNING, "no evidence that both needs are legitimate"),
    "EC-007": (Severity.WARNING, "no assumption is targeted by an injection"),
    "EC-008": (Severity.ERROR, "conflict has no evidence of persistence"),
    "EC-009": (Severity.WARNING, "conflict rests only on generic resource finitude"),
    # Prerequisite Tree
    "PRT-001": (Severity.ERROR, "obstacle has no intermediate objective"),
    "PRT-002": (Severity.WARNING, "IO overcomes no named obstacle"),
    "PRT-003": (Severity.WARNING, "IO is written as an imperative action, not a condition"),
    "PRT-004": (Severity.WARNING, "disconnected prerequisite row"),
    "PRT-006": (Severity.ERROR, "IO has no dependency path to the target injection"),
    # Transition Tree
    "TT-002": (Severity.ERROR, "transition advances no intermediate objective"),
    "TT-003": (Severity.WARNING, "action contains multiple independently verifiable changes"),
    "TT-004": (Severity.WARNING, "action directly implements the whole injection"),
    "TT-005": (Severity.WARNING, "transition has no verification"),
    "TT-006": (Severity.INFO, "transition has no likely scope"),
    "TT-007": (Severity.ERROR, "transition has no immediate observable effect"),
    # Constraint
    "CON-001": (Severity.ERROR, "current constraint is not a constraint-kind entity"),
    "CON-002": (Severity.ERROR, "current constraint has no limiting-mechanism argument"),
    "CON-003": (Severity.WARNING, "constraint assessment has no goal measure"),
    "CON-004": (Severity.WARNING, "constraint assessment considered no alternatives"),
    "CON-005": (Severity.WARNING, "constraint assessment has no Five Focusing Steps posture"),
    "CON-006": (Severity.WARNING, "root cause used as the constraint without demonstration"),
    # Cross-tree
    "XTR-003": (Severity.WARNING, "injection resolves no root cause or conflict assumption"),
    "XTR-004": (Severity.ERROR, "recommended action has no complete path to the goal"),
    "XTR-005": (Severity.WARNING, "entity is disconnected from every structure"),
    # CLR review
    "CLR-001": (Severity.WARNING, "sufficiency claim has no CLR review (candidate claim)"),
    "CLR-003": (Severity.ERROR, "CLR concluded no causality exists"),
    "CLR-006": (Severity.ERROR, "CLR concluded the cause and effect are reversed"),
    "CLR-007": (Severity.ERROR, "CLR concluded the claim is a tautology"),
    "CLR-008": (Severity.WARNING, "claim has open CLR checks (not yet scrutinized)"),
    "CLR-009": (Severity.WARNING, "claimed entity existence is unverified"),
    # Predicted effects
    "PRED-001": (Severity.WARNING, "root-cause candidate has no predicted effect"),
    "PRED-002": (Severity.WARNING, "a predicted effect that should exist was not observed"),
    # Analysis plan
    "PLAN-001": (Severity.INFO, "analysis-plan status disagrees with model content"),
    "PLAN-002": (Severity.WARNING, "a required tree has no content"),
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    target: Optional[str] = None
    hint: Optional[str] = None

    @property
    def severity(self) -> Severity:
        return CATALOG[self.code][0]

    @property
    def title(self) -> str:
        return CATALOG[self.code][1]

    def format(self) -> str:
        location = f" [{self.target}]" if self.target else ""
        line = f"{self.severity.value.upper():7} {self.code}{location}: {self.message}"
        if self.hint:
            line += f"\n        hint: {self.hint}"
        return line

    def to_dict(self) -> "dict[str, Optional[str]]":
        return {
            "code": self.code,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "target": self.target,
            "hint": self.hint,
        }


def diagnostic(
    code: str,
    message: str,
    *,
    target: Optional[str] = None,
    hint: Optional[str] = None,
) -> Diagnostic:
    """Build a diagnostic, validating the code against the catalog."""
    if code not in CATALOG:
        raise KeyError(f"unknown diagnostic code {code!r}")
    return Diagnostic(code=code, message=message, target=target, hint=hint)


def sort_key(item: Diagnostic) -> "tuple[int, str, str]":
    """Most severe first, then by code, then by target -- fully deterministic."""
    return (item.severity.rank, item.code, item.target or "")


def counts(items: "list[Diagnostic]") -> "dict[str, int]":
    result = {"error": 0, "warning": 0, "info": 0}
    for item in items:
        result[item.severity.value] += 1
    return result
