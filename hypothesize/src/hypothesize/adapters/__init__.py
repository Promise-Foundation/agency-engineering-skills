"""Runner adapters that normalize acceptance reports into one scenario model.

Every adapter returns a list of scenario dicts with the shape the engine expects:

    {
      "id": str,               # stable unique id (location::name or nodeid)
      "name": str,
      "feature": str,
      "location": str,
      "capabilities": [CAP-ID, ...],   # resolved from @cap_* tags via the catalog
      "hypotheses": [HYP-ID, ...],     # resolved from @hyp_* tags via the catalog
      "evidence_kind": str,            # from an @evidence_* tag; default "capability"
      "required": bool,                # False when tagged @optional
      "status": one of SCENARIO_STATUSES,
      "tags": [sorted tags],
    }

An unknown ``@hyp_*`` or ``@cap_*`` tag is a hard error: traceability must be
explicit, never silently created or dropped.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class TraceabilityError(ValueError):
    """A test references a hypothesis or capability the portfolio does not define."""


def capability_tag_map(catalog: Mapping[str, Any]) -> "dict[str, str]":
    mapping: "dict[str, str]" = {}
    for item in catalog.get("capabilities", []):
        tag = item.get("tag") or f"cap_{str(item['id']).lower().replace('-', '_')}"
        mapping[str(tag)] = str(item["id"])
    return mapping


def hypothesis_tag_map(catalog: Mapping[str, Any]) -> "dict[str, str]":
    mapping: "dict[str, str]" = {}
    for item in catalog.get("hypotheses", []):
        tag = item.get("tag") or f"hyp_{str(item['id']).lower().replace('-', '_')}"
        mapping[str(tag)] = str(item["id"])
    return mapping


def resolve_scenario(
    *,
    tags: "set[str]",
    scenario_id: str,
    name: str,
    feature: str,
    location: str,
    status: str,
    capability_tags: Mapping[str, str],
    hypothesis_tags: Mapping[str, str],
) -> "dict[str, Any]":
    """Build one normalized scenario record, enforcing tag traceability."""
    unknown_hypotheses = sorted(
        tag for tag in tags if tag.startswith("hyp_") and tag not in hypothesis_tags
    )
    unknown_capabilities = sorted(
        tag for tag in tags if tag.startswith("cap_") and tag not in capability_tags
    )
    if unknown_hypotheses or unknown_capabilities:
        unknown = ", ".join([*unknown_hypotheses, *unknown_capabilities])
        raise TraceabilityError(f"unknown research traceability tags: {unknown}")
    evidence_tags = sorted(tag for tag in tags if tag.startswith("evidence_"))
    evidence_kind = evidence_tags[0][len("evidence_"):] if evidence_tags else "capability"
    return {
        "id": scenario_id,
        "name": name,
        "feature": feature,
        "location": location,
        "capabilities": sorted(
            capability_tags[tag] for tag in tags if tag in capability_tags
        ),
        "hypotheses": sorted(
            hypothesis_tags[tag] for tag in tags if tag in hypothesis_tags
        ),
        "evidence_kind": evidence_kind,
        "required": "optional" not in tags,
        "status": status,
        "tags": sorted(tags),
    }
