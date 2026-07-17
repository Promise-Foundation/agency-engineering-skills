"""Migrate a v1 permissive model to the v2 typed model, preserving ids.

v1 stored generic ``links`` with free-string ``relation``/``logic`` and a single
``status`` per entity. v2 replaces links with typed claims and splits status into
``basis`` + ``review_status``. The migration is deliberately conservative: it
maps everything it can prove and records the rest as ``open_questions`` prefixed
``migrated:`` rather than inventing structure. The result is a v2 skeleton you
then run ``ltp validate`` against and repair -- migration produces honest gaps,
not plausible filler.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .errors import MigrationError

# v1 entity ``type`` -> v2 ``kind``.
_KIND_MAP = {
    "goal": "goal",
    "critical_success_factor": "critical_success_factor",
    "necessary_condition": "necessary_condition",
    "undesirable_effect": "undesirable_effect",
    "cause": "cause",
    "root_cause": "root_cause",
    "constraint": "constraint",
    "injection": "injection",
    "desirable_effect": "desirable_effect",
    "negative_branch": "negative_branch",
    "trimming_injection": "trimming_injection",
    "obstacle": "obstacle",
    "intermediate_objective": "intermediate_objective",
    "assumption": "assumption",
    "existing_reality": "existing_reality",
    "immediate_effect": "immediate_effect",
    # cloud / transition v1 vocabulary
    "common_objective": "cloud_objective",
    "need": "cloud_need",
    "option": "cloud_action",
    "action": "transition_action",
    "expected_effect": "immediate_effect",
}

# v1 ``status`` -> (basis, review_status).
_STATUS_MAP = {
    "observed": ("observed", "unreviewed"),
    "inferred": ("inferred", "unreviewed"),
    "provisional": ("provisional", "unreviewed"),
    "confirmed": ("inferred", "user_confirmed"),
    "disputed": ("inferred", "disputed"),
}

_NECESSITY_RELATIONS = {"necessary_for", "believed_necessary_for"}
_CAUSAL_RELATIONS = {"causes", "contributes_to"}


_KNOWN_V1_KEYS = frozenset(
    {
        "schema_version", "project", "candidate_goals", "entities", "links",
        "assumptions", "evidence", "open_questions", "contradictions",
        "coverage_gaps", "views", "analysis",
    }
)


def _to_text(item: Any) -> str:
    """Flatten a v1 note (string or structured dict) into a v2 string."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        body = next(
            (item[key] for key in ("question", "statement", "label", "text", "summary", "reason")
             if item.get(key)),
            None,
        )
        if body is None:
            body = "; ".join(f"{k}={v}" for k, v in item.items() if k != "id")
        record_id = item.get("id")
        text = " ".join(str(body).split())
        return f"{record_id}: {text}" if record_id else text
    return str(item)


def needs_migration(data: "dict[str, Any]") -> bool:
    return int(data.get("schema_version", 1)) < 3


def _migrate_v1_to_v2(data: "dict[str, Any]") -> "dict[str, Any]":
    if not isinstance(data, dict):
        raise MigrationError("v1 model must be a mapping")

    notes: "list[str]" = []
    for key in data:
        if key not in _KNOWN_V1_KEYS:
            notes.append(f"migrated: dropped unrecognized v1 field {key!r}")
    entities: "list[dict[str, Any]]" = []
    kind_by_id: "dict[str, str]" = {}

    for raw in data.get("entities", []):
        v1_type = str(raw.get("type", "")).strip()
        kind = _KIND_MAP.get(v1_type)
        if kind is None:
            kind = "cause"
            notes.append(
                f"migrated: entity {raw.get('id')} had unmapped type {v1_type!r}; "
                "defaulted to kind 'cause' -- reclassify it"
            )
        basis, review = _STATUS_MAP.get(str(raw.get("status", "inferred")), ("inferred", "unreviewed"))
        entity: "dict[str, Any]" = {
            "id": raw["id"],
            "kind": kind,
            "statement": raw.get("statement", ""),
            "basis": basis,
            "review_status": review,
            "confidence": raw.get("confidence", "medium"),
        }
        if raw.get("evidence"):
            entity["evidence_refs"] = list(raw["evidence"])
        if raw.get("assumptions"):
            entity["assumption_refs"] = list(raw["assumptions"])
        if raw.get("reasoning"):
            entity["reasoning"] = raw["reasoning"]
        entities.append(entity)
        kind_by_id[raw["id"]] = kind

    existing_ids = {entity["id"] for entity in entities}
    provisional_goal = data.get("project", {}).get("provisional_goal")

    # v1 candidate_goals were a separate list -> promote them to goal entities and
    # select the provisional goal so the migrated model has a Goal Tree root.
    for candidate in data.get("candidate_goals", []):
        goal_id = candidate.get("id")
        if not goal_id:
            continue
        if candidate.get("selected") and not provisional_goal:
            provisional_goal = goal_id
        if goal_id in existing_ids:
            continue
        basis, review = _STATUS_MAP.get(str(candidate.get("status", "inferred")), ("inferred", "unreviewed"))
        goal_entity: "dict[str, Any]" = {
            "id": goal_id,
            "kind": "goal",
            "statement": candidate.get("statement") or candidate.get("label", ""),
            "basis": basis,
            "review_status": review,
            "confidence": candidate.get("confidence", "medium"),
        }
        if candidate.get("evidence"):
            goal_entity["evidence_refs"] = list(candidate["evidence"])
        entities.append(goal_entity)
        existing_ids.add(goal_id)

    # v1 kept assumptions in a top-level list; v2 makes them first-class entities.
    for assumption in data.get("assumptions", []):
        assumption_id = assumption.get("id")
        if not assumption_id or assumption_id in existing_ids:
            continue
        basis, review = _STATUS_MAP.get(str(assumption.get("status", "inferred")), ("inferred", "unreviewed"))
        entities.append(
            {
                "id": assumption_id,
                "kind": "assumption",
                "statement": assumption.get("statement", ""),
                "basis": basis,
                "review_status": review,
                "confidence": assumption.get("confidence", "medium"),
            }
        )
        existing_ids.add(assumption_id)

    necessity_claims: "list[dict[str, Any]]" = []
    causal_claims: "list[dict[str, Any]]" = []
    obstacle_resolutions: "list[dict[str, Any]]" = []
    produces: "dict[str, str]" = {}   # action id -> immediate effect id
    achieves: "dict[str, str]" = {}   # effect id -> advanced entity id
    nec_counter = causal_counter = or_counter = 0

    for link in data.get("links", []):
        relation = str(link.get("relation", "")).strip()
        source, target = link.get("from"), link.get("to")
        assumption = link.get("assumption")
        if relation in _NECESSITY_RELATIONS:
            nec_counter += 1
            claim = {"id": f"NEC-M{nec_counter}", "prerequisite": source, "objective": target}
            if assumption:
                claim["assumption_refs"] = [assumption]
            necessity_claims.append(claim)
        elif relation == "enables":
            nec_counter += 1
            necessity_claims.append({"id": f"NEC-M{nec_counter}", "prerequisite": source, "objective": target})
        elif relation in _CAUSAL_RELATIONS:
            causal_counter += 1
            claim = {"id": f"CLM-M{causal_counter}", "premises": [source], "operator": "single", "conclusion": target}
            if assumption:
                claim["assumption_refs"] = [assumption]
            causal_claims.append(claim)
        elif relation == "overcome_by":
            or_counter += 1
            obstacle_resolutions.append(
                {"id": f"OR-M{or_counter}", "obstacle": source, "intermediate_objective": target}
            )
        elif relation == "produces":
            produces[source] = target
        elif relation in {"achieves", "advances"}:
            achieves[source] = target
        elif relation == "conflicts_with":
            notes.append(
                f"migrated: link {source}<->{target} was a conflict; reconstruct a "
                "first-class Cloud (five roles, four necessity claims, a conflict_claim)"
            )
        else:
            causal_counter += 1
            causal_claims.append(
                {"id": f"CLM-M{causal_counter}", "premises": [source], "operator": "single", "conclusion": target}
            )
            notes.append(
                f"migrated: link relation {relation!r} ({source}->{target}) mapped to a "
                "generic causal claim -- confirm it"
            )

    # Synthesize transitions from action --produces--> effect --achieves--> IO.
    transitions: "list[dict[str, Any]]" = []
    tr_counter = 0
    for action_id, effect_id in produces.items():
        tr_counter += 1
        advances = achieves.get(effect_id, effect_id)
        transition = {"id": f"TR-M{tr_counter}", "action": action_id, "advances": advances}
        if effect_id in kind_by_id:
            transition["immediate_effect"] = effect_id
        transitions.append(transition)
        if advances == effect_id:
            notes.append(
                f"migrated: transition {transition['id']} could not find the IO it "
                "advances; set 'advances' to a real intermediate_objective"
            )

    project = dict(data.get("project", {}))
    mode = project.get("analysis_mode")
    if mode not in ("forward", "reverse", "reconciliation"):
        mode = None

    out: "dict[str, Any]" = {
        "schema_version": 2,
        "project": {
            "name": project.get("name", "Migrated project"),
            **({"analyzed_path": project["analyzed_path"]} if project.get("analyzed_path") else {}),
            **({"analysis_mode": mode} if mode else {}),
            **({"provisional_goal": provisional_goal} if provisional_goal else {}),
        },
        "entities": entities,
    }
    if data.get("analysis"):
        out["analysis"] = {k: v for k, v in data["analysis"].items() if v is not None}
    if data.get("evidence"):
        out["evidence"] = data["evidence"]
    if necessity_claims:
        out["necessity_claims"] = necessity_claims
    if causal_claims:
        out["causal_claims"] = causal_claims
    if obstacle_resolutions:
        out["obstacle_resolutions"] = obstacle_resolutions
    if transitions:
        out["transitions"] = transitions
    open_questions = [_to_text(question) for question in data.get("open_questions", [])] + notes
    if open_questions:
        out["open_questions"] = open_questions
    if data.get("contradictions"):
        out["contradictions"] = [_to_text(item) for item in data["contradictions"]]
    if data.get("coverage_gaps"):
        out["coverage_gaps"] = [_to_text(item) for item in data["coverage_gaps"]]
    return out


def _migrate_v2_to_v3(data: "dict[str, Any]") -> "dict[str, Any]":
    """Move preventive trimming links out of forward causal sufficiency."""
    out = deepcopy(data)
    out["schema_version"] = 3
    kinds = {
        entity.get("id"): entity.get("kind")
        for entity in out.get("entities", [])
        if isinstance(entity, dict)
    }
    kept: "list[dict[str, Any]]" = []
    moved: "list[dict[str, Any]]" = list(out.get("semantic_relations", []))
    moved_ids: "set[str]" = set()
    for claim in out.get("causal_claims", []):
        premises = claim.get("premises", [])
        conclusion = claim.get("conclusion")
        if (
            len(premises) == 1
            and kinds.get(premises[0]) == "trimming_injection"
            and kinds.get(conclusion) == "negative_branch"
        ):
            moved_ids.add(claim["id"])
            relation: "dict[str, Any]" = {
                "id": claim["id"],
                "source": premises[0],
                "target": conclusion,
                "relation": "neutralizes",
            }
            if claim.get("assumption_refs"):
                relation["reasoning"] = (
                    "migrated from a v2 causal claim; review assumptions "
                    + ", ".join(claim["assumption_refs"])
                )
            moved.append(relation)
        else:
            kept.append(claim)
    if moved_ids:
        out["causal_claims"] = kept
        out["semantic_relations"] = moved
        for view in out.get("views", {}).values():
            if not isinstance(view, dict):
                continue
            claims = view.get("claims", [])
            selected = [claim_id for claim_id in claims if claim_id in moved_ids]
            if selected:
                view["claims"] = [claim_id for claim_id in claims if claim_id not in moved_ids]
                view["relations"] = list(dict.fromkeys(view.get("relations", []) + selected))
    return out


def migrate_dict(data: "dict[str, Any]") -> "dict[str, Any]":
    """Migrate any supported legacy model to the current v3 schema."""
    if not isinstance(data, dict):
        raise MigrationError("model must be a mapping")
    version = int(data.get("schema_version", 1))
    if version > 3:
        raise MigrationError(f"model schema v{version} is newer than this engine")
    if version < 2:
        return _migrate_v2_to_v3(_migrate_v1_to_v2(data))
    if version == 2:
        return _migrate_v2_to_v3(data)
    return deepcopy(data)
