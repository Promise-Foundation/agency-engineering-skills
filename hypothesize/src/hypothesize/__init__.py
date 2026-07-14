"""hypothesize — a reusable engine for honest, machine-readable research status.

Public API:

    from hypothesize import ResearchStatusService, ResearchStatusError, EvidenceBundle
    from hypothesize.adapters.behave import load_scenarios

The engine keeps three dimensions separate — capability status (from tests),
evidence maturity (from artifacts), and scientific conclusion (only from
qualified, preregistered results) — so implementation progress can never be
mistaken for empirical validation.
"""

from __future__ import annotations

from .collector import EvidenceBundle
from .core import (
    CONCLUSIONS,
    MATURITY_ORDER,
    SCENARIO_STATUSES,
    ResearchStatusError,
    ResearchStatusService,
)

__version__ = "0.1.0"

__all__ = [
    "ResearchStatusService",
    "ResearchStatusError",
    "EvidenceBundle",
    "CONCLUSIONS",
    "MATURITY_ORDER",
    "SCENARIO_STATUSES",
    "__version__",
]
