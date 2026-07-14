"""Generate the JSON Schema, TypeScript types, and diagnostics catalog from the
Python model -- one source of truth, so the Python/schema/dashboard contracts
cannot drift.

    python -m ltp.schema            # write all three artifacts
    python -m ltp.schema --check    # fail if any committed artifact is stale (CI)

Writes:
  references/ltp-model.schema.json      (JSON Schema, draft 2020-12)
  dashboard/src/model-types.ts          (TypeScript interfaces + unions)
  references/diagnostics.md             (the diagnostic-code catalog)
"""

from __future__ import annotations

import dataclasses
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Union, get_args, get_origin, get_type_hints

from . import models
from .diagnostics import CATALOG, Severity

_SKILL_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = _SKILL_ROOT / "references" / "ltp-model.schema.json"
TS_PATH = _SKILL_ROOT / "dashboard" / "src" / "model-types.ts"
DIAGNOSTICS_PATH = _SKILL_ROOT / "references" / "diagnostics.md"


# --------------------------------------------------------------------------- #
# Introspection
# --------------------------------------------------------------------------- #
def _is_optional(tp: Any) -> bool:
    return get_origin(tp) is Union and type(None) in get_args(tp)


def _optional_inner(tp: Any) -> Any:
    return next(arg for arg in get_args(tp) if arg is not type(None))


def _discover() -> "tuple[list[type], list[type]]":
    """Return (dataclasses, enums) reachable from LtpModel, in stable order."""
    seen_dc: "dict[str, type]" = {}
    seen_enum: "dict[str, type]" = {}

    def walk(tp: Any) -> None:
        if _is_optional(tp):
            walk(_optional_inner(tp))
            return
        origin = get_origin(tp)
        if origin in (list, dict):
            for arg in get_args(tp):
                if arg is not type(None):
                    walk(arg)
            return
        if isinstance(tp, type) and issubclass(tp, Enum):
            seen_enum.setdefault(tp.__name__, tp)
            return
        if dataclasses.is_dataclass(tp):
            if tp.__name__ in seen_dc:
                return
            seen_dc[tp.__name__] = tp
            for hint in get_type_hints(tp).values():
                walk(hint)

    walk(models.LtpModel)
    dcs = sorted(seen_dc.values(), key=lambda c: c.__name__)
    enums = sorted(seen_enum.values(), key=lambda c: c.__name__)
    return dcs, enums


def _required(cls: type) -> "list[str]":
    required = []
    for f in dataclasses.fields(cls):
        has_default = f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING  # type: ignore[misc]
        if not has_default:
            required.append(f.name)
    return required


# --------------------------------------------------------------------------- #
# JSON Schema
# --------------------------------------------------------------------------- #
def _json_type(tp: Any) -> "dict[str, Any]":
    if _is_optional(tp):
        return _json_type(_optional_inner(tp))
    origin = get_origin(tp)
    if origin is list:
        return {"type": "array", "items": _json_type(get_args(tp)[0])}
    if origin is dict:
        return {"type": "object", "additionalProperties": _json_type(get_args(tp)[1])}
    if isinstance(tp, type) and issubclass(tp, Enum):
        return {"enum": [member.value for member in tp]}
    if dataclasses.is_dataclass(tp):
        return {"$ref": f"#/$defs/{tp.__name__}"}
    if tp is str:
        return {"type": "string"}
    if tp is bool:
        return {"type": "boolean"}
    if tp is int:
        return {"type": "integer"}
    if tp is float:
        return {"type": "number"}
    return {}


def json_schema() -> "dict[str, Any]":
    dcs, _ = _discover()
    defs: "dict[str, Any]" = {}
    for cls in dcs:
        hints = get_type_hints(cls)
        properties = {name: _json_type(hints[name]) for name in hints}
        entry: "dict[str, Any]" = {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
        }
        required = _required(cls)
        if required:
            entry["required"] = required
        defs[cls.__name__] = entry
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://anthropic.local/ltp/ltp-model.schema.json",
        "title": "LTP model",
        "description": "Generated from ltp.models by ltp.schema -- do not hand-edit.",
        "allOf": [{"$ref": "#/$defs/LtpModel"}],
        "$defs": defs,
    }


# --------------------------------------------------------------------------- #
# TypeScript
# --------------------------------------------------------------------------- #
def _ts_type(tp: Any) -> str:
    if _is_optional(tp):
        return _ts_type(_optional_inner(tp))
    origin = get_origin(tp)
    if origin is list:
        return f"{_ts_type(get_args(tp)[0])}[]"
    if origin is dict:
        return f"Record<string, {_ts_type(get_args(tp)[1])}>"
    if isinstance(tp, type) and issubclass(tp, Enum):
        return tp.__name__
    if dataclasses.is_dataclass(tp):
        return tp.__name__
    if tp is str:
        return "string"
    if tp is bool:
        return "boolean"
    if tp in (int, float):
        return "number"
    return "unknown"


def typescript() -> str:
    dcs, enums = _discover()
    lines = [
        "// Generated from ltp.models by ltp.schema -- do not hand-edit.",
        "// Regenerate with `python -m ltp.schema`.",
        "",
    ]
    for enum in enums:
        union = " | ".join(f'"{member.value}"' for member in enum)
        lines.append(f"export type {enum.__name__} = {union};")
    lines.append("")
    for cls in dcs:
        hints = get_type_hints(cls)
        required = set(_required(cls))
        lines.append(f"export interface {cls.__name__} {{")
        for name in hints:
            optional = "" if name in required else "?"
            lines.append(f"  {name}{optional}: {_ts_type(hints[name])};")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# Diagnostics catalog
# --------------------------------------------------------------------------- #
def diagnostics_markdown() -> str:
    lines = [
        "# Diagnostic codes",
        "",
        "Generated from `ltp.diagnostics` by `ltp.schema` -- do not hand-edit.",
        "",
        "`ltp validate` emits these. **error** blocks publication; **warning** is the",
        "scrutiny backlog; **info** is a note.",
        "",
        "| Code | Severity | Meaning |",
        "|---|---|---|",
    ]
    for code in sorted(CATALOG):
        severity, title = CATALOG[code]
        lines.append(f"| `{code}` | {severity.value} | {title} |")
    counts = {s: 0 for s in Severity}
    for severity, _ in CATALOG.values():
        counts[severity] += 1
    lines.append("")
    lines.append(
        f"_{len(CATALOG)} codes: {counts[Severity.ERROR]} error, "
        f"{counts[Severity.WARNING]} warning, {counts[Severity.INFO]} info._"
    )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
def artifacts() -> "dict[Path, str]":
    return {
        SCHEMA_PATH: json.dumps(json_schema(), indent=2, sort_keys=True) + "\n",
        TS_PATH: typescript(),
        DIAGNOSTICS_PATH: diagnostics_markdown(),
    }


def main(argv: "list[str] | None" = None) -> int:
    check = argv is not None and "--check" in argv
    stale = []
    for path, content in artifacts().items():
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"wrote {path.relative_to(_SKILL_ROOT)}")
    if check and stale:
        for path in stale:
            print(f"stale generated artifact: {path.relative_to(_SKILL_ROOT)}", file=sys.stderr)
        print("run `python -m ltp.schema` to regenerate", file=sys.stderr)
        return 1
    if check:
        print("schema artifacts are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
