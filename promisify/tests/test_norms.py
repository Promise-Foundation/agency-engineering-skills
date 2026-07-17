"""Unit tests for ``promisify/scripts/norms.py``.

Why this file exists
---------------------
A repo-review assessment recorded against this repository's own ``.norms/``
found ``/skills/_provides_automated_verification`` **broken** for the
``/skills/promisify`` domain: ``norms.py`` implements real logic -- domain
grammar, inheritance resolution, assessment selection, conflict-policy
resolution, and trust arithmetic -- but none of it had an automated test.
``promisify/evals/*.yaml`` only checks whether an *agent* is triggered to use
the skill; it does not check whether ``norms.py`` computes the right answer.

This suite is the repair: it exercises the module directly (not the skill's
prompt-triggering behavior) so a regression in domain resolution, inheritance,
conflict-policy resolution, or trust arithmetic fails a test, not just a
future user's expectations. It intentionally builds tiny, disposable
``.norms/`` fixtures on disk (via ``tmp_path``) so each test is hermetic and
exercises the real discover -> validate -> resolve -> score pipeline end to
end, rather than mocking internals.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import norms  # noqa: E402  (path must be adjusted before this import)


# ---------------------------------------------------------------------------
# Domain grammar and ancestry -- references/domain-resolution.md
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "domain",
    ["/", "/biology", "/biology/botany", "/biology/botany/bryology", "/software/python/models"],
)
def test_is_domain_accepts_valid_paths(domain: str) -> None:
    assert norms.is_domain(domain) is True


@pytest.mark.parametrize(
    "domain",
    [
        "biology/botany",  # not absolute
        "/biology/",  # trailing slash
        "/biology//botany",  # empty segment
        "/biology/../botany",  # traversal segment
        "/Biology",  # segment must start lowercase
        "/bio logy",  # disallowed character
    ],
)
def test_is_domain_rejects_invalid_paths(domain: str) -> None:
    assert norms.is_domain(domain) is False


def test_is_ancestor_root_is_ancestor_of_everything() -> None:
    assert norms.is_ancestor("/", "/biology/botany/bryology") is True
    assert norms.is_ancestor("/", "/") is True


def test_is_ancestor_respects_segment_boundaries() -> None:
    # domain-resolution.md is explicit: "/bio" is NOT an ancestor of "/biology"
    # under raw string-prefix matching; ancestry requires a segment boundary.
    assert norms.is_ancestor("/bio", "/biology") is False
    assert norms.is_ancestor("/biology", "/biology/botany") is True
    assert norms.is_ancestor("/biology/botany", "/biology") is False
    assert norms.is_ancestor("/biology", "/biology") is True


def test_promise_address_root_avoids_double_slash() -> None:
    assert norms.promise_address("/", "_repository_is_reproducible") == "/_repository_is_reproducible"


def test_promise_address_nested_domain() -> None:
    assert norms.promise_address("/biology/botany", "_relates_to_plants") == "/biology/botany/_relates_to_plants"


def test_domain_parent_and_depth() -> None:
    assert norms.domain_parent("/") is None
    assert norms.domain_parent("/skills") == "/"
    assert norms.domain_parent("/skills/ltp") == "/skills"
    assert norms.domain_depth("/") == 0
    assert norms.domain_depth("/skills") == 1
    assert norms.domain_depth("/skills/ltp") == 2


def test_all_domains_with_ancestors_fills_gaps_and_sorts_by_depth() -> None:
    domains = norms.all_domains_with_ancestors(["/skills/ltp", "/interface"])
    assert set(domains) == {"/", "/skills", "/skills/ltp", "/interface"}
    assert domains == sorted(domains, key=lambda value: (norms.domain_depth(value), value))


# ---------------------------------------------------------------------------
# Fixture helpers: build a tiny .norms/ tree on disk per test.
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _repository(name: str = "fixture") -> dict[str, Any]:
    return {
        "apiVersion": "norms/v1",
        "kind": "Repository",
        "metadata": {"name": name},
        "spec": {
            "promiseRoot": ".norms/promises",
            "assessmentRoot": ".norms/assessments",
            "trustViewRoot": ".norms/views",
            "defaultView": "default",
        },
    }


def _promise(domain: str, name: str, statement: str | None = None) -> dict[str, Any]:
    return {
        "apiVersion": "norms/v1",
        "kind": "Promise",
        "metadata": {"domain": domain, "name": name},
        "spec": {
            "statement": statement or f"Subjects OUGHT to satisfy {name}.",
            "criteria": {"kind": "manual-review", "instructions": "Inspect manually."},
        },
    }


def _assessment(
    id_: str,
    promise: str,
    effective_domain: str,
    verdict: str,
    assessor: str = "agent/test",
    observed_at: str = "2026-01-01T00:00:00Z",
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "promise": promise,
        "effectiveDomain": effective_domain,
        "verdict": verdict,
        "rationale": f"test rationale for {verdict}",
    }
    if evidence is not None:
        spec["evidence"] = evidence
    elif verdict in {"kept", "broken"}:
        spec["evidence"] = [{"kind": "test", "summary": "synthetic evidence"}]
    return {
        "apiVersion": "norms/v1",
        "kind": "Assessment",
        "metadata": {"id": id_, "assessor": assessor, "observedAt": observed_at},
        "spec": spec,
    }


def _view(name: str, domain: str, conflict_policy: str = "unknown-on-conflict") -> dict[str, Any]:
    return {
        "apiVersion": "norms/v1",
        "kind": "TrustView",
        "metadata": {"name": name},
        "spec": {
            "observer": "team/test",
            "domain": domain,
            "assessmentSelection": {"assessors": "*", "latestPerAssessor": True, "requireEvidence": True},
            "conflictPolicy": conflict_policy,
            "scoring": {
                "unit": "effective-promise",
                "weighting": "equal",
                "excludeVerdicts": ["unknown", "not_applicable", "disputed"],
            },
        },
    }


@pytest.fixture
def norms_root(tmp_path: Path) -> Path:
    root = tmp_path
    _write_yaml(root / ".norms" / "repository.yaml", _repository())
    _write_yaml(root / ".norms" / "promises" / "_root_promise.yaml", _promise("/", "_root_promise"))
    _write_yaml(
        root / ".norms" / "promises" / "biology" / "_relates_to_plants.yaml",
        _promise("/biology", "_relates_to_plants"),
    )
    _write_yaml(root / ".norms" / "views" / "default.yaml", _view("default", "/biology"))
    return root


# ---------------------------------------------------------------------------
# discover / validate_repository
# ---------------------------------------------------------------------------


def test_validate_repository_passes_on_well_formed_fixture(norms_root: Path) -> None:
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert errors == []
    assert len(documents) == 4  # repository + 2 promises + 1 view


def test_validate_repository_rejects_forbidden_promise_keys(norms_root: Path) -> None:
    bad = _promise("/biology", "_bad_promise")
    bad["spec"]["status"] = "kept"  # a promise must never store a verdict
    _write_yaml(norms_root / ".norms" / "promises" / "biology" / "_bad_promise.yaml", bad)
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert any("forbidden status/trust keys" in error for error in errors)


def test_validate_repository_rejects_misplaced_promise_file(norms_root: Path) -> None:
    # Declares /biology/_wrong_path but is stored at the promises/ root, not promises/biology/.
    misplaced = _promise("/biology", "_wrong_path")
    _write_yaml(norms_root / ".norms" / "promises" / "_wrong_path.yaml", misplaced)
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert any("must be stored at" in error for error in errors)


def test_validate_repository_rejects_duplicate_promise_address(norms_root: Path) -> None:
    duplicate = _promise("/", "_root_promise")
    _write_yaml(norms_root / ".norms" / "promises" / "_root_promise_dup.yaml", duplicate)
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert any("duplicate promise address" in error for error in errors)


def test_validate_repository_rejects_assessment_of_unknown_promise(norms_root: Path) -> None:
    _write_yaml(
        norms_root / ".norms" / "assessments" / "agent-test" / "a1.yaml",
        _assessment("a1", "/does/not/_exist", "/biology", "kept"),
    )
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert any("references unknown promise" in error for error in errors)


def test_validate_repository_rejects_assessment_outside_effective_scope(norms_root: Path) -> None:
    # /biology/_relates_to_plants is declared at /biology; /chemistry is not a descendant of it.
    _write_yaml(
        norms_root / ".norms" / "assessments" / "agent-test" / "a1.yaml",
        _assessment("a1", "/biology/_relates_to_plants", "/chemistry", "kept"),
    )
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert any("is not effective in" in error for error in errors)


def test_validate_repository_warns_on_missing_evidence(norms_root: Path) -> None:
    _write_yaml(
        norms_root / ".norms" / "assessments" / "agent-test" / "a1.yaml",
        _assessment("a1", "/biology/_relates_to_plants", "/biology", "kept", evidence=[]),
    )
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert errors == []
    assert any("has no evidence" in warning for warning in warnings)


# ---------------------------------------------------------------------------
# effective_promises: inheritance
# ---------------------------------------------------------------------------


def test_effective_promises_includes_ancestors_only(norms_root: Path) -> None:
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert errors == []
    effective = dict(norms.effective_promises(documents, "/biology/botany"))
    assert "/_root_promise" in effective
    assert "/biology/_relates_to_plants" in effective


def test_effective_promises_excludes_sibling_domains(norms_root: Path) -> None:
    errors, warnings, documents = norms.validate_repository(norms_root)
    effective = dict(norms.effective_promises(documents, "/chemistry"))
    assert "/_root_promise" in effective
    assert "/biology/_relates_to_plants" not in effective


# ---------------------------------------------------------------------------
# Conflict-policy resolution -- references/assessments.md
# ---------------------------------------------------------------------------


class _Doc:
    """A minimal stand-in for LoadedDocument for resolve_claims unit tests."""

    def __init__(self, verdict: str, observed_at: str, assessor: str = "agent/x") -> None:
        self.data = {
            "metadata": {"observedAt": observed_at, "assessor": assessor, "id": f"{assessor}-{observed_at}"},
            "spec": {"verdict": verdict},
        }


def test_resolve_claims_unknown_on_conflict() -> None:
    claims = [_Doc("kept", "2026-01-01T00:00:00Z"), _Doc("broken", "2026-01-02T00:00:00Z")]
    assert norms.resolve_claims(claims, "unknown-on-conflict") == "disputed"


def test_resolve_claims_latest_wins() -> None:
    claims = [_Doc("kept", "2026-01-01T00:00:00Z"), _Doc("broken", "2026-01-02T00:00:00Z")]
    assert norms.resolve_claims(claims, "latest") == "broken"


def test_resolve_claims_majority() -> None:
    claims = [
        _Doc("kept", "2026-01-01T00:00:00Z"),
        _Doc("kept", "2026-01-02T00:00:00Z"),
        _Doc("broken", "2026-01-03T00:00:00Z"),
    ]
    assert norms.resolve_claims(claims, "majority") == "kept"


def test_resolve_claims_majority_tie_is_disputed() -> None:
    claims = [_Doc("kept", "2026-01-01T00:00:00Z"), _Doc("broken", "2026-01-02T00:00:00Z")]
    assert norms.resolve_claims(claims, "majority") == "disputed"


def test_resolve_claims_conservative_any_broken_wins() -> None:
    claims = [
        _Doc("kept", "2026-01-01T00:00:00Z"),
        _Doc("broken", "2026-01-02T00:00:00Z"),
        _Doc("kept", "2026-01-03T00:00:00Z"),
    ]
    assert norms.resolve_claims(claims, "conservative") == "broken"


def test_resolve_claims_no_claims_is_unknown() -> None:
    assert norms.resolve_claims([], "unknown-on-conflict") == "unknown"


# ---------------------------------------------------------------------------
# Trust arithmetic -- the worked example from references/trust.md
# ---------------------------------------------------------------------------


def test_calculate_trust_matches_documented_worked_example(tmp_path: Path) -> None:
    """references/trust.md's worked example:

        kept=7 broken=2 unknown=3 not_applicable=1 disputed=0
        score = 7 / 9 = 0.7778
        coverage = 9 / 12 = 0.75
    """
    root = tmp_path
    _write_yaml(root / ".norms" / "repository.yaml", _repository())

    verdict_plan = ["kept"] * 7 + ["broken"] * 2 + ["unknown"] * 3 + ["not_applicable"] * 1
    for index, verdict in enumerate(verdict_plan):
        name = f"_p{index}"
        _write_yaml(root / ".norms" / "promises" / f"{name}.yaml", _promise("/", name))
        _write_yaml(
            root / ".norms" / "assessments" / "agent-test" / f"a{index}.yaml",
            _assessment(f"a{index}", f"/{name}", "/", verdict, observed_at=f"2026-01-{index + 1:02d}T00:00:00Z"),
        )
    _write_yaml(root / ".norms" / "views" / "default.yaml", _view("default", "/"))

    errors, warnings, documents = norms.validate_repository(root)
    assert errors == []
    view_doc = norms.load_view(documents, "default")
    report = norms.calculate_trust(documents, view_doc)

    assert report["spec"]["counts"] == {"kept": 7, "broken": 2, "unknown": 3, "not_applicable": 1, "disputed": 0}
    assert report["spec"]["score"] == pytest.approx(7 / 9)
    assert report["spec"]["coverage"] == pytest.approx(9 / 12)


def test_calculate_trust_score_is_null_when_no_scorable_promises(norms_root: Path) -> None:
    errors, warnings, documents = norms.validate_repository(norms_root)
    view_doc = norms.load_view(documents, "default")
    report = norms.calculate_trust(documents, view_doc)
    assert report["spec"]["score"] is None


def test_calculate_trust_latest_per_assessor_supersedes_prior_observation(norms_root: Path) -> None:
    # Same assessor, same promise: the newer observation must be the one selected,
    # without deleting or mutating the older record on disk.
    _write_yaml(
        norms_root / ".norms" / "assessments" / "agent-test" / "a1.yaml",
        _assessment("a1", "/biology/_relates_to_plants", "/biology", "broken", observed_at="2026-01-01T00:00:00Z"),
    )
    _write_yaml(
        norms_root / ".norms" / "assessments" / "agent-test" / "a2.yaml",
        _assessment("a2", "/biology/_relates_to_plants", "/biology", "kept", observed_at="2026-01-02T00:00:00Z"),
    )
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert errors == []
    view_doc = norms.load_view(documents, "default")
    report = norms.calculate_trust(documents, view_doc, domain_override="/biology")
    result = next(r for r in report["spec"]["results"] if r["promise"] == "/biology/_relates_to_plants")
    assert result["verdict"] == "kept"


# ---------------------------------------------------------------------------
# CLI wiring and the explorer projection
# ---------------------------------------------------------------------------


def test_build_parser_exposes_all_commands() -> None:
    parser = norms.build_parser()
    assert parser.parse_args(["validate", "."]).command == "validate"
    assert parser.parse_args(["trust", ".", "--view", "default"]).command == "trust"
    assert parser.parse_args(["effective", ".", "/biology"]).command == "effective"
    assert parser.parse_args(["explorer", "."]).command == "explorer"


def test_command_validate_returns_zero_for_valid_repository(norms_root: Path) -> None:
    args = argparse.Namespace(repository=str(norms_root))
    assert norms.command_validate(args) == 0


def test_command_validate_returns_one_for_invalid_repository(norms_root: Path) -> None:
    _write_yaml(
        norms_root / ".norms" / "assessments" / "agent-test" / "a1.yaml",
        _assessment("a1", "/does/not/_exist", "/biology", "kept"),
    )
    args = argparse.Namespace(repository=str(norms_root))
    assert norms.command_validate(args) == 1


def test_build_explorer_smoke(norms_root: Path) -> None:
    errors, warnings, documents = norms.validate_repository(norms_root)
    assert errors == []
    explorer = norms.build_explorer(documents)
    assert explorer["kind"] == "Explorer"
    assert {"domains", "effective", "promises", "assessments", "views", "trust"} <= explorer.keys()


# ---------------------------------------------------------------------------
# Self-check: this repository dogfoods promisify on itself under .norms/.
# ---------------------------------------------------------------------------


def test_this_repositorys_own_norms_tree_is_valid() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    assert (repo_root / ".norms").exists()
    errors, warnings, documents = norms.validate_repository(repo_root)
    assert errors == [], "\n".join(errors)
