"""The typed model: parsing, coercion, closed vocabularies, round-trip."""

from __future__ import annotations

import pytest

from ltp.errors import ModelError
from ltp.models import parse_model, to_dict

MINIMAL = {
    "project": {"name": "T", "goal": "G-1"},
    "entities": [{"id": "G-1", "kind": "goal", "statement": "Succeed"}],
}


def test_parses_minimal_and_applies_defaults():
    model = parse_model(MINIMAL)
    assert model.schema_version == 2
    entity = model.entities[0]
    assert entity.basis.value == "inferred"
    assert entity.review_status.value == "unreviewed"
    assert entity.confidence.value == "medium"


def test_unknown_kind_is_structural_error():
    bad = {"project": {"name": "T"}, "entities": [{"id": "E", "kind": "banana", "statement": "s"}]}
    with pytest.raises(ModelError) as excinfo:
        parse_model(bad)
    assert "not a valid EntityKind" in str(excinfo.value)


def test_missing_required_field_is_structural_error():
    bad = {"project": {"name": "T"}, "entities": [{"id": "E", "kind": "goal"}]}
    with pytest.raises(ModelError) as excinfo:
        parse_model(bad)
    assert "missing required field 'statement'" in str(excinfo.value)


def test_unknown_field_is_rejected():
    bad = {"project": {"name": "T"}, "entities": [{"id": "E", "kind": "goal", "statement": "s", "nope": 1}]}
    with pytest.raises(ModelError) as excinfo:
        parse_model(bad)
    assert "unknown field 'nope'" in str(excinfo.value)


def test_duplicate_ids_rejected_across_families():
    bad = {
        "project": {"name": "T"},
        "entities": [{"id": "X", "kind": "goal", "statement": "s"}],
        "evidence": [{"id": "X", "source": "a", "observation": "o"}],
    }
    with pytest.raises(ModelError) as excinfo:
        parse_model(bad)
    assert "duplicate id 'X'" in str(excinfo.value)


def test_nested_enum_and_error_location():
    bad = {
        "project": {"name": "T"},
        "entities": [{"id": "G-1", "kind": "goal", "statement": "s"}],
        "causal_claims": [
            {"id": "CLM-1", "conclusion": "G-1", "premises": ["G-1"], "operator": "nonsense"}
        ],
    }
    with pytest.raises(ModelError) as excinfo:
        parse_model(bad)
    message = str(excinfo.value)
    assert "operator" in message and "not a valid Operator" in message


def test_round_trip_is_stable():
    model = parse_model(MINIMAL)
    once = to_dict(model, prune=True)
    twice = to_dict(parse_model(once), prune=True)
    assert once == twice


def test_prune_omits_defaults_but_keeps_required():
    model = parse_model(MINIMAL)
    data = to_dict(model, prune=True)
    entity = data["entities"][0]
    assert "id" in entity and "kind" in entity and "statement" in entity
    assert "basis" not in entity  # default pruned
