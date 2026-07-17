"""Deterministic Mermaid diagrams, one per non-empty view.

The point the old dashboard missed: a compound sufficiency claim
(``operator: all``) is drawn as a single AND gate, so the diagram asserts that
the premises *together* deliver the effect -- not as two arrows that each look
independently sufficient. Necessity is dashed; sufficiency is solid; the Cloud
gets its fixed A / B,C / D,D' layout.
"""

from __future__ import annotations

from ..enums import EntityKind, Operator
from ..models import LtpModel, ModelIndex
from .views import derive_views

_GATE_LABEL = {
    Operator.ALL: "AND",
    Operator.ANY: "OR",
    Operator.EXCLUSIVE_ANY: "XOR",
    Operator.MAGNITUDINAL: "MAG",
}

_MAX_LABEL = 64


def _nid(record_id: str) -> str:
    """Mermaid node ids may not contain '-' or '.'."""
    return record_id.replace("-", "_").replace(".", "_")


def _label(record_id: str, statement: str) -> str:
    text = " ".join(statement.split())
    if len(text) > _MAX_LABEL:
        text = text[: _MAX_LABEL - 1].rstrip() + "…"
    text = text.replace('"', "'").replace("[", "(").replace("]", ")")
    return f"{record_id}: {text}"


class _Diagram:
    def __init__(self, direction: str) -> None:
        self.direction = direction
        self._nodes: "dict[str, str]" = {}
        self._edges: "list[str]" = []

    def node(self, record_id: str, statement: str, shape: str = "rect") -> str:
        nid = _nid(record_id)
        if nid not in self._nodes:
            label = _label(record_id, statement)
            if shape == "gate":
                self._nodes[nid] = f'{nid}{{{{"{statement}"}}}}'
            elif shape == "goal":
                self._nodes[nid] = f'{nid}(["{label}"])'
            elif shape == "round":
                self._nodes[nid] = f'{nid}("{label}")'
            else:
                self._nodes[nid] = f'{nid}["{label}"]'
        return nid

    def edge(self, source: str, target: str, label: str = "", dashed: bool = False) -> None:
        connector = "-.->" if dashed else "-->"
        if label:
            connector = (
                f"-. {label} .->" if dashed else f"-->|{label}|"
            )
        self._edges.append(f"{_nid(source)} {connector} {_nid(target)}")

    def render(self) -> str:
        lines = [f"flowchart {self.direction}"]
        for nid in sorted(self._nodes):
            lines.append(f"    {self._nodes[nid]}")
        for edge in self._edges:
            lines.append(f"    {edge}")
        return "\n".join(lines) + "\n"


def _goal_tree(model: LtpModel, index: ModelIndex, view) -> str:
    diagram = _Diagram("BT")
    for entity_id in view.entities:
        entity = index.entities[entity_id]
        shape = "goal" if entity.kind == EntityKind.GOAL else "rect"
        diagram.node(entity_id, entity.statement, shape)
    for claim_id in sorted(view.necessity_claims):
        claim = index.necessity_claims[claim_id]
        diagram.edge(claim.prerequisite, claim.objective, "necessary for", dashed=True)
    return diagram.render()


def _causal(model: LtpModel, index: ModelIndex, view, direction: str = "BT") -> str:
    diagram = _Diagram(direction)
    for entity_id in view.entities:
        entity = index.entities[entity_id]
        shape = "goal" if entity.kind == EntityKind.GOAL else "rect"
        diagram.node(entity_id, entity.statement, shape)
    for claim_id in sorted(view.causal_claims):
        claim = index.causal_claims[claim_id]
        if len(claim.premises) <= 1 and claim.operator == Operator.SINGLE:
            for premise in claim.premises:
                diagram.edge(premise, claim.conclusion, "causes")
        else:
            gate_label = _GATE_LABEL.get(claim.operator, "AND")
            gate_id = f"{claim.id}#gate"
            diagram.node(gate_id, f"{gate_label} ({claim.id})", "gate")
            for premise in sorted(claim.premises):
                diagram.edge(premise, gate_id)
            diagram.edge(gate_id, claim.conclusion, "causes")
    for relation_id in sorted(view.semantic_relations):
        relation = index.semantic_relations[relation_id]
        diagram.edge(
            relation.source,
            relation.target,
            relation.relation.value.replace("_", " "),
            dashed=True,
        )
    return diagram.render()


def _cloud(model: LtpModel, index: ModelIndex, view) -> str:
    diagram = _Diagram("BT")
    for cloud in model.clouds:
        diagram.node(cloud.objective, index.entities[cloud.objective].statement
                     if cloud.objective in index.entities else cloud.objective, "round")
        for role in (cloud.need_b, cloud.need_c, cloud.action_d, cloud.action_d_prime):
            stmt = index.entities[role].statement if role in index.entities else role
            diagram.node(role, stmt, "round")
        diagram.edge(cloud.need_b, cloud.objective, "requires", dashed=True)
        diagram.edge(cloud.need_c, cloud.objective, "requires", dashed=True)
        diagram.edge(cloud.action_d, cloud.need_b, "requires", dashed=True)
        diagram.edge(cloud.action_d_prime, cloud.need_c, "requires", dashed=True)
        diagram.edge(cloud.action_d, cloud.action_d_prime, "conflict", dashed=True)
    return diagram.render()


def _prerequisite(model: LtpModel, index: ModelIndex, view) -> str:
    diagram = _Diagram("BT")
    for entity_id in view.entities:
        entity = index.entities[entity_id]
        shape = "round" if entity.kind == EntityKind.OBSTACLE else "rect"
        diagram.node(entity_id, entity.statement, shape)
    for res_id in sorted(view.obstacle_resolutions):
        res = index.obstacle_resolutions[res_id]
        diagram.edge(res.obstacle, res.intermediate_objective, "overcome by", dashed=True)
    for claim_id in sorted(view.necessity_claims):
        claim = index.necessity_claims[claim_id]
        diagram.edge(claim.prerequisite, claim.objective, "enables", dashed=True)
    return diagram.render()


def _transition(model: LtpModel, index: ModelIndex, view) -> str:
    diagram = _Diagram("TD")
    for transition in model.transitions:
        chain = [
            (transition.existing_reality, "existing reality"),
            (transition.need, "need"),
            (transition.action, "action"),
            (transition.immediate_effect, "immediate effect"),
            (transition.advances, "advances"),
        ]
        present = [(eid, role) for eid, role in chain if eid and eid in index.entities]
        for eid, _role in present:
            diagram.node(eid, index.entities[eid].statement)
        for (source, _), (target, role) in zip(present, present[1:]):
            diagram.edge(source, target, role)
    return diagram.render()


_RENDERERS = {
    "goal-tree": _goal_tree,
    "current-reality": lambda m, i, v: _causal(m, i, v, "BT"),
    "evaporating-cloud": _cloud,
    "future-reality": lambda m, i, v: _causal(m, i, v, "BT"),
    "prerequisite-tree": _prerequisite,
    "transition-tree": _transition,
}


def diagram_for(view_key: str, model: LtpModel) -> str:
    index = ModelIndex(model)
    view = derive_views(model)[view_key]
    return _RENDERERS[view_key](model, index, view)


def render_diagrams(model: LtpModel) -> "dict[str, str]":
    """view_key -> mermaid source, for every non-empty view."""
    views = derive_views(model)
    out: "dict[str, str]" = {}
    for key, view in views.items():
        if not view.is_empty:
            out[key] = diagram_for(key, model)
    return out
