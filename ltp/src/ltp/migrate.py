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


def needs_migration(data: "dict[str, Any]") -> bool:
    if int(data.get("schema_version", 1)) >= 2:
        return False
    if "links" in data:
        return True
    for entity in data.get("entities", []):
        if isinstance(entity, dict) and "type" in entity:
            return True
    return False


def migrate_dict(data: "dict[str, Any]") -> "dict[str, Any]":
    if not isinstance(data, dict):
        raise MigrationError("v1 model must be a mapping")

    notes: "list[str]" = list(data.get("open_questions", []))
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
            **({"provisional_goal": project["provisional_goal"]} if project.get("provisional_goal") else {}),
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
    if notes:
        out["open_questions"] = notes
    if data.get("contradictions"):
        out["contradictions"] = data["contradictions"]
    if data.get("coverage_gaps"):
        out["coverage_gaps"] = data["coverage_gaps"]
    return out
