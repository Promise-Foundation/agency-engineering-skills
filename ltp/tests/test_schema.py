"""The committed schema, TS types, and diagnostics catalog stay in sync with the
Python model."""

from __future__ import annotations

import json

from ltp.schema import artifacts, json_schema, main


def test_committed_artifacts_are_current():
    # main(["--check"]) returns 0 only if every committed artifact matches what the
    # current model would generate.
    assert main(["--check"]) == 0


def test_schema_covers_the_model_and_forbids_extra_fields():
    schema = json_schema()
    assert "LtpModel" in schema["$defs"]
    entity = schema["$defs"]["Entity"]
    assert entity["additionalProperties"] is False
    assert "id" in entity["required"] and "kind" in entity["required"]
    # kind is a closed enum, not a free string
    assert "enum" in entity["properties"]["kind"]


def test_typescript_and_schema_agree_on_files():
    # Both artifacts are generated together; the set is stable.
    paths = {p.name for p in artifacts()}
    assert paths == {"ltp-model.schema.json", "model-types.ts", "diagnostics.md"}
