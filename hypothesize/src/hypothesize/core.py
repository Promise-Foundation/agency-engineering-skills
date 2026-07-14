"""The reusable research-status engine.

Derives an honest project status from three deliberately separate inputs and
never lets one stand in for another:

* **Capability status** is a pure function of tagged acceptance scenarios.
* **Evidence maturity** reflects the strongest admitted evidence artifact.
* **Scientific conclusion** changes only for a qualified, preregistered result.

This module contains only generic machinery. Project-specific knowledge — the
portfolio contents, how evidence is collected, and where projections are written
— lives in the consuming project's configuration and collectors.

Extracted and generalized from the Graphist and Uptake Integrity Protocol
research-status services so a single engine derives both without divergence.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any, Optional


class ResearchStatusError(ValueError):
    """The research publication inputs are inconsistent or untraceable."""


CONCLUSIONS = {"not_tested", "supported", "falsified", "inconclusive"}
SCENARIO_STATUSES = {"passed", "failed", "skipped", "untested", "undefined", "error"}
# Maturity ladder, weakest to strongest. ``design`` sits between ``none`` and a
# demonstrated ``mechanism``: a protocol exists but no mechanism has been shown.
MATURITY_ORDER = {
    "none": 0,
    "design": 1,
    "mechanism": 2,
    "internal_pilot": 3,
    "comparative_pilot": 4,
    "external_replication": 5,
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _index(items: Sequence[Mapping[str, Any]], label: str) -> "dict[str, Mapping[str, Any]]":
    result: "dict[str, Mapping[str, Any]]" = {}
    for item in items:
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            raise ResearchStatusError(f"{label} has no id")
        if item_id in result:
            raise ResearchStatusError(f"duplicate {label} id {item_id}")
        result[item_id] = item
    return result


class ResearchStatusService:
    """Validate inputs, derive status, and render publication projections.

    ``maturity_fallback`` is the maturity assigned to a hypothesis that has
    passing scenarios but no maturity-bearing evidence or evidence-role tag. With
    ``fallback_requires_pass`` (the default) only *passed* scenarios trigger it;
    skipped or specified-only scenarios never do.
    """

    def __init__(
        self,
        *,
        maturity_fallback: str = "design",
        fallback_requires_pass: bool = True,
    ) -> None:
        if maturity_fallback not in MATURITY_ORDER:
            raise ResearchStatusError(f"unknown maturity fallback {maturity_fallback}")
        self._maturity_fallback = maturity_fallback
        self._fallback_requires_pass = fallback_requires_pass

    # -- validation --------------------------------------------------------
    def validate(
        self,
        catalog: Mapping[str, Any],
        scenarios: Sequence[Mapping[str, Any]],
        evidence: Sequence[Mapping[str, Any]],
    ) -> None:
        hypotheses = _index(list(catalog.get("hypotheses", [])), "hypothesis")
        tracks = _index(list(catalog.get("tracks", [])), "track")
        capabilities = _index(list(catalog.get("capabilities", [])), "capability")
        requirements = _index(list(catalog.get("requirements", [])), "requirement")
        use_cases = _index(list(catalog.get("use_cases", [])), "use case")
        studies = _index(list(catalog.get("studies", [])), "study")

        for hypothesis in hypotheses.values():
            self._validate_refs(hypothesis, tracks, "tracks", "track")

        for capability in capabilities.values():
            self._validate_refs(capability, hypotheses, "hypotheses", "hypothesis")

        for requirement in requirements.values():
            self._validate_refs(requirement, hypotheses, "hypotheses", "hypothesis")
            self._validate_refs(requirement, capabilities, "capabilities", "capability")

        for use_case in use_cases.values():
            self._validate_refs(use_case, hypotheses, "hypotheses", "hypothesis")
            self._validate_refs(use_case, capabilities, "capabilities", "capability")

        for study in studies.values():
            self._validate_refs(study, hypotheses, "hypotheses", "hypothesis")
            self._validate_refs(study, use_cases, "use_cases", "use case")

        _index(scenarios, "scenario")
        for scenario in scenarios:
            self._validate_refs(scenario, hypotheses, "hypotheses", "hypothesis")
            self._validate_refs(scenario, capabilities, "capabilities", "capability")
            status = str(scenario.get("status", "untested"))
            if status not in SCENARIO_STATUSES:
                raise ResearchStatusError(
                    f"scenario {scenario['id']} has unknown status {status}"
                )

        _index(evidence, "evidence")
        for item in evidence:
            self._validate_refs(item, hypotheses, "hypotheses", "hypothesis")
            outcome = str(item.get("outcome", "not_tested"))
            if outcome not in CONCLUSIONS:
                raise ResearchStatusError(
                    f"evidence {item['id']} has unknown outcome {outcome}"
                )
            maturity = str(item.get("maturity", "none"))
            if maturity not in MATURITY_ORDER:
                raise ResearchStatusError(
                    f"evidence {item['id']} has unknown maturity {maturity}"
                )

    @staticmethod
    def _validate_refs(
        item: Mapping[str, Any],
        known: Mapping[str, Mapping[str, Any]],
        field: str,
        label: str,
    ) -> None:
        for reference in item.get(field, []):
            if reference not in known:
                raise ResearchStatusError(
                    f"{item.get('id', 'item')} references unknown {label} {reference}"
                )

    # -- publication -------------------------------------------------------
    def publish(
        self,
        *,
        catalog: Mapping[str, Any],
        scenarios: Sequence[Mapping[str, Any]],
        evidence: Sequence[Mapping[str, Any]],
        previous: Optional[Mapping[str, Any]] = None,
        results: Optional[Mapping[str, Any]] = None,
    ) -> "dict[str, Any]":
        self.validate(catalog, scenarios, evidence)
        normalized_scenarios = [deepcopy(dict(item)) for item in scenarios]
        normalized_evidence = [deepcopy(dict(item)) for item in evidence]
        source = {
            "catalog": deepcopy(dict(catalog)),
            "scenarios": normalized_scenarios,
            "evidence": normalized_evidence,
            "previous": deepcopy(dict(previous)) if previous is not None else None,
            "results": deepcopy(dict(results)) if results is not None else None,
        }
        source_hash = hashlib.sha256(_canonical(source).encode()).hexdigest()

        capability_rows = self._derive_capabilities(catalog, normalized_scenarios, previous)
        hypothesis_rows = self._derive_hypotheses(
            catalog, normalized_scenarios, normalized_evidence, capability_rows, previous
        )
        quarantined = [
            item
            for item in normalized_evidence
            if item.get("kind") == "scientific"
            and item.get("outcome") != "not_tested"
            and not self._is_qualified_scientific(item)
        ]

        manifest: "dict[str, Any]" = {
            "schema_version": int(catalog.get("schema_version", 1)),
            "portfolio": {
                "title": str(catalog.get("title", "")),
                "thesis": str(catalog.get("thesis", "")),
                "last_reviewed": str(catalog.get("last_reviewed", "")),
            },
            "build": {
                "source_hash": source_hash,
                "scenario_counts": self._scenario_counts(normalized_scenarios),
                "evidence_count": len(normalized_evidence),
            },
            "hypotheses": hypothesis_rows,
            "capabilities": capability_rows,
            "studies": [deepcopy(dict(item)) for item in catalog.get("studies", [])],
            "limitations": [deepcopy(dict(item)) for item in catalog.get("limitations", [])],
            "evidence": normalized_evidence,
            "quarantined_evidence": quarantined,
        }
        # Conditional sections: include only what the catalog/inputs provide so a
        # minimal portfolio does not gain empty keys and a rich one keeps its own.
        if catalog.get("tracks"):
            manifest["tracks"] = self._derive_tracks(catalog, hypothesis_rows)
        if catalog.get("use_cases"):
            manifest["use_cases"] = self._derive_use_cases(catalog, capability_rows)
        if catalog.get("requirements"):
            manifest["requirements"] = [
                deepcopy(dict(item)) for item in catalog.get("requirements", [])
            ]
        if results is not None:
            manifest["results"] = deepcopy(dict(results))

        return {
            "manifest": manifest,
            "markdown": self.render_markdown(manifest),
            "use_case_markdown": self.render_use_case_markdown(manifest),
        }

    def _derive_capabilities(
        self,
        catalog: Mapping[str, Any],
        scenarios: Sequence[Mapping[str, Any]],
        previous: Optional[Mapping[str, Any]],
    ) -> "list[dict[str, Any]]":
        previous_rows = {
            str(item["id"]): item for item in (previous or {}).get("capabilities", [])
        }
        rows: "list[dict[str, Any]]" = []
        for capability in catalog.get("capabilities", []):
            capability_id = str(capability["id"])
            linked = [
                item for item in scenarios if capability_id in item.get("capabilities", [])
            ]
            required = [item for item in linked if item.get("required", True)]
            statuses = [str(item.get("status", "untested")) for item in required]
            prior = previous_rows.get(capability_id, {})
            status = self._capability_status(statuses, str(prior.get("status", "")))
            rows.append(
                {
                    **deepcopy(dict(capability)),
                    "status": status,
                    "scenario_counts": self._scenario_counts(linked),
                    "scenario_ids": [str(item["id"]) for item in linked],
                }
            )
        return rows

    @staticmethod
    def _capability_status(statuses: Sequence[str], previous: str) -> str:
        if not statuses:
            return "specified"
        if any(status in {"failed", "undefined", "error"} for status in statuses):
            return "regressed" if previous == "implemented" else "failing"
        if all(status == "passed" for status in statuses):
            return "implemented"
        if any(status == "passed" for status in statuses):
            return "partial"
        return "specified"

    def _derive_hypotheses(
        self,
        catalog: Mapping[str, Any],
        scenarios: Sequence[Mapping[str, Any]],
        evidence: Sequence[Mapping[str, Any]],
        capabilities: Sequence[Mapping[str, Any]],
        previous: Optional[Mapping[str, Any]],
    ) -> "list[dict[str, Any]]":
        previous_rows = {
            str(item["id"]): item for item in (previous or {}).get("hypotheses", [])
        }
        rows: "list[dict[str, Any]]" = []
        for hypothesis in catalog.get("hypotheses", []):
            hypothesis_id = str(hypothesis["id"])
            linked_evidence = [
                item for item in evidence if hypothesis_id in item.get("hypotheses", [])
            ]
            linked_scenarios = [
                item for item in scenarios if hypothesis_id in item.get("hypotheses", [])
            ]
            linked_capabilities = [
                item for item in capabilities if hypothesis_id in item.get("hypotheses", [])
            ]
            qualified = [
                item for item in linked_evidence if self._is_qualified_scientific(item)
            ]
            previous_conclusion = str(
                previous_rows.get(hypothesis_id, {}).get("conclusion", "not_tested")
            )
            conclusion = str(qualified[-1]["outcome"]) if qualified else previous_conclusion
            maturity = self._maturity(linked_evidence, linked_scenarios)
            capability_status = self._hypothesis_capability_status(linked_capabilities)
            evidence_health = (
                "regressed"
                if any(item["status"] == "regressed" for item in linked_capabilities)
                else "current"
            )
            rows.append(
                {
                    **deepcopy(dict(hypothesis)),
                    "capability_status": capability_status,
                    "evidence_maturity": maturity,
                    "conclusion": conclusion,
                    "evidence_health": evidence_health,
                    "scenario_counts": self._scenario_counts(linked_scenarios),
                    "evidence": [str(item["id"]) for item in linked_evidence],
                }
            )
        return rows

    @staticmethod
    def _is_qualified_scientific(item: Mapping[str, Any]) -> bool:
        return (
            item.get("kind") == "scientific"
            and bool(item.get("qualified"))
            and bool(item.get("preregistered"))
            and item.get("outcome") in {"supported", "falsified", "inconclusive"}
        )

    @staticmethod
    def _hypothesis_capability_status(capabilities: Sequence[Mapping[str, Any]]) -> str:
        statuses = {str(item["status"]) for item in capabilities}
        if "regressed" in statuses:
            return "regressed"
        if "failing" in statuses:
            return "failing"
        if statuses and statuses == {"implemented"}:
            return "implemented"
        if "implemented" in statuses or "partial" in statuses:
            return "partial"
        return "specified"

    def _maturity(
        self,
        evidence: Sequence[Mapping[str, Any]],
        scenarios: Sequence[Mapping[str, Any]],
    ) -> str:
        maturities = [str(item.get("maturity", "none")) for item in evidence]
        candidate_scenarios = (
            [item for item in scenarios if item.get("status") == "passed"]
            if self._fallback_requires_pass
            else list(scenarios)
        )
        for item in candidate_scenarios:
            kind = str(item.get("evidence_kind", "capability"))
            if kind in MATURITY_ORDER:
                maturities.append(kind)
        if not maturities and candidate_scenarios:
            maturities.append(self._maturity_fallback)
        return max(maturities or ["none"], key=MATURITY_ORDER.__getitem__)

    @staticmethod
    def _derive_use_cases(
        catalog: Mapping[str, Any], capabilities: Sequence[Mapping[str, Any]]
    ) -> "list[dict[str, Any]]":
        capability_index = {str(item["id"]): item for item in capabilities}
        rows: "list[dict[str, Any]]" = []
        for use_case in catalog.get("use_cases", []):
            linked = [
                capability_index[capability_id]
                for capability_id in use_case.get("capabilities", [])
                if capability_id in capability_index
            ]
            statuses = {str(item["status"]) for item in linked}
            if "regressed" in statuses:
                implementation = "regressed"
            elif "failing" in statuses:
                implementation = "failing"
            elif not linked:
                implementation = "not_started"
            elif statuses & {"implemented", "partial"}:
                implementation = str(
                    use_case.get("implementation_ceiling", "adjacent_mechanisms")
                )
            else:
                implementation = "specified_only"
            rows.append(
                {
                    **deepcopy(dict(use_case)),
                    "implementation": implementation,
                    "capability_statuses": {
                        str(item["id"]): str(item["status"]) for item in linked
                    },
                }
            )
        return rows

    @staticmethod
    def _derive_tracks(
        catalog: Mapping[str, Any], hypotheses: Sequence[Mapping[str, Any]]
    ) -> "list[dict[str, Any]]":
        rows: "list[dict[str, Any]]" = []
        for track in catalog.get("tracks", []):
            track_id = str(track["id"])
            linked = [item for item in hypotheses if track_id in item.get("tracks", [])]
            rows.append(
                {
                    **deepcopy(dict(track)),
                    "hypotheses": [str(item["id"]) for item in linked],
                    "conclusions": {
                        conclusion: sum(item["conclusion"] == conclusion for item in linked)
                        for conclusion in sorted(CONCLUSIONS)
                    },
                }
            )
        return rows

    @staticmethod
    def _scenario_counts(scenarios: Sequence[Mapping[str, Any]]) -> "dict[str, int]":
        return {
            status: sum(item.get("status", "untested") == status for item in scenarios)
            for status in sorted(SCENARIO_STATUSES)
        }

    @staticmethod
    def render_markdown(manifest: Mapping[str, Any]) -> str:
        lines = [
            "| ID | Hypothesis | Capability | Evidence | Conclusion | Health | Current reading |",
            "|---|---|---|---|---|---|---|",
        ]
        for item in manifest["hypotheses"]:
            lines.append(
                f"| **{item['id']}** | **{item['title']}** | "
                f"{item['capability_status']} | "
                f"{item['evidence_maturity']} | {item['conclusion']} | "
                f"{item['evidence_health']} | {item.get('summary', '')} |"
            )
        return "\n".join(lines) + "\n"

    @staticmethod
    def render_use_case_markdown(manifest: Mapping[str, Any]) -> str:
        lines = [
            "| ID | Use case | Priority | Specification | Implementation | Validation | "
            "Hypotheses |",
            "|---|---|---|---|---|---|---|",
        ]
        for item in manifest.get("use_cases", []):
            hypothesis_text = ", ".join(f"`{value}`" for value in item["hypotheses"])
            document = str(item["path"]).rsplit("/", 1)[-1]
            lines.append(
                f"| **{item['id']}** | [{item['title']}](./{document}) | "
                f"{item['priority']} | {item['specification']} | "
                f"{item['implementation']} | {item['validation']} | {hypothesis_text} |"
            )
        return "\n".join(lines) + "\n"
