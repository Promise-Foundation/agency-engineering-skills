"""Shared graph traversals and phrasing heuristics for the validators.

Two directed relations run through an LTP model:

* **causal** -- ``premise -> conclusion`` for every premise of a sufficiency
  claim (Current/Future Reality Trees).
* **necessity** -- ``prerequisite -> objective`` (Goal Tree, Prerequisite Tree
  ordering, IO -> injection readiness).

The *combined* graph overlays both, which is what a cross-tree "does this action
actually reach the goal?" question needs.
"""

from __future__ import annotations

from typing import Optional

from ..models import LtpModel, ModelIndex


def causal_in(model: LtpModel) -> "dict[str, list[str]]":
    """conclusion entity id -> claim ids that conclude it."""
    result: "dict[str, list[str]]" = {}
    for claim in model.causal_claims:
        result.setdefault(claim.conclusion, []).append(claim.id)
    return result


def causal_premise_of(model: LtpModel) -> "dict[str, list[str]]":
    """entity id -> claim ids in which it is a premise."""
    result: "dict[str, list[str]]" = {}
    for claim in model.causal_claims:
        for premise in claim.premises:
            result.setdefault(premise, []).append(claim.id)
    return result


def causal_adjacency(model: LtpModel) -> "dict[str, set[str]]":
    """premise entity -> set of conclusion entities."""
    adjacency: "dict[str, set[str]]" = {}
    for claim in model.causal_claims:
        for premise in claim.premises:
            adjacency.setdefault(premise, set()).add(claim.conclusion)
    return adjacency


def necessity_adjacency(model: LtpModel) -> "dict[str, set[str]]":
    """prerequisite entity -> set of objective entities."""
    adjacency: "dict[str, set[str]]" = {}
    for claim in model.necessity_claims:
        adjacency.setdefault(claim.prerequisite, set()).add(claim.objective)
    return adjacency


def combined_adjacency(model: LtpModel) -> "dict[str, set[str]]":
    adjacency = causal_adjacency(model)
    for source, targets in necessity_adjacency(model).items():
        adjacency.setdefault(source, set()).update(targets)
    return adjacency


def reachable(adjacency: "dict[str, set[str]]", start: str) -> "set[str]":
    """Every node reachable from ``start`` (excluding ``start`` itself)."""
    seen: "set[str]" = set()
    stack = list(adjacency.get(start, ()))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency.get(node, ()))
    return seen


def reaches(adjacency: "dict[str, set[str]]", start: str, target: str) -> bool:
    return target in reachable(adjacency, start)


def find_cycle(adjacency: "dict[str, set[str]]") -> "Optional[list[str]]":
    """Return one directed cycle as a node list, or ``None``. Deterministic:
    nodes and neighbours are visited in sorted order."""
    WHITE, GREY, BLACK = 0, 1, 2
    color: "dict[str, int]" = {}
    stack: "list[str]" = []

    def visit(node: str) -> "Optional[list[str]]":
        color[node] = GREY
        stack.append(node)
        for neighbour in sorted(adjacency.get(node, ())):
            state = color.get(neighbour, WHITE)
            if state == WHITE:
                found = visit(neighbour)
                if found:
                    return found
            elif state == GREY:
                index = stack.index(neighbour)
                return stack[index:] + [neighbour]
        stack.pop()
        color[node] = BLACK
        return None

    for start in sorted({node for node in adjacency}):
        if color.get(start, WHITE) == WHITE:
            found = visit(start)
            if found:
                return found
    return None


# --------------------------------------------------------------------------- #
# Phrasing heuristics
# --------------------------------------------------------------------------- #
_MISSING_FEATURE = (
    "we do not have",
    "we don't have",
    "we have not",
    "we haven't",
    "is missing",
    "are missing",
    "not implemented",
    "isn't implemented",
    "is not implemented",
    "lack of",
    "lacks ",
    "no support for",
    "does not exist",
    "absence of",
    "has not been implemented",
    "have not implemented",
    "there is no ",
    "there are no ",
)
_IMPERATIVE_VERBS = (
    "add ",
    "implement ",
    "build ",
    "refactor ",
    "create ",
    "write ",
    "fix ",
    "migrate ",
    "remove ",
    "delete ",
    "update ",
    "introduce ",
    "set up ",
    "configure ",
    "install ",
    "enable ",
    "wire ",
    "rename ",
    "extract ",
)
_RESOURCE_FINITUDE = (
    "finite time",
    "limited time",
    "not enough time",
    "limited resources",
    "finite resources",
    "limited budget",
    "too few",
    "understaffed",
    "limited bandwidth",
    "no bandwidth",
    "can only do one thing",
    "cannot do everything",
)


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def looks_like_missing_feature(text: str) -> bool:
    normalized = _normalize(text)
    return any(pattern in normalized for pattern in _MISSING_FEATURE)


def looks_imperative(text: str) -> bool:
    normalized = _normalize(text)
    return any(normalized.startswith(verb) for verb in _IMPERATIVE_VERBS)


def looks_resource_finitude(text: str) -> bool:
    normalized = _normalize(text)
    return any(pattern in normalized for pattern in _RESOURCE_FINITUDE)


def looks_multi_change(text: str, likely_scope: "Optional[list[str]]" = None) -> bool:
    """Heuristic for a transition that bundles several independent changes:
    two imperative verbs joined by 'and'/'then', or scope spanning unrelated
    top-level directories."""
    normalized = _normalize(text)
    verb_hits = sum(1 for verb in _IMPERATIVE_VERBS if verb in normalized)
    joined = (" and " in normalized or ", then " in normalized or "; " in normalized)
    if verb_hits >= 2 and joined:
        return True
    if likely_scope and len(likely_scope) >= 2:
        tops = {path.strip("/").split("/", 1)[0] for path in likely_scope if path}
        if len(tops) >= 3:
            return True
    return False


def selected_goal(model: LtpModel, index: ModelIndex) -> "Optional[str]":
    """The one goal an analysis has committed to (``goal`` overrides
    ``provisional_goal``)."""
    for candidate in (model.project.goal, model.project.provisional_goal):
        if candidate and candidate in index.entities:
            return candidate
    return None
