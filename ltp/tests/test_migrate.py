"""Legacy -> v3 migration preserves ids and yields a parseable typed model."""

from __future__ import annotations

from conftest import FIXTURES
from ltp.migrate import migrate_dict, needs_migration
from ltp.models import parse_model
from ltp.store import yaml_load

V1 = FIXTURES / "v1" / "ltp-model.yaml"


def test_v1_needs_migration_v3_does_not():
    v1 = yaml_load(V1.read_text(encoding="utf-8"))
    assert needs_migration(v1) is True
    migrated = migrate_dict(v1)
    assert needs_migration(migrated) is False


def test_migration_preserves_ids_and_parses():
    v1 = yaml_load(V1.read_text(encoding="utf-8"))
    original_ids = {e["id"] for e in v1["entities"]}
    migrated = migrate_dict(v1)
    model = parse_model(migrated)  # must parse as typed v2
    assert model.schema_version == 3
    migrated_ids = {e.id for e in model.entities}
    assert original_ids <= migrated_ids  # every v1 entity id survived


def test_migration_drops_generic_links_for_typed_claims():
    v1 = yaml_load(V1.read_text(encoding="utf-8"))
    migrated = migrate_dict(v1)
    assert "links" not in migrated
    # necessary_for links became necessity claims; causal links became causal claims.
    assert migrated.get("necessity_claims"), "expected necessity claims from necessary_for links"
    assert migrated.get("causal_claims"), "expected causal claims from causes links"


def test_migration_handles_structured_v1_extensions():
    """Real-world v1 models (e.g. Graphist) carry candidate_goals, a top-level
    assumptions list, and structured (dict) notes -- migrate must fold them in."""
    v1 = {
        "project": {"name": "X"},
        "candidate_goals": [
            {"id": "G-1", "label": "Ship", "statement": "The goal", "status": "inferred", "selected": True, "evidence": ["EVD-1"]},
            {"id": "G-alt", "statement": "Alternative", "status": "provisional"},
        ],
        "entities": [{"id": "UDE-1", "type": "undesirable_effect", "statement": "bad", "status": "observed"}],
        "assumptions": [{"id": "ASM-1", "statement": "an assumption", "status": "observed", "confidence": "high"}],
        "links": [{"id": "L1", "from": "UDE-1", "to": "G-1", "relation": "causes", "logic": "sufficient"}],
        "open_questions": [{"id": "OQ-1", "question": "which fork?", "impact": "big"}],
        "contradictions": [{"id": "C-1", "statement": "a tension"}],
        "coverage_gaps": ["a plain string gap"],
        "weird_field": {"unexpected": True},
    }
    migrated = migrate_dict(v1)
    model = parse_model(migrated)  # must parse as typed v3

    kinds = {e.id: e.kind.value for e in model.entities}
    assert kinds.get("G-1") == "goal" and kinds.get("G-alt") == "goal"
    assert kinds.get("ASM-1") == "assumption"
    assert model.project.provisional_goal == "G-1"
    # structured notes are flattened to strings
    assert all(isinstance(q, str) for q in model.open_questions)
    assert any("which fork" in q for q in model.open_questions)
    assert all(isinstance(c, str) for c in model.contradictions)
    # an unrecognized v1 field is dropped but noted, not passed through
    assert "weird_field" not in migrated
    assert any("weird_field" in q for q in model.open_questions)


def test_v2_trimming_claim_becomes_typed_relation_with_same_id():
    v2 = {
        "schema_version": 2,
        "project": {"name": "T"},
        "entities": [
            {"id": "TRIM-1", "kind": "trimming_injection", "statement": "trim"},
            {"id": "NBR-1", "kind": "negative_branch", "statement": "risk"},
        ],
        "causal_claims": [
            {"id": "CLM-6", "premises": ["TRIM-1"], "conclusion": "NBR-1"}
        ],
    }
    migrated = migrate_dict(v2)
    model = parse_model(migrated)
    assert not model.causal_claims
    relation = model.semantic_relations[0]
    assert relation.id == "CLM-6"
    assert relation.relation.value == "neutralizes"
