"""The diagnostics catalog and ordering."""

from __future__ import annotations

import pytest

from ltp.diagnostics import CATALOG, Diagnostic, Severity, diagnostic, sort_key


def test_unknown_code_raises():
    with pytest.raises(KeyError):
        diagnostic("ZZ-999", "nope")


def test_every_catalog_code_is_constructible():
    for code in CATALOG:
        item = diagnostic(code, "message")
        assert isinstance(item.severity, Severity)
        assert item.title


def test_severity_rank_orders_errors_first():
    assert Severity.ERROR.rank < Severity.WARNING.rank < Severity.INFO.rank


def test_sort_key_is_deterministic_and_severity_first():
    items = [
        diagnostic("TT-006", "info", target="TR-1"),  # INFO
        diagnostic("GT-004", "warn", target="CSF-1"),  # WARNING
        diagnostic("CRT-002", "err", target="UDE-1"),  # ERROR
        diagnostic("CRT-004", "err", target="UDE-2"),  # ERROR
    ]
    ordered = sorted(items, key=sort_key)
    severities = [item.severity for item in ordered]
    assert severities == sorted(severities, key=lambda s: s.rank)
    assert ordered[0].code == "CRT-002"  # ties broken by code
