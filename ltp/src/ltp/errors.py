"""Error types shared across the engine."""

from __future__ import annotations


class LtpError(ValueError):
    """Base class for every error the engine raises."""


class ModelError(LtpError):
    """The authored model is *structurally* malformed.

    This covers anything that stops the model from being loaded as typed data:
    a missing required field, an unknown field, a value outside a closed
    vocabulary, a duplicate id, or a reference to an id that does not exist.

    Structural errors are distinct from *logical* diagnostics (see
    :mod:`ltp.diagnostics`). A model can load cleanly and still be logically
    incomplete or invalid; only structural failures raise here.
    """


class MigrationError(LtpError):
    """A v1 model could not be migrated to the current schema."""
