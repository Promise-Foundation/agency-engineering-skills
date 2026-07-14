"""Renderers: determinism, no id leakage, gate semantics, and a golden snapshot."""

from __future__ import annotations

import json

import pytest

from conftest import FIXTURES, GOLDEN
from ltp.renderers import render_all
from ltp.store import load_model

SIMPLE = FIXTURES / "valid" / "simple-complete" / "ltp-model.yaml"
COMPOUND = FIXTURES / "valid" / "compound-cause" / "ltp-model.yaml"


def test_render_is_deterministic():
    model = load_model(SIMPLE)
    assert render_all(model) == render_all(model)


def test_dashboard_has_no_unknown_entities():
    model = load_model(SIMPLE)
    files = render_all(model)
    dash = json.loads(files["generated/dashboard-model.json"])
    model_ids = {e.id for e in model.entities}
    dash_ids = {e["id"] for e in dash["entities"]}
    assert dash_ids == model_ids


def test_no_phantom_id_in_documents():
    """A document can never mention an id the model does not contain."""
    model = load_model(SIMPLE)
    files = render_all(model)
    frt = files["generated/05-future-reality-tree.md"]
    assert "DE-3" not in frt  # the model has DE-1 only
    assert "DE-1" in frt


def test_compound_claim_renders_as_gate():
    model = load_model(COMPOUND)
    files = render_all(model)
    # CLM-1 (and CLM-2 in this fixture) are `all` claims -> AND gate nodes.
    diagram = files["generated/diagrams/current-reality.mmd"]
    assert "AND" in diagram
    assert "#gate" in diagram or "gate" in diagram
    dash = json.loads(files["generated/dashboard-model.json"])
    assert dash["gates"], "compound claim must produce a gate node"


def test_golden_compound_cause():
    """Byte-for-byte snapshot: identical model -> identical generated tree."""
    model = load_model(COMPOUND)
    files = render_all(model)
    golden_dir = GOLDEN / "compound-cause"
    if not golden_dir.exists():
        pytest.skip("golden not generated; run tests/regen_golden.py")
    for relpath, content in files.items():
        golden_file = golden_dir / relpath
        assert golden_file.exists(), f"missing golden for {relpath}"
        assert golden_file.read_text(encoding="utf-8") == content, f"golden drift in {relpath}"
    # No extra golden files lingering.
    committed = {
        str(p.relative_to(golden_dir)) for p in golden_dir.rglob("*") if p.is_file()
    }
    assert committed == set(files), "golden file set differs from rendered set"
