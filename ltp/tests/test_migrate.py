"""v1 -> v2 migration preserves ids and yields a parseable v2 model."""

from __future__ import annotations

from conftest import FIXTURES
from ltp.migrate import migrate_dict, needs_migration
from ltp.models import parse_model
from ltp.store import yaml_load

V1 = FIXTURES / "v1" / "ltp-model.yaml"


def test_v1_needs_migration_v2_does_not():
    v1 = yaml_load(V1.read_text(encoding="utf-8"))
    assert needs_migration(v1) is True
    migrated = migrate_dict(v1)
    assert needs_migration(migrated) is False


def test_migration_preserves_ids_and_parses():
    v1 = yaml_load(V1.read_text(encoding="utf-8"))
    original_ids = {e["id"] for e in v1["entities"]}
    migrated = migrate_dict(v1)
    model = parse_model(migrated)  # must parse as typed v2
    assert model.schema_version == 2
    migrated_ids = {e.id for e in model.entities}
    assert original_ids <= migrated_ids  # every v1 entity id survived


def test_migration_drops_generic_links_for_typed_claims():
    v1 = yaml_load(V1.read_text(encoding="utf-8"))
    migrated = migrate_dict(v1)
    assert "links" not in migrated
    # necessary_for links became necessity claims; causal links became causal claims.
    assert migrated.get("necessity_claims"), "expected necessity claims from necessary_for links"
    assert migrated.get("causal_claims"), "expected causal claims from causes links"
