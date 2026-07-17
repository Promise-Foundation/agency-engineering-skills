"""Deterministic Markdown deliverables (00-09).

Every document is a pure function of the model (and its validation report), so
running the renderer twice on the same model yields byte-identical files. The
documents never restate membership -- they read it back from the same typed
model the dashboard uses.
"""

from __future__ import annotations

from typing import Optional

from ..diagnostics import Diagnostic
from ..enums import EntityKind
from ..models import LtpModel, ModelIndex
from .mermaid import diagram_for
from .views import derive_views


def _table(headers: "list[str]", rows: "list[list[str]]") -> str:
    if not rows:
        return "_None._\n"
    line = "| " + " | ".join(headers) + " |\n"
    line += "|" + "|".join("---" for _ in headers) + "|\n"
    for row in rows:
        cells = [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        line += "| " + " | ".join(cells) + " |\n"
    return line


def _bullets(items: "list[str]") -> str:
    if not items:
        return "_None._\n"
    return "".join(f"- {item}\n" for item in items)


def _fenced_diagram(model: LtpModel, view_key: str) -> str:
    return "```mermaid\n" + diagram_for(view_key, model) + "```\n"


def _status(entity) -> str:
    return (
        f"{entity.basis.value} / {entity.review_status.value} / "
        f"{entity.confidence.value}"
    )


# --------------------------------------------------------------------------- #
def coverage_and_evidence(model: LtpModel, index: ModelIndex, report) -> str:
    rows = [
        [e.id, e.source, e.lines or "", e.kind or "", e.observation]
        for e in model.evidence
    ]
    out = "# Coverage and evidence\n\n"
    out += f"Evidence items: **{len(model.evidence)}**.\n\n"
    out += "## Evidence\n\n"
    out += _table(["ID", "Source", "Lines", "Kind", "Observation"], rows)
    out += "\n## Coverage gaps\n\n" + _bullets(model.coverage_gaps)
    out += "\n## Contradictions\n\n" + _bullets(model.contradictions)
    out += "\n## Open questions\n\n" + _bullets(model.open_questions)
    return out


def project_model(model: LtpModel, index: ModelIndex, report) -> str:
    project = model.project
    out = "# Project model\n\n"
    out += _table(
        ["Field", "Value"],
        [
            ["Name", project.name],
            ["Analyzed path", project.analyzed_path or ""],
            ["Analysis mode", project.analysis_mode.value],
            ["Goal", project.goal or project.provisional_goal or "(none selected)"],
            ["Current constraint", model.analysis.current_constraint or ""],
            ["Recommended next action", model.analysis.recommended_next_action or ""],
            ["Updated at", model.analysis.updated_at or ""],
        ],
    )
    out += "\n## Analysis plan\n\n"
    plan_rows = [
        [name, item.status.value, item.reason or ""]
        for name, item in model.analysis_plan.by_view().items()
    ]
    out += _table(["View", "Status", "Reason"], plan_rows)

    out += "\n## Entity inventory\n\n"
    counts: "dict[str, int]" = {}
    for entity in model.entities:
        counts[entity.kind.value] = counts.get(entity.kind.value, 0) + 1
    out += _table(
        ["Kind", "Count"],
        [[kind, str(counts[kind])] for kind in sorted(counts)],
    )
    out += "\n## Claim inventory\n\n"
    out += _table(
        ["Family", "Count"],
        [
            ["necessity_claims", str(len(model.necessity_claims))],
            ["causal_claims", str(len(model.causal_claims))],
            ["clouds", str(len(model.clouds))],
            ["obstacle_resolutions", str(len(model.obstacle_resolutions))],
            ["transitions", str(len(model.transitions))],
            ["predicted_effects", str(len(model.predicted_effects))],
        ],
    )
    return out


def goal_tree(model: LtpModel, index: ModelIndex, report) -> str:
    view = derive_views(model)["goal-tree"]
    out = "# Goal Tree\n\n"
    if view.is_empty:
        return out + "_No Goal Tree in this analysis._\n"
    rows = []
    for entity_id in view.entities:
        e = index.entities[entity_id]
        rows.append(
            [
                e.id,
                e.kind.value,
                e.statement,
                e.satisfaction.value,
                e.influence.value,
                e.satisfaction_criterion or "",
            ]
        )
    out += _table(["ID", "Kind", "Statement", "Satisfaction", "Influence", "Criterion"], rows)
    out += "\n## Necessity\n\n"
    nec_rows = [
        [
            claim.id,
            f"{claim.prerequisite} -> {claim.objective}",
            ", ".join(claim.assumption_refs) or "-",
        ]
        for claim in (index.necessity_claims[c] for c in view.necessity_claims)
    ]
    out += _table(["Claim", "Necessary for", "Assumptions"], nec_rows)
    out += "\n## Diagram\n\n" + _fenced_diagram(model, "goal-tree")
    return out


def _causal_rows(model: LtpModel, index: ModelIndex, claim_ids: "list[str]") -> "list[list[str]]":
    rows = []
    for claim_id in claim_ids:
        claim = index.causal_claims[claim_id]
        premises = f" {claim.operator.value.upper()} ".join(claim.premises)
        clr = "yes" if claim.clr is not None else "no"
        rows.append(
            [
                claim.id,
                f"{premises} => {claim.conclusion}",
                claim.operator.value,
                claim.confidence.value,
                ", ".join(claim.assumption_refs) or "-",
                clr,
            ]
        )
    return rows


def current_reality_tree(model: LtpModel, index: ModelIndex, report) -> str:
    view = derive_views(model)["current-reality"]
    out = "# Current Reality Tree\n\n"
    if view.is_empty:
        return out + "_No Current Reality Tree in this analysis._\n"
    udes = [index.entities[e] for e in view.entities if index.kind_of(e) == EntityKind.UNDESIRABLE_EFFECT]
    out += "## Undesirable effects\n\n"
    out += _table(
        ["ID", "Statement", "Basis"],
        [[u.id, u.statement, u.basis.value] for u in udes],
    )
    out += "\n## Causal claims\n\n"
    out += _table(
        ["Claim", "Logic", "Operator", "Confidence", "Assumptions", "CLR"],
        _causal_rows(model, index, sorted(view.causal_claims)),
    )
    out += "\n## Diagram\n\n" + _fenced_diagram(model, "current-reality")
    return out


def evaporating_clouds(model: LtpModel, index: ModelIndex, report) -> str:
    out = "# Evaporating Clouds\n\n"
    if not model.clouds:
        if model.conflict_analysis is not None:
            out += f"**Conflict analysis:** {model.conflict_analysis.status.value}\n\n"
            rej = [
                [c.candidate, c.reason]
                for c in model.conflict_analysis.candidates_rejected
            ]
            out += _table(["Rejected candidate", "Reason"], rej)
        else:
            out += "_No cloud, and no conflict_analysis recorded._\n"
        return out
    for cloud in model.clouds:
        out += f"## {cloud.id} ({cloud.status.value})\n\n"
        def stmt(eid: str) -> str:
            return index.entities[eid].statement if eid in index.entities else eid
        out += _table(
            ["Role", "Entity", "Statement"],
            [
                ["A objective", cloud.objective, stmt(cloud.objective)],
                ["B need", cloud.need_b, stmt(cloud.need_b)],
                ["C need", cloud.need_c, stmt(cloud.need_c)],
                ["D action", cloud.action_d, stmt(cloud.action_d)],
                ["D' action", cloud.action_d_prime, stmt(cloud.action_d_prime)],
            ],
        )
        if cloud.conflict_claim and cloud.conflict_claim in index.conflict_claims:
            out += f"\n**Conflict:** {index.conflict_claims[cloud.conflict_claim].statement}\n"
        out += f"\n**Persistence evidence:** {', '.join(cloud.persistence_evidence) or '-'}\n"
        out += f"\n**Injections:** {', '.join(cloud.injection_refs) or '-'}\n\n"
    out += "## Diagram\n\n" + _fenced_diagram(model, "evaporating-cloud")
    return out


def future_reality_tree(model: LtpModel, index: ModelIndex, report) -> str:
    view = derive_views(model)["future-reality"]
    out = "# Future Reality Tree\n\n"
    if view.is_empty:
        return out + "_No Future Reality Tree in this analysis._\n"
    injections = [index.entities[e] for e in view.entities if index.kind_of(e) == EntityKind.INJECTION]
    out += "## Injections\n\n"
    out += _table(["ID", "Statement", "Confidence"], [[i.id, i.statement, i.confidence.value] for i in injections])
    out += "\n## Causal claims\n\n"
    out += _table(
        ["Claim", "Logic", "Operator", "Confidence", "Assumptions", "CLR"],
        _causal_rows(model, index, sorted(view.causal_claims)),
    )
    if view.semantic_relations:
        out += "\n## Typed non-causal relationships\n\n"
        out += _table(
            ["Relation", "Source", "Type", "Target"],
            [
                [relation.id, relation.source, relation.relation.value, relation.target]
                for relation in (
                    index.semantic_relations[item]
                    for item in sorted(view.semantic_relations)
                )
            ],
        )
    if model.predicted_effects:
        out += "\n## Predicted effects\n\n"
        out += _table(
            ["ID", "Source", "Expectation", "Result", "Review by", "Statement"],
            [
                [
                    p.id,
                    p.source_claim,
                    p.expectation.value,
                    p.result.value,
                    p.review_by or "-",
                    p.statement,
                ]
                for p in model.predicted_effects
            ],
        )
    out += "\n## Diagram\n\n" + _fenced_diagram(model, "future-reality")
    return out


def prerequisite_tree(model: LtpModel, index: ModelIndex, report) -> str:
    out = "# Prerequisite Tree\n\n"
    view = derive_views(model)["prerequisite-tree"]
    if view.is_empty:
        return out + "_No Prerequisite Tree in this analysis._\n"
    out += "## Obstacles and intermediate objectives\n\n"
    rows = []
    for res in model.obstacle_resolutions:
        obstacle = index.entities.get(res.obstacle)
        io = index.entities.get(res.intermediate_objective)
        rows.append(
            [
                res.obstacle,
                obstacle.statement if obstacle else "",
                res.intermediate_objective,
                io.statement if io else "",
            ]
        )
    out += _table(["Obstacle", "Statement", "IO", "IO statement"], rows)
    out += "\n## Diagram\n\n" + _fenced_diagram(model, "prerequisite-tree")
    return out


def transition_tree(model: LtpModel, index: ModelIndex, report) -> str:
    out = "# Transition Tree\n\n"
    if not model.transitions:
        return out + "_No Transition Tree in this analysis._\n"
    for transition in model.transitions:
        def stmt(eid: Optional[str]) -> str:
            return index.entities[eid].statement if eid and eid in index.entities else "-"
        verification = "-"
        if transition.verification is not None:
            verification = transition.verification.kind
            if transition.verification.command:
                verification += f": `{transition.verification.command}`"
        out += f"## {transition.id}\n\n"
        out += _table(
            ["Field", "Value"],
            [
                ["Existing reality", stmt(transition.existing_reality)],
                ["Need", stmt(transition.need)],
                ["Action", stmt(transition.action)],
                ["Immediate effect", stmt(transition.immediate_effect)],
                ["Advances", transition.advances],
                ["Preconditions", ", ".join(transition.precondition_refs) or "-"],
                ["Likely scope", ", ".join(transition.likely_scope) or "-"],
                ["Verification", verification],
                ["Estimated size", transition.estimated_size.value if transition.estimated_size else "-"],
                ["Rollback", transition.rollback or "-"],
            ],
        )
        out += "\n"
    out += "## Diagram\n\n" + _fenced_diagram(model, "transition-tree")
    return out


def next_action(model: LtpModel, index: ModelIndex, report) -> str:
    out = "# Next action\n\n"
    analysis = model.analysis
    action = index.transitions.get(analysis.recommended_next_action or "")
    if action is None:
        out += "_No recommended next action selected._\n"
    else:
        act_entity = index.entities.get(action.action)
        out += f"**Recommended:** {action.id}"
        if act_entity:
            out += f" - {act_entity.statement}"
        out += "\n\n"
        out += f"- Advances: {action.advances}\n"
        if action.immediate_effect and action.immediate_effect in index.entities:
            out += f"- Immediate effect: {index.entities[action.immediate_effect].statement}\n"
    out += f"\n**Current constraint:** {analysis.current_constraint or '(none)'}\n"
    assessment = model.constraint_assessment
    if assessment is not None and assessment.focusing_step is not None:
        out += f"\n**Focusing step:** {assessment.focusing_step.current.value}\n"
        if assessment.exploit_direction:
            out += f"- Exploit: {assessment.exploit_direction}\n"
        if assessment.subordinate_direction:
            out += f"- Subordinate: {assessment.subordinate_direction}\n"
        if assessment.elevation_direction:
            out += f"- Elevate: {assessment.elevation_direction}\n"
    return out


def assumptions_and_questions(model: LtpModel, index: ModelIndex, report) -> str:
    out = "# Assumptions and questions\n\n"
    assumptions = [e for e in model.entities if e.kind == EntityKind.ASSUMPTION]
    out += "## Assumptions\n\n"
    out += _table(
        ["ID", "Statement", "Basis / Review / Confidence", "Evidence"],
        [
            [a.id, a.statement, _status(a), ", ".join(a.evidence_refs) or "-"]
            for a in assumptions
        ],
    )
    out += "\n## Open questions\n\n" + _bullets(model.open_questions)
    out += "\n## Model health\n\n"
    if report is not None:
        counts = report.counts
        out += (
            f"Errors: **{counts['error']}**, warnings: **{counts['warning']}**, "
            f"info: **{counts['info']}**. "
            f"Publishable: **{'yes' if report.is_publishable else 'no'}**.\n\n"
        )
        top = [d for d in report.diagnostics if d.severity.value == "error"][:20]
        out += _table(
            ["Code", "Target", "Message"],
            [[d.code, d.target or "", d.message] for d in top],
        )
    else:
        out += "_Run `ltp validate` for model health._\n"
    return out


DOCUMENTS = [
    ("00-coverage-and-evidence.md", coverage_and_evidence),
    ("01-project-model.md", project_model),
    ("02-goal-tree.md", goal_tree),
    ("03-current-reality-tree.md", current_reality_tree),
    ("04-evaporating-clouds.md", evaporating_clouds),
    ("05-future-reality-tree.md", future_reality_tree),
    ("06-prerequisite-tree.md", prerequisite_tree),
    ("07-transition-tree.md", transition_tree),
    ("08-next-action.md", next_action),
    ("09-assumptions-and-questions.md", assumptions_and_questions),
]


def render_documents(model: LtpModel, report=None) -> "dict[str, str]":
    index = ModelIndex(model)
    return {name: fn(model, index, report) for name, fn in DOCUMENTS}
