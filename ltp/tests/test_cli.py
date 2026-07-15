"""End-to-end CLI lifecycle: init -> validate -> sync -> check, plus staleness."""

from __future__ import annotations

import shutil

from conftest import FIXTURES
from ltp.cli import main


def test_init_validate_sync_check(tmp_path):
    root = str(tmp_path)
    assert main(["--root", root, "init", "--name", "Demo"]) == 0
    assert (tmp_path / "ltp" / "ltp-model.yaml").exists()
    assert main(["--root", root, "validate"]) == 0  # warnings ok, no errors
    assert main(["--root", root, "sync"]) == 0
    assert main(["--root", root, "check"]) == 0


def test_check_fails_when_generated_is_stale(tmp_path):
    root = str(tmp_path)
    main(["--root", root, "init"])
    main(["--root", root, "sync"])
    doc = tmp_path / "ltp" / "generated" / "02-goal-tree.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
    assert main(["--root", root, "check"]) == 2


def test_strict_validate_fails_on_warnings(tmp_path):
    root = str(tmp_path)
    main(["--root", root, "init"])
    # The starter has a GT-010 warning (placeholder NC without evidence).
    assert main(["--root", root, "validate"]) == 0
    assert main(["--root", root, "validate", "--strict"]) == 1


def test_validate_reports_errors_on_invalid_fixture(tmp_path):
    src = FIXTURES / "invalid" / "reversed-causality" / "ltp-model.yaml"
    home = tmp_path / "ltp"
    home.mkdir()
    shutil.copy(src, home / "ltp-model.yaml")
    assert main(["--root", str(tmp_path), "validate"]) == 1


def test_explain_missing_id_returns_error(tmp_path):
    root = str(tmp_path)
    main(["--root", root, "init"])
    assert main(["--root", root, "explain", "NOPE-1"]) == 2
    assert main(["--root", root, "explain", "G-1"]) == 0


def test_explain_dependents_include_analysis_and_constraint():
    from ltp.cli import _dependents
    from ltp.models import parse_model

    model = parse_model(
        {
            "project": {"name": "T", "goal": "G-1"},
            "analysis": {"current_constraint": "CON-E"},
            "entities": [
                {"id": "G-1", "kind": "goal", "statement": "g"},
                {"id": "CON-E", "kind": "constraint", "statement": "the limit"},
            ],
            "constraint_assessment": {"entity": "CON-E", "limiting_mechanism": "why"},
        }
    )
    hits = _dependents(model, "CON-E")
    assert any("current_constraint" in hit for hit in hits)
    assert any("constraint_assessment" in hit for hit in hits)
    # the goal is referenced by project.goal
    assert any("project goal" in hit for hit in _dependents(model, "G-1"))
