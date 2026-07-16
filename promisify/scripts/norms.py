#!/usr/bin/env python3
"""Validate and query a norms/v1 repository.

This helper is intentionally small. It validates the portable file format,
resolves inherited promises, and calculates observer-relative trust reports.
It does not assess repository code by itself; assessors create Assessment files.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover
    print(
        "Missing optional dependencies. Install them with: "
        "python -m pip install -r scripts/requirements.txt",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


TOOL_VERSION = "norms.py/0.1.0"
SCHEMA_BY_KIND = {
    "Repository": "repository.schema.json",
    "Promise": "promise.schema.json",
    "Assessment": "assessment.schema.json",
    "TrustView": "trust-view.schema.json",
    "TrustReport": "trust-report.schema.json",
}
VERDICTS = ("kept", "broken", "unknown", "not_applicable", "disputed")
FORBIDDEN_PROMISE_KEYS = {"status", "verdict", "kept", "broken", "trust", "score", "compliance"}


class StringTimestampLoader(yaml.SafeLoader):
    """Safe YAML loader that leaves timestamps as strings for JSON Schema."""


for first_char, resolvers in list(StringTimestampLoader.yaml_implicit_resolvers.items()):
    StringTimestampLoader.yaml_implicit_resolvers[first_char] = [
        (tag, regex)
        for tag, regex in resolvers
        if tag != "tag:yaml.org,2002:timestamp"
    ]


@dataclass(frozen=True)
class LoadedDocument:
    path: Path
    data: dict[str, Any]


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=StringTimestampLoader)
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"{path}: cannot read YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected one YAML mapping document")
    return value


def dump_yaml(value: Any) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def schemas() -> dict[str, dict[str, Any]]:
    root = skill_root() / "assets" / "schemas"
    result: dict[str, dict[str, Any]] = {}
    for kind, filename in SCHEMA_BY_KIND.items():
        result[kind] = json.loads((root / filename).read_text(encoding="utf-8"))
    return result


def is_domain(value: str) -> bool:
    if value == "/":
        return True
    if not value.startswith("/") or value.endswith("/") or "//" in value:
        return False
    for segment in value[1:].split("/"):
        if segment in {"", ".", ".."}:
            return False
        if not segment[0].isalnum() or not segment[0].islower() and not segment[0].isdigit():
            return False
        if any(not (char.islower() or char.isdigit() or char in "_-") for char in segment):
            return False
    return True


def is_ancestor(ancestor: str, domain: str) -> bool:
    if ancestor == "/":
        return is_domain(domain)
    return domain == ancestor or domain.startswith(ancestor + "/")


def promise_address(domain: str, name: str) -> str:
    return f"/{name}" if domain == "/" else f"{domain}/{name}"


def walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def discover(root: Path) -> list[LoadedDocument]:
    norms_root = root / ".norms"
    if not norms_root.exists():
        raise ValueError(f"{root}: .norms directory not found")
    paths = sorted([*norms_root.rglob("*.yaml"), *norms_root.rglob("*.yml")])
    documents: list[LoadedDocument] = []
    for path in paths:
        documents.append(LoadedDocument(path=path, data=load_yaml(path)))
    return documents


def by_kind(documents: list[LoadedDocument], kind: str) -> list[LoadedDocument]:
    return [doc for doc in documents if doc.data.get("kind") == kind]


def index_promises(documents: list[LoadedDocument]) -> dict[str, LoadedDocument]:
    result: dict[str, LoadedDocument] = {}
    for doc in by_kind(documents, "Promise"):
        metadata = doc.data.get("metadata", {})
        address = promise_address(str(metadata.get("domain", "")), str(metadata.get("name", "")))
        result[address] = doc
    return result


def effective_promises(documents: list[LoadedDocument], target_domain: str) -> list[tuple[str, LoadedDocument]]:
    if not is_domain(target_domain):
        raise ValueError(f"invalid target domain: {target_domain}")
    effective: list[tuple[str, LoadedDocument]] = []
    for address, doc in index_promises(documents).items():
        declaration_domain = doc.data["metadata"]["domain"]
        if is_ancestor(declaration_domain, target_domain):
            effective.append((address, doc))
    return sorted(effective, key=lambda item: (item[1].data["metadata"]["domain"].count("/"), item[0]))


def validate_repository(root: Path) -> tuple[list[str], list[str], list[LoadedDocument]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        documents = discover(root)
    except ValueError as exc:
        return [str(exc)], warnings, []

    schema_map = schemas()
    format_checker = FormatChecker()
    repository_docs = by_kind(documents, "Repository")
    if len(repository_docs) != 1:
        errors.append(f"expected exactly one Repository document; found {len(repository_docs)}")

    for doc in documents:
        kind = doc.data.get("kind")
        if kind not in schema_map:
            errors.append(f"{doc.path}: unknown or missing kind {kind!r}")
            continue
        validator = Draft202012Validator(schema_map[kind], format_checker=format_checker)
        for issue in sorted(validator.iter_errors(doc.data), key=lambda err: list(err.absolute_path)):
            location = ".".join(str(part) for part in issue.absolute_path) or "<root>"
            errors.append(f"{doc.path}: {location}: {issue.message}")

    promises: dict[str, LoadedDocument] = {}
    promise_ids: set[str] = set()
    for doc in by_kind(documents, "Promise"):
        metadata = doc.data.get("metadata", {})
        domain = metadata.get("domain")
        name = metadata.get("name")
        if not isinstance(domain, str) or not isinstance(name, str):
            continue
        address = promise_address(domain, name)
        if address in promise_ids:
            errors.append(f"{doc.path}: duplicate promise address {address}")
        promise_ids.add(address)
        promises[address] = doc

        relative = doc.path.relative_to(root / ".norms" / "promises")
        expected = Path(*domain.strip("/").split("/"), f"{name}.yaml") if domain != "/" else Path(f"{name}.yaml")
        if relative != expected:
            errors.append(f"{doc.path}: promise address {address} must be stored at .norms/promises/{expected.as_posix()}")

        forbidden = sorted(set(walk_keys(doc.data)) & FORBIDDEN_PROMISE_KEYS)
        if forbidden:
            errors.append(f"{doc.path}: promise contains forbidden status/trust keys: {', '.join(forbidden)}")

        statement = str(doc.data.get("spec", {}).get("statement", ""))
        if "ought" not in statement.lower():
            warnings.append(f"{doc.path}: statement does not explicitly contain OUGHT")
        if domain == "/":
            warnings.append(f"{doc.path}: root promise is inherited by every domain")

    assessment_ids: set[str] = set()
    for doc in by_kind(documents, "Assessment"):
        metadata = doc.data.get("metadata", {})
        spec = doc.data.get("spec", {})
        assessment_id = metadata.get("id")
        if isinstance(assessment_id, str):
            if assessment_id in assessment_ids:
                errors.append(f"{doc.path}: duplicate assessment id {assessment_id}")
            assessment_ids.add(assessment_id)
        address = spec.get("promise")
        target = spec.get("effectiveDomain")
        if address not in promises:
            errors.append(f"{doc.path}: references unknown promise {address!r}")
            continue
        declaration_domain = promises[address].data["metadata"]["domain"]
        if isinstance(target, str) and not is_ancestor(declaration_domain, target):
            errors.append(f"{doc.path}: promise {address} is not effective in {target}")
        verdict = spec.get("verdict")
        evidence = spec.get("evidence", [])
        if verdict in {"kept", "broken"} and not evidence:
            warnings.append(f"{doc.path}: {verdict} assessment has no evidence")

    view_names: set[str] = set()
    for doc in by_kind(documents, "TrustView"):
        name = doc.data.get("metadata", {}).get("name")
        if isinstance(name, str):
            if name in view_names:
                errors.append(f"{doc.path}: duplicate trust view name {name}")
            view_names.add(name)
            if doc.path.stem != name:
                warnings.append(f"{doc.path}: trust view filename normally matches metadata.name ({name}.yaml)")

    local_names: dict[str, list[str]] = defaultdict(list)
    for address, doc in promises.items():
        local_names[doc.data["metadata"]["name"]].append(address)
    for name, addresses in sorted(local_names.items()):
        if len(addresses) > 1:
            warnings.append(f"local promise name {name} appears at multiple domains: {', '.join(sorted(addresses))}")

    return errors, warnings, documents


def parse_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def load_view(documents: list[LoadedDocument], name: str) -> LoadedDocument:
    matches = [doc for doc in by_kind(documents, "TrustView") if doc.data.get("metadata", {}).get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"expected one trust view named {name!r}; found {len(matches)}")
    return matches[0]


def select_assessments(
    documents: list[LoadedDocument],
    effective_addresses: set[str],
    target_domain: str,
    view: dict[str, Any],
) -> dict[str, list[LoadedDocument]]:
    spec = view["spec"]
    selection = spec["assessmentSelection"]
    assessors = selection["assessors"]
    accepted = None if assessors == "*" else set(assessors)
    revision = spec.get("snapshot", {}).get("revision")
    at_or_before = spec.get("snapshot", {}).get("atOrBefore")
    cutoff = parse_time(at_or_before) if at_or_before else None

    candidates: list[LoadedDocument] = []
    for doc in by_kind(documents, "Assessment"):
        metadata = doc.data["metadata"]
        assessment = doc.data["spec"]
        if assessment["promise"] not in effective_addresses:
            continue
        if assessment["effectiveDomain"] != target_domain:
            continue
        if accepted is not None and metadata["assessor"] not in accepted:
            continue
        if revision and metadata.get("revision") != revision:
            continue
        if cutoff and parse_time(metadata["observedAt"]) > cutoff:
            continue
        if selection.get("requireEvidence", True) and assessment["verdict"] in {"kept", "broken"} and not assessment.get("evidence"):
            continue
        candidates.append(doc)

    if selection.get("latestPerAssessor", True):
        latest: dict[tuple[str, str], LoadedDocument] = {}
        for doc in candidates:
            key = (doc.data["spec"]["promise"], doc.data["metadata"]["assessor"])
            existing = latest.get(key)
            if existing is None or parse_time(doc.data["metadata"]["observedAt"]) > parse_time(existing.data["metadata"]["observedAt"]):
                latest[key] = doc
        candidates = list(latest.values())

    grouped: dict[str, list[LoadedDocument]] = defaultdict(list)
    for doc in candidates:
        grouped[doc.data["spec"]["promise"]].append(doc)
    return grouped


def fallback_resolution(verdicts: list[str]) -> str:
    scorable = {verdict for verdict in verdicts if verdict in {"kept", "broken"}}
    if len(scorable) == 1:
        return next(iter(scorable))
    if len(scorable) > 1:
        return "disputed"
    if verdicts and all(verdict == "not_applicable" for verdict in verdicts):
        return "not_applicable"
    if "disputed" in verdicts:
        return "disputed"
    return "unknown"


def resolve_claims(claims: list[LoadedDocument], policy: str) -> str:
    if not claims:
        return "unknown"
    verdicts = [doc.data["spec"]["verdict"] for doc in claims]

    if policy in {"unknown-on-conflict", "all"}:
        return fallback_resolution(verdicts)
    if policy == "latest":
        latest = max(claims, key=lambda doc: parse_time(doc.data["metadata"]["observedAt"]))
        return latest.data["spec"]["verdict"]
    if policy == "majority":
        votes = Counter(verdict for verdict in verdicts if verdict in {"kept", "broken"})
        if not votes:
            return fallback_resolution(verdicts)
        if votes["kept"] == votes["broken"]:
            return "disputed"
        return "kept" if votes["kept"] > votes["broken"] else "broken"
    if policy == "conservative":
        if "broken" in verdicts:
            return "broken"
        if "kept" in verdicts:
            return "kept"
        return fallback_resolution(verdicts)
    raise ValueError(f"unsupported conflict policy: {policy}")


def calculate_trust(documents: list[LoadedDocument], view_doc: LoadedDocument, domain_override: str | None = None) -> dict[str, Any]:
    view = view_doc.data
    target_domain = domain_override or view["spec"]["domain"]
    effective = effective_promises(documents, target_domain)
    addresses = [address for address, _ in effective]
    grouped = select_assessments(documents, set(addresses), target_domain, view)
    policy = view["spec"]["conflictPolicy"]

    counts = {verdict: 0 for verdict in VERDICTS}
    selected_ids: list[str] = []
    unresolved: list[str] = []
    results: list[dict[str, Any]] = []

    for address in addresses:
        claims = sorted(grouped.get(address, []), key=lambda doc: doc.data["metadata"]["observedAt"])
        verdict = resolve_claims(claims, policy)
        counts[verdict] += 1
        ids = [doc.data["metadata"]["id"] for doc in claims]
        selected_ids.extend(ids)
        if verdict in {"unknown", "disputed"}:
            unresolved.append(address)
        results.append({"promise": address, "verdict": verdict, "assessmentIds": ids})

    scorable = counts["kept"] + counts["broken"]
    relevant = len(addresses) - counts["not_applicable"]
    score = counts["kept"] / scorable if scorable else None
    coverage = scorable / relevant if relevant else 0.0

    return {
        "apiVersion": "norms/v1",
        "kind": "TrustReport",
        "metadata": {
            "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "toolVersion": TOOL_VERSION,
            "view": view["metadata"]["name"],
        },
        "spec": {
            "observer": view["spec"]["observer"],
            "domain": target_domain,
            "snapshot": view["spec"].get("snapshot", {}),
            "score": score,
            "coverage": coverage,
            "effectivePromiseCount": len(addresses),
            "counts": counts,
            "conflictPolicy": policy,
            "selectedAssessmentIds": sorted(set(selected_ids)),
            "unresolved": unresolved,
            "results": results,
        },
    }


def domain_parent(domain: str) -> "str | None":
    if domain == "/":
        return None
    segments = domain.strip("/").split("/")
    return "/" if len(segments) == 1 else "/" + "/".join(segments[:-1])


def domain_depth(domain: str) -> int:
    return 0 if domain == "/" else domain.strip("/").count("/") + 1


def all_domains_with_ancestors(domains: Iterable[str]) -> "list[str]":
    result = {"/"}
    for domain in domains:
        if domain == "/":
            continue
        segments = domain.strip("/").split("/")
        for index in range(1, len(segments) + 1):
            result.add("/" + "/".join(segments[:index]))
    return sorted(result, key=lambda value: (domain_depth(value), value))


def build_explorer(documents: list[LoadedDocument]) -> dict[str, Any]:
    """Assemble one normalized model for the read-only Promises explorer UI.

    Reuses the same inheritance and trust logic the CLI uses, so the frontend
    never re-implements resolution, assessment selection, or scoring.
    """
    promise_index = index_promises(documents)
    view_docs = by_kind(documents, "TrustView")
    assessment_docs = by_kind(documents, "Assessment")

    repository_docs = by_kind(documents, "Repository")
    repo_meta = repository_docs[0].data.get("metadata", {}) if repository_docs else {}
    repo_spec = repository_docs[0].data.get("spec", {}) if repository_docs else {}
    explicit_domains = repo_spec.get("domains", [])
    subjects_by_domain = {
        item["path"]: item["subjects"]
        for item in explicit_domains
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }

    mentioned = {doc.data["metadata"]["domain"] for doc in by_kind(documents, "Promise")}
    mentioned |= {doc.data["spec"]["effectiveDomain"] for doc in assessment_docs}
    mentioned |= {doc.data["spec"]["domain"] for doc in view_docs}
    mentioned |= set(subjects_by_domain)
    domains = all_domains_with_ancestors(mentioned)
    domain_set = set(domains)

    declared_by_domain: dict[str, list[str]] = defaultdict(list)
    for address, doc in promise_index.items():
        declared_by_domain[doc.data["metadata"]["domain"]].append(address)

    effective_by_domain: dict[str, list[dict[str, Any]]] = {}
    domain_records: list[dict[str, Any]] = []
    for domain in domains:
        effective = effective_promises(documents, domain)
        effective_by_domain[domain] = [
            {
                "promise": address,
                "declaredAt": doc.data["metadata"]["domain"],
                "inherited": doc.data["metadata"]["domain"] != domain,
                "title": doc.data["metadata"].get("title"),
                "statement": doc.data["spec"]["statement"],
            }
            for address, doc in effective
        ]
        domain_records.append(
            {
                "domain": domain,
                "parent": domain_parent(domain),
                "depth": domain_depth(domain),
                "children": sorted(child for child in domain_set if domain_parent(child) == domain),
                "subjects": subjects_by_domain.get(domain, []),
                "declaredCount": len(declared_by_domain.get(domain, [])),
                "effectivePromiseCount": len(effective),
            }
        )

    promises = []
    for address, doc in sorted(promise_index.items()):
        metadata, spec = doc.data["metadata"], doc.data["spec"]
        promises.append(
            {
                "address": address,
                "domain": metadata["domain"],
                "name": metadata["name"],
                "title": metadata.get("title"),
                "tags": metadata.get("tags", []),
                "statement": spec["statement"],
                "subjects": spec.get("scope", {}).get("subjects", []),
                "criteria": spec.get("criteria", {}),
                "source": spec.get("source", {}),
            }
        )

    assessments = []
    for doc in sorted(assessment_docs, key=lambda item: item.data["metadata"].get("observedAt", "")):
        metadata, spec = doc.data["metadata"], doc.data["spec"]
        assessments.append(
            {
                "id": metadata.get("id"),
                "assessor": metadata.get("assessor"),
                "observedAt": metadata.get("observedAt"),
                "revision": metadata.get("revision"),
                "promise": spec.get("promise"),
                "effectiveDomain": spec.get("effectiveDomain"),
                "verdict": spec.get("verdict"),
                "confidence": spec.get("confidence"),
                "rationale": spec.get("rationale"),
                "evidence": spec.get("evidence", []),
            }
        )

    views = []
    for doc in view_docs:
        metadata, spec = doc.data["metadata"], doc.data["spec"]
        views.append(
            {
                "name": metadata["name"],
                "description": metadata.get("description"),
                "observer": spec["observer"],
                "domain": spec["domain"],
                "snapshot": spec.get("snapshot", {}),
                "conflictPolicy": spec["conflictPolicy"],
                "assessmentSelection": spec.get("assessmentSelection", {}),
            }
        )

    trust = []
    for view_doc in view_docs:
        for domain in domains:
            try:
                report = calculate_trust(documents, view_doc, domain)
            except (ValueError, KeyError):
                continue
            trust.append({"view": view_doc.data["metadata"]["name"], "domain": domain, **report["spec"]})

    return {
        "apiVersion": "norms/v1",
        "kind": "Explorer",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "toolVersion": TOOL_VERSION,
        "repository": {
            "name": repo_meta.get("name"),
            "description": repo_meta.get("description"),
            "defaultView": repo_spec.get("defaultView"),
        },
        "domains": domain_records,
        "effective": effective_by_domain,
        "promises": promises,
        "assessments": assessments,
        "views": views,
        "trust": trust,
    }


def command_explorer(args: argparse.Namespace) -> int:
    root = Path(args.repository).resolve()
    errors, warnings, documents = validate_repository(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    output = json.dumps(build_explorer(documents), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        destination = Path(args.output).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    root = Path(args.repository).resolve()
    errors, warnings, documents = validate_repository(root)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"Validation failed: {len(errors)} error(s), {len(warnings)} warning(s).", file=sys.stderr)
        return 1
    print(f"Validation passed: {len(documents)} document(s), {len(warnings)} warning(s).")
    return 0


def command_effective(args: argparse.Namespace) -> int:
    root = Path(args.repository).resolve()
    errors, warnings, documents = validate_repository(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    entries = []
    for address, doc in effective_promises(documents, args.domain):
        declared = doc.data["metadata"]["domain"]
        entries.append(
            {
                "promise": address,
                "declaredAt": declared,
                "effectiveAt": args.domain,
                "inherited": declared != args.domain,
                "statement": doc.data["spec"]["statement"],
            }
        )
    print(dump_yaml({"domain": args.domain, "effectivePromises": entries}), end="")
    return 0


def command_trust(args: argparse.Namespace) -> int:
    root = Path(args.repository).resolve()
    errors, warnings, documents = validate_repository(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    try:
        view_doc = load_view(documents, args.view)
        report = calculate_trust(documents, view_doc, args.domain)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(dump_yaml(report), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and query norms/v1 repository data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate .norms documents and semantic invariants.")
    validate_parser.add_argument("repository", help="Repository root containing .norms/")
    validate_parser.set_defaults(handler=command_validate)

    effective_parser = subparsers.add_parser("effective", help="List promises effective in a domain.")
    effective_parser.add_argument("repository", help="Repository root containing .norms/")
    effective_parser.add_argument("domain", help="Absolute target domain, such as /software/python")
    effective_parser.set_defaults(handler=command_effective)

    trust_parser = subparsers.add_parser("trust", help="Calculate an observer-relative trust report.")
    trust_parser.add_argument("repository", help="Repository root containing .norms/")
    trust_parser.add_argument("--view", required=True, help="Trust view metadata.name")
    trust_parser.add_argument("--domain", help="Optional target-domain override")
    trust_parser.set_defaults(handler=command_trust)

    explorer_parser = subparsers.add_parser(
        "explorer", help="Emit one normalized JSON model for the read-only explorer UI."
    )
    explorer_parser.add_argument("repository", help="Repository root containing .norms/")
    explorer_parser.add_argument("--output", help="Write the generated explorer JSON to this path")
    explorer_parser.set_defaults(handler=command_explorer)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
