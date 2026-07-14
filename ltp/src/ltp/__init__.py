"""``ltp`` -- a self-policing engine for Theory-of-Constraints Logical Thinking
Processes.

The model (``ltp/ltp-model.yaml``) is the single authored source of truth. The
engine parses it into typed data, checks it against the Categories of Legitimate
Reservation and the structural rules of each tree, and deterministically renders
every projection (documents, Mermaid, dashboard data). Ordinary regeneration is
the CLI's job (``ltp sync`` / ``ltp check``); the accompanying skill covers the
judgment work of proposing and repairing meaning.
"""

from __future__ import annotations

from .errors import LtpError, MigrationError, ModelError
from .models import CURRENT_SCHEMA_VERSION, LtpModel, ModelIndex, parse_model

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "LtpError",
    "LtpModel",
    "MigrationError",
    "ModelError",
    "ModelIndex",
    "parse_model",
]
