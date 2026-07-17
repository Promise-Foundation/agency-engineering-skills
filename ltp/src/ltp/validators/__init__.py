"""Run every logical validator over a model and report the findings.

A model is *publishable* when it has no ``error``-severity diagnostics. Warnings
and info notes never block publication; they are the running list of scrutiny a
mature model works down over time.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..diagnostics import Diagnostic, Severity, counts, sort_key
from ..models import LtpModel, ModelIndex
from . import (
    clr,
    cloud,
    constraint,
    crosstree,
    goal_tree,
    learning,
    plan,
    prerequisite,
    reality,
    structure,
    transition,
)

# Order is cosmetic only -- findings are sorted by severity before returning.
_VALIDATORS = (
    structure.validate,
    goal_tree.validate,
    reality.validate,
    clr.validate,
    cloud.validate,
    prerequisite.validate,
    transition.validate,
    constraint.validate,
    crosstree.validate,
    plan.validate,
)


@dataclass
class ValidationReport:
    diagnostics: "list[Diagnostic]"

    @property
    def errors(self) -> "list[Diagnostic]":
        return [d for d in self.diagnostics if d.severity == Severity.ERROR]

    @property
    def warnings(self) -> "list[Diagnostic]":
        return [d for d in self.diagnostics if d.severity == Severity.WARNING]

    @property
    def counts(self) -> "dict[str, int]":
        return counts(self.diagnostics)

    @property
    def is_publishable(self) -> bool:
        """No error-severity findings. Warnings do not block publication."""
        return not self.errors

    def to_dict(self) -> "dict[str, object]":
        return {
            "counts": self.counts,
            "publishable": self.is_publishable,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }


def run_all(model: LtpModel, *, as_of: str | None = None) -> "list[Diagnostic]":
    index = ModelIndex(model)
    found: "list[Diagnostic]" = []
    for validator in _VALIDATORS:
        found.extend(validator(model, index))
    found.extend(learning.validate(model, index, as_of=as_of))
    # Deterministic and de-duplicated: identical (code, target, message) once.
    unique = {(d.code, d.target, d.message): d for d in found}
    return sorted(unique.values(), key=sort_key)


def validate(model: LtpModel, *, as_of: str | None = None) -> ValidationReport:
    return ValidationReport(diagnostics=run_all(model, as_of=as_of))
