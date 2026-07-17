"""Acceptance scenarios for this repository's own composition claims.

This is the acceptance suite for the repo-root `hypothesize` project
(`research/portfolio.toml`). It is deliberately black-box: every test exercises
the *installed, public* behavior of `promisify`, `hypothesize`, and `ltp` --
source layout, package boundaries, and public bridge functions -- and does not
duplicate, import internals from, or modify any existing skill's own test
suite (ltp/tests/, hypothesize/tests/, promisify/tests/ are untouched). Each
test carries `@pytest.mark.hyp_*` / `@pytest.mark.cap_*` / `@pytest.mark.evidence_*`
markers so `hypothesize`'s pytest adapter can derive real capability status and
evidence maturity for research/portfolio.toml -- see references/tag-vocabulary.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _package_source(*relative_parts: str) -> str:
    """Concatenate every .py file under a package's src/ tree into one string."""
    package_root = REPO_ROOT.joinpath(*relative_parts)
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package_root.rglob("*.py"))
    )


# ---------------------------------------------------------------------------
# HYP-ENGINE-DECOUPLING / CAP-NO-CROSS-IMPORT
#
# README.md's Composition section: "The skills form a federation, not a
# mandatory pipeline. Each shipped skill can run in isolation." At the Python
# package level, that requires no engine's source to import a sibling engine's
# implementation package.
# ---------------------------------------------------------------------------


@pytest.mark.hyp_engine_decoupling
@pytest.mark.cap_no_cross_import
def test_hypothesize_engine_does_not_import_ltp_or_norms_py() -> None:
    source = _package_source("hypothesize", "src")
    assert "import ltp" not in source
    assert "from ltp" not in source
    assert "norms.py" not in source
    assert "promisify" not in source.lower()


@pytest.mark.hyp_engine_decoupling
@pytest.mark.cap_no_cross_import
def test_ltp_engine_does_not_import_the_hypothesize_package() -> None:
    # ltp/src/ltp/integrations/hypothesize.py is a bridge MODULE whose name
    # happens to match the sibling engine -- it must not import that engine's
    # package. It reads a plain research-status.json (see the next test).
    #
    # `from .integrations import hypothesize` (a relative import of ltp's own
    # submodule) is expected and must not be flagged; only a bare `import
    # hypothesize` statement or `from hypothesize[.submodule] import ...`
    # would mean ltp actually depends on the external hypothesize package.
    source = _package_source("ltp", "src")
    assert re.search(r"(?m)^\s*import hypothesize\b", source) is None
    assert re.search(r"(?m)^\s*from hypothesize\b", source) is None


@pytest.mark.hyp_engine_decoupling
@pytest.mark.cap_no_cross_import
def test_promisify_has_no_installable_package_for_others_to_import() -> None:
    # promisify ships scripts/norms.py directly (no setup.py/pyproject package
    # target other than pytest config for its own tests); nothing else in the
    # repository should import it as a module either.
    for tree in ("hypothesize/src", "ltp/src"):
        source = _package_source(*tree.split("/"))
        assert "import norms" not in source
        assert "from norms" not in source


# ---------------------------------------------------------------------------
# HYP-BRIDGE-PRESERVES-LOGIC / CAP-BRIDGE-SEPARATION
#
# references/cli-and-integration.md: "`ltp evidence import` folds a hypothesize
# outcome into `verification.empirical_status` only. It never writes
# `review_status` or the CLR-derived logical status." This is a bounded
# mechanism demonstration on a synthetic fixture (`@evidence_mechanism`): it
# proves the bridge preserves the logic/empirical separation; it does not test
# any real hypothesis's truth.
# ---------------------------------------------------------------------------

_MODEL = {
    "project": {"name": "composition-check", "goal": "G-1"},
    "entities": [
        {"id": "G-1", "kind": "goal", "statement": "goal"},
        {"id": "RC-1", "kind": "root_cause", "statement": "cause"},
        {"id": "UDE-1", "kind": "undesirable_effect", "statement": "effect", "basis": "observed"},
    ],
    "causal_claims": [
        {
            "id": "CLM-1",
            "premises": ["RC-1"],
            "conclusion": "UDE-1",
            "clr": {"causality_existence": {"result": "pass"}},
            "verification": {"hypothesis_ref": "HYP-EXT", "role": "causal_outcome"},
        }
    ],
}


@pytest.mark.hyp_bridge_preserves_logic
@pytest.mark.cap_bridge_separation
@pytest.mark.evidence_mechanism
@pytest.mark.synthetic_fixture
def test_ltp_bridge_updates_empirical_status_without_touching_clr() -> None:
    from ltp.integrations import hypothesize as bridge
    from ltp.models import parse_model

    model = parse_model(_MODEL)
    research_status = {"hypotheses": [{"id": "HYP-EXT", "conclusion": "falsified"}]}

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        status_path = Path(tmp) / "research-status.json"
        status_path.write_text(json.dumps(research_status), encoding="utf-8")
        changes = bridge.import_evidence(model, status_path)

    claim = model.causal_claims[0]
    assert claim.verification.empirical_status.value == "falsified"
    # The logical (CLR) status is untouched by the empirical import.
    assert claim.clr.causality_existence.result.value == "pass"
    # A contradiction is recorded rather than the claim being deleted or reversed.
    assert any("falsified" in note for note in model.contradictions)
    assert changes


@pytest.mark.hyp_bridge_preserves_logic
@pytest.mark.cap_bridge_separation
@pytest.mark.evidence_mechanism
@pytest.mark.synthetic_fixture
def test_ltp_bridge_export_never_asserts_a_conclusion() -> None:
    from ltp.integrations import hypothesize as bridge
    from ltp.models import parse_model

    model = parse_model(_MODEL)
    links = bridge.export_links(model)
    assert links == [
        {
            "claim": "CLM-1",
            "conclusion": "UDE-1",
            "hypothesis_ref": "HYP-EXT",
            "role": "causal_outcome",
            "empirical_status": "not_tested",
        }
    ]
    # export_links never contains a scientific-conclusion-shaped key -- the
    # bridge only ever reads/writes verification.empirical_status.
    assert "supported" not in links[0].values()
    assert "falsified" not in links[0].values()
