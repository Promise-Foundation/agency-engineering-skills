"""Stable-id conventions.

Ids are author-assigned and reused across every view -- the same condition
keeps one id wherever it appears. Ids are never renumbered by the engine, so
``explain CLM-17`` and a hypothesis link like ``ltp://ltp-model.yaml#CLM-17``
stay valid across a migration.

The prefix map below is a *convention*, not a hard rule. The validator emits a
low-severity hint (``ID-001``) when an entity's id prefix does not match its
kind, which catches copy-paste mistakes without blocking analysis.
"""

from __future__ import annotations

from .enums import EntityKind

# Recommended id prefix per entity kind. ``cause`` uses ``AC`` (auxiliary /
# additional cause) so a compound premise reads ``premises: [RC-1, AC-3]``.
ENTITY_PREFIX: "dict[EntityKind, str]" = {
    EntityKind.GOAL: "G",
    EntityKind.CRITICAL_SUCCESS_FACTOR: "CSF",
    EntityKind.NECESSARY_CONDITION: "NC",
    EntityKind.UNDESIRABLE_EFFECT: "UDE",
    EntityKind.CAUSE: "AC",
    EntityKind.ROOT_CAUSE: "RC",
    EntityKind.CONSTRAINT: "CONSTRAINT",
    EntityKind.CLOUD_OBJECTIVE: "A",
    EntityKind.CLOUD_NEED: "N",
    EntityKind.CLOUD_ACTION: "D",
    EntityKind.INJECTION: "INJ",
    EntityKind.DESIRABLE_EFFECT: "DE",
    EntityKind.NEGATIVE_BRANCH: "NBR",
    EntityKind.TRIMMING_INJECTION: "TRIM",
    EntityKind.OBSTACLE: "OBS",
    EntityKind.INTERMEDIATE_OBJECTIVE: "IO",
    EntityKind.EXISTING_REALITY: "ER",
    EntityKind.NEED: "NEED",
    EntityKind.TRANSITION_ACTION: "ACT",
    EntityKind.IMMEDIATE_EFFECT: "IE",
    EntityKind.ASSUMPTION: "ASM",
    EntityKind.RISK: "RISK",
}

# Prefixes for the non-entity record families.
EVIDENCE_PREFIX = "EVD"
NECESSITY_PREFIX = "NEC"
CAUSAL_PREFIX = "CLM"
CLOUD_PREFIX = "EC"
CONFLICT_PREFIX = "CON"
PREDICTED_PREFIX = "PRED"
OBSTACLE_RESOLUTION_PREFIX = "OR"
TRANSITION_PREFIX = "TR"


def prefix_of(entity_id: str) -> str:
    """Return the leading alphabetic prefix of an id (``CSF-2`` -> ``CSF``)."""
    head = entity_id.split("-", 1)[0]
    return head.strip()


def prefix_matches_kind(entity_id: str, kind: EntityKind) -> bool:
    """Whether ``entity_id`` uses the conventional prefix for ``kind``.

    Cloud roles share loose prefixes (``A``/``B``/``C`` for objective and the
    two needs; ``D``/``DP`` for the two actions), so those kinds accept any of
    their family's letters rather than one exact string.
    """
    prefix = prefix_of(entity_id)
    if kind in (EntityKind.CLOUD_OBJECTIVE, EntityKind.CLOUD_NEED):
        return prefix in {"A", "B", "C", "N"}
    if kind == EntityKind.CLOUD_ACTION:
        return prefix in {"D", "DP"}
    return prefix == ENTITY_PREFIX.get(kind, prefix)
