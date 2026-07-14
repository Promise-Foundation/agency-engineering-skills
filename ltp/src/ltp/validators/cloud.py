"""Evaporating Cloud validation (EC-*).

A Cloud is a first-class structure with five distinct roles (A, B, C, D, D'),
four necessity arrows, and an explicit D-D' conflict -- never one text node. A
Cloud is only built when a persistent conflict is warranted; the absence of one
is recorded as ``conflict_analysis`` rather than forced by a checklist.
"""

from __future__ import annotations

from ..diagnostics import Diagnostic, diagnostic
from ..enums import CloudStatus
from ..models import LtpModel, ModelIndex
from . import graph


def validate(model: LtpModel, index: ModelIndex) -> "list[Diagnostic]":
    out: "list[Diagnostic]" = []
    for cloud in model.clouds:
        roles = [
            cloud.objective,
            cloud.need_b,
            cloud.need_c,
            cloud.action_d,
            cloud.action_d_prime,
        ]
        # EC-002: the five roles must be five distinct entities.
        if len(set(roles)) < 5:
            out.append(
                diagnostic(
                    "EC-002",
                    f"cloud {cloud.id} does not have five distinct A/B/C/D/D' "
                    "entities; it has collapsed roles",
                    target=cloud.id,
                )
            )

        # EC-003: the four necessity claims must connect the right pairs.
        expected = {
            "a_requires_b": (cloud.need_b, cloud.objective),
            "a_requires_c": (cloud.need_c, cloud.objective),
            "b_requires_d": (cloud.action_d, cloud.need_b),
            "c_requires_d_prime": (cloud.action_d_prime, cloud.need_c),
        }
        wiring = {
            "a_requires_b": cloud.necessity_claims.a_requires_b,
            "a_requires_c": cloud.necessity_claims.a_requires_c,
            "b_requires_d": cloud.necessity_claims.b_requires_d,
            "c_requires_d_prime": cloud.necessity_claims.c_requires_d_prime,
        }
        for label, claim_id in wiring.items():
            claim = index.necessity_claims.get(claim_id)
            if claim is None:
                continue  # dangling ref already reported by structure
            want_prereq, want_obj = expected[label]
            if claim.prerequisite != want_prereq or claim.objective != want_obj:
                out.append(
                    diagnostic(
                        "EC-003",
                        f"cloud {cloud.id} {label} ({claim_id}) connects "
                        f"{claim.prerequisite}->{claim.objective}; expected "
                        f"{want_prereq}->{want_obj}",
                        target=cloud.id,
                    )
                )
            if not claim.assumption_refs:
                out.append(
                    diagnostic(
                        "EC-005",
                        f"cloud {cloud.id} necessity claim {claim_id} ({label}) has "
                        "no assumption; every arrow of a cloud rests on one",
                        target=claim_id,
                    )
                )

        # EC-004: the D-D' incompatibility must be explicit.
        if not cloud.conflict_claim:
            out.append(
                diagnostic(
                    "EC-004",
                    f"cloud {cloud.id} has no conflict_claim stating why D and D' "
                    "are incompatible",
                    target=cloud.id,
                )
            )

        # EC-006: both needs must be shown legitimate.
        for role, ref in (("B", cloud.need_b), ("C", cloud.need_c)):
            need = index.entities.get(ref)
            if need is not None and not need.evidence_refs:
                out.append(
                    diagnostic(
                        "EC-006",
                        f"cloud {cloud.id} need {role} ({ref}) has no evidence that "
                        "it is a legitimate need",
                        target=ref,
                    )
                )

        # EC-007: an injection must target one of the cloud's assumptions.
        if not cloud.injection_refs:
            out.append(
                diagnostic(
                    "EC-007",
                    f"cloud {cloud.id} names no injection; a cloud is resolved by "
                    "breaking an assumption, so it needs at least one injection_ref",
                    target=cloud.id,
                )
            )

        # EC-008: a validated conflict must prove it is persistent.
        if (
            cloud.status == CloudStatus.VALIDATED_PERSISTENT_CONFLICT
            and not cloud.persistence_evidence
        ):
            out.append(
                diagnostic(
                    "EC-008",
                    f"cloud {cloud.id} is marked a validated persistent conflict but "
                    "has no persistence_evidence",
                    target=cloud.id,
                )
            )

        # EC-009: reject a conflict that rests only on generic resource finitude.
        conflict = index.conflict_claims.get(cloud.conflict_claim or "")
        texts = [conflict.statement] if conflict else []
        for ref in (cloud.action_d, cloud.action_d_prime):
            action = index.entities.get(ref)
            if action:
                texts.append(action.statement)
        if any(graph.looks_resource_finitude(text) for text in texts):
            out.append(
                diagnostic(
                    "EC-009",
                    f"cloud {cloud.id} rests on generic resource finitude (finite "
                    "time/resources); name the specific, persistent contention",
                    target=cloud.id,
                )
            )

    return out
