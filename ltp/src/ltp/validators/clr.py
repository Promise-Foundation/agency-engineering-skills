"""CLR review and predicted-effect validation (CLR-*, CRT-006, PRED-*).

The engine never decides whether a cause is real. It verifies that the
Categories of Legitimate Reservation were applied and that their conclusions are
represented honestly: a claim with an open check is a *candidate*; a claim with
a failed required check cannot be called scrutinized; a root cause with no
predicted effect is an untested explanation.
"""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..enums import CLRState, EntityKind, Expectation, PredictedResult
from ..models import LtpModel, ModelIndex

# Conclusions important enough that an un-reviewed claim is worth flagging.
_LOAD_BEARING = {
    EntityKind.UNDESIRABLE_EFFECT,
    EntityKind.DESIRABLE_EFFECT,
    EntityKind.NECESSARY_CONDITION,
    EntityKind.CRITICAL_SUCCESS_FACTOR,
    EntityKind.GOAL,
}


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []

    for claim in model.causal_claims:
        load_bearing = index.kind_of(claim.conclusion) in _LOAD_BEARING
        if claim.clr is None:
            if load_bearing:
                out.append(
                    diagnostic(
                        "CLR-001",
                        f"claim {claim.id} concludes a load-bearing "
                        f"{index.kind_of(claim.conclusion).value} but has no CLR "  # type: ignore[union-attr]
                        "review (candidate claim)",
                        target=claim.id,
                    )
                )
            continue

        clr = claim.clr
        if clr.causality_existence.result == CLRState.FAIL:
            out.append(
                diagnostic(
                    "CLR-003",
                    f"claim {claim.id}: CLR concluded no causality exists "
                    f"({clr.causality_existence.reservation or 'no reservation given'})",
                    target=claim.id,
                )
            )
        if clr.cause_effect_reversal.result == CLRState.FAIL:
            out.append(
                diagnostic(
                    "CLR-006",
                    f"claim {claim.id}: CLR concluded the cause and effect are "
                    "reversed",
                    target=claim.id,
                    hint="swap premises and conclusion, or restate the mechanism",
                )
            )
        if clr.tautology.result == CLRState.FAIL:
            out.append(
                diagnostic(
                    "CLR-007",
                    f"claim {claim.id}: CLR concluded the claim is a tautology "
                    "(the cause restates the effect)",
                    target=claim.id,
                )
            )
        if CLRState.FAIL in (
            clr.cause_insufficiency.result,
            clr.additional_cause.result,
        ):
            proposed = (
                clr.cause_insufficiency.proposed_additional_premise
                or clr.additional_cause.proposed_additional_premise
            )
            hint = (
                f"consider adding premise {proposed}" if proposed else
                "identify the additional cause that must also be present"
            )
            out.append(
                diagnostic(
                    "CRT-006",
                    f"claim {claim.id} may require an additional premise (CLR "
                    "cause-insufficiency / additional-cause)",
                    target=claim.id,
                    hint=hint,
                )
            )
        existence = clr.entity_existence
        if existence.result == CLRState.FAIL or (
            existence.result == CLRState.OPEN and not existence.evidence_refs
        ):
            out.append(
                diagnostic(
                    "CLR-009",
                    f"claim {claim.id}: existence of a referenced entity is "
                    f"unverified ({existence.result.value})",
                    target=claim.id,
                )
            )
        open_checks = sorted(
            name for name, check in clr.checks().items() if check.result == CLRState.OPEN
        )
        if open_checks:
            out.append(
                diagnostic(
                    "CLR-008",
                    f"claim {claim.id} has open CLR checks ({', '.join(open_checks)}); "
                    "it remains a candidate, not scrutinized",
                    target=claim.id,
                )
            )

    # -- predicted effects ---------------------------------------------- #
    preds_by_root: "dict[str, list[str]]" = {}
    for pred in model.predicted_effects:
        claim = index.causal_claims.get(pred.source_claim)
        if claim is None:
            continue
        for premise in claim.premises:
            if index.kind_of(premise) == EntityKind.ROOT_CAUSE:
                preds_by_root.setdefault(premise, []).append(pred.id)
        if pred.expectation == Expectation.SHOULD_EXIST and pred.result == PredictedResult.ABSENT:
            out.append(
                diagnostic(
                    "PRED-002",
                    f"predicted effect {pred.id} should exist but was not observed; "
                    "this weakens the explanation it tests",
                    target=pred.id,
                )
            )

    for root in index.of_kind(EntityKind.ROOT_CAUSE):
        if not preds_by_root.get(root.id):
            out.append(
                diagnostic(
                    "PRED-001",
                    f"root-cause candidate {root.id} has no predicted effect; an "
                    "untested root cause is a guess",
                    target=root.id,
                    hint="add a predicted_effect on a claim from this root cause, or "
                    "waive it with a reason",
                )
            )

    return out
