"""A thin bridge to the ``hypothesize`` tool.

``ltp`` owns causal structure and logical scrutiny; ``hypothesize`` owns the
empirical status of tested claims. This module reads/writes only the small
overlap -- the ``verification`` link on a causal claim -- and never lets a green
test promote a claim's *logical* status.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ..enums import EmpiricalStatus
from ..models import LtpModel


def export_links(model: LtpModel) -> "list[dict[str, Any]]":
    """Every causal claim that carries a hypothesize verification link."""
    links = []
    for claim in model.causal_claims:
        if claim.verification is not None:
            links.append(
                {
                    "claim": claim.id,
                    "conclusion": claim.conclusion,
                    "hypothesis_ref": claim.verification.hypothesis_ref,
                    "role": claim.verification.role.value,
                    "empirical_status": (
                        claim.verification.empirical_status.value
                        if claim.verification.empirical_status
                        else "not_tested"
                    ),
                }
            )
    return links


def check_links(model: LtpModel, known_ids: "Optional[set[str]]" = None) -> "list[str]":
    """Report problems with verification links.

    With ``known_ids`` (hypothesis ids from a hypothesize registry) it flags refs
    that do not resolve; without it, it can only report that resolution needs the
    registry.
    """
    problems: "list[str]" = []
    for link in export_links(model):
        ref = link["hypothesis_ref"]
        if known_ids is not None and ref not in known_ids:
            problems.append(f"{link['claim']}: hypothesis_ref {ref!r} not in registry")
    return problems


def _load_outcomes(path: Path) -> "dict[str, str]":
    """Read hypothesis id -> conclusion from a hypothesize research-status.json."""
    data = json.loads(path.read_text(encoding="utf-8"))
    outcomes: "dict[str, str]" = {}
    for hypothesis in data.get("hypotheses", []):
        hid = hypothesis.get("id")
        if hid:
            outcomes[hid] = str(hypothesis.get("conclusion", "not_tested"))
    return outcomes


def import_evidence(model: LtpModel, research_status: Path) -> "list[str]":
    """Fold hypothesize outcomes into each linked claim's *empirical* status.

    Returns a list of human-readable changes. A falsified outcome also records a
    contradiction note. This never edits CLR results or deletes a claim -- logical
    and empirical status stay separate.
    """
    outcomes = _load_outcomes(research_status)
    changes: "list[str]" = []
    for claim in model.causal_claims:
        if claim.verification is None:
            continue
        ref = claim.verification.hypothesis_ref
        if ref not in outcomes:
            continue
        try:
            status = EmpiricalStatus(outcomes[ref])
        except ValueError:
            continue
        if claim.verification.empirical_status != status:
            claim.verification.empirical_status = status
            changes.append(f"{claim.id}: empirical_status <- {status.value} (from {ref})")
        if status == EmpiricalStatus.FALSIFIED:
            note = (
                f"{claim.id} is empirically falsified by {ref}; review it and its "
                "dependents (logical status is unchanged and must be re-scrutinized)"
            )
            if note not in model.contradictions:
                model.contradictions.append(note)
                changes.append(f"{claim.id}: recorded falsification contradiction")
    return changes
