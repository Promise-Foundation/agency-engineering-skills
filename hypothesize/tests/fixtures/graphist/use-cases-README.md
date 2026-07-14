# Graphist use-case registry

This document is the authoritative index of Graphist use cases. It tracks what is specified, what is implemented, which [README hypotheses](../README.md#hypothesis-portfolio) each use case could test, and what evidence would be needed next.

Last reviewed: **2026-07-14**

## Status vocabulary

The three status dimensions are deliberately separate.

| Dimension | Values | Meaning |
|---|---|---|
| Specification | Outline / Specified | Whether the use-case document contains the full product, JTBD, boundary, Gherkin, hypothesis, and demonstration structure |
| Implementation | Not started / Adjacent mechanisms / Bounded mechanism / Product slice | How much executable capability exists for this use case, not for Graphist in general |
| Validation | Not run / Internal mechanism / Comparative pilot / External replication | Strength of use-case-specific evidence |

`Adjacent mechanisms` means reusable Graphist capabilities exist but no end-to-end use-case implementation has been demonstrated. `Bounded mechanism` means a narrow executable path exists but has not established external usefulness. No use case currently has an external replication.

## Portfolio

<!-- BEGIN GENERATED: use-case-status -->
| ID | Use case | Priority | Specification | Implementation | Validation | Hypotheses |
|---|---|---|---|---|---|---|
| **UC-01** | [Verified AI Transformations](./verified_ai_transformations.md) | tier_1 | specified | bounded_mechanism | internal_mechanism | `GH-SAF`, `GH-VER`, `GH-AUD`, `GH-CHL`, `GH-GOV`, `GH-DBG`, `GH-INT`, `GH-EFF` |
| **UC-02** | [Structured Agent Runtime / Harness](./agent_harness.md) | tier_2 | specified | adjacent_mechanisms | not_run | `GH-GOV`, `GH-AUD`, `GH-DBG`, `GH-SAF`, `GH-INT`, `GH-HMI`, `GH-CHL`, `GH-EFF` |
| **UC-03** | [Knowledge and Data Change Assurance](./knowledge_data_assurance.md) | domain_extension | specified | adjacent_mechanisms | not_run | `GH-SAF`, `GH-VER`, `GH-AUD`, `GH-DBG`, `GH-EXP`, `GH-GOV`, `GH-INT`, `GH-EFF` |
| **UC-04** | [Proof and Program Synthesis](./proof_and_program_synthesis.md) | research | specified | adjacent_mechanisms | not_run | `GH-VER`, `GH-LRN`, `GH-INT`, `GH-CHL`, `GH-EXP`, `GH-EFF` |
| **UC-05** | [Scientific Hypothesis Management](./scientific_hypothesis_management.md) | research | specified | adjacent_mechanisms | not_run | `GH-EPI`, `GH-AUD`, `GH-HMI`, `GH-CHL`, `GH-GOV`, `GH-EXP`, `GH-INT`, `GH-EFF` |
| **UC-06** | [Graphist-Grapheus Inquiry](./graphist_grapheus_inquiry.md) | tier_3 | specified | bounded_mechanism | internal_mechanism | `GH-HMI`, `GH-CHL`, `GH-EPI`, `GH-EXP`, `GH-GOV`, `GH-AUD`, `GH-LRN`, `GH-INT`, `GH-EFF` |
| **UC-07** | [Auditable Decision Dossiers](./auditable_decision_dossiers.md) | tier_1 | specified | not_started | not_run | `GH-AUD`, `GH-EXP`, `GH-GOV`, `GH-HMI`, `GH-EPI`, `GH-CHL`, `GH-EFF` |
| **UC-08** | [AI Incident Forensics and Rollback](./ai_incident_forensics_and_rollback.md) | tier_1 | specified | adjacent_mechanisms | not_run | `GH-DBG`, `GH-AUD`, `GH-SAF`, `GH-VER`, `GH-GOV`, `GH-EXP`, `GH-EFF` |
| **UC-09** | [Human Review and Dispute Resolution](./human_review_and_dispute_resolution.md) | explain | specified | adjacent_mechanisms | not_run | `GH-EXP`, `GH-CHL`, `GH-HMI`, `GH-GOV`, `GH-AUD`, `GH-EPI`, `GH-EFF` |
| **UC-10** | [Safety and Assurance Cases](./safety_and_assurance_cases.md) | tier_2 | specified | adjacent_mechanisms | not_run | `GH-VER`, `GH-AUD`, `GH-GOV`, `GH-CHL`, `GH-EXP`, `GH-EPI`, `GH-EFF` |
| **UC-11** | [Model-Agnostic Verification Gateway](./model_agnostic_verification_gateway.md) | tier_2 | specified | bounded_mechanism | internal_mechanism | `GH-INT`, `GH-VER`, `GH-GOV`, `GH-SAF`, `GH-AUD`, `GH-EFF` |
| **UC-12** | [Compliance-by-Construction Workflows](./compliance_by_construction_workflows.md) | tier_2 | specified | adjacent_mechanisms | not_run | `GH-GOV`, `GH-SAF`, `GH-AUD`, `GH-VER`, `GH-EPI`, `GH-INT`, `GH-EFF` |
| **UC-13** | [Explainable Entity-Resolution Review](./explainable_entity_resolution_review.md) | domain_experiment | specified | adjacent_mechanisms | not_run | `GH-EXP`, `GH-CHL`, `GH-HMI`, `GH-AUD`, `GH-SAF`, `GH-EPI`, `GH-EFF` |
| **UC-14** | [Auditable Training and Evaluation Traces](./auditable_training_and_evaluation.md) | research_infrastructure | specified | bounded_mechanism | internal_mechanism | `GH-AUD`, `GH-EPI`, `GH-VER`, `GH-GOV`, `GH-INT`, `GH-LRN`, `GH-EFF` |
<!-- END GENERATED: use-case-status -->

## Hypothesis coverage

This is a routing map, not an evidence summary. `Primary` means the use case can directly test the hypothesis; `secondary` means it supplies a useful outcome or constraint but should not carry the main conclusion.

| Hypothesis | Primary use cases | Secondary or enabling use cases |
|---|---|---|
| **GH-LRN** | UC-04 | UC-06, UC-14 |
| **GH-VER** | UC-01, UC-03, UC-04, UC-10, UC-11, UC-14 | UC-08, UC-12 |
| **GH-AUD** | UC-01, UC-02, UC-03, UC-05, UC-07, UC-08, UC-10, UC-12, UC-14 | UC-06, UC-09, UC-11, UC-13 |
| **GH-EXP** | UC-07, UC-09, UC-13 | UC-03, UC-04, UC-06, UC-08, UC-10 |
| **GH-CHL** | UC-06, UC-09, UC-13 | UC-01, UC-02, UC-04, UC-05, UC-07, UC-10 |
| **GH-GOV** | UC-01, UC-02, UC-07, UC-10, UC-11, UC-12 | UC-03, UC-05, UC-06, UC-08, UC-09, UC-14 |
| **GH-INT** | UC-04, UC-11 | UC-01, UC-02, UC-03, UC-05, UC-06, UC-12, UC-14 |
| **GH-HMI** | UC-05, UC-06, UC-09, UC-13 | UC-02, UC-07 |
| **GH-DBG** | UC-02, UC-08 | UC-01, UC-03 |
| **GH-SAF** | UC-01, UC-02, UC-03, UC-08, UC-12 | UC-11, UC-13 |
| **GH-EPI** | UC-05, UC-06, UC-14 | UC-07, UC-09, UC-10, UC-12, UC-13 |
| **GH-EFF** | — | Every use case; it is a required cost constraint, not a benefit inferred from another outcome |

## Recommended validation queue

The queue prioritizes experiments that can distinguish a Graphist benefit without assuming a reasoning-performance advantage.

| Order | Validation study | Use cases | Main measures | Advancement criterion |
|---|---|---|---|---|
| 1 | **Verified change-control pilot** | UC-01, with UC-11 as the delivery boundary | Unsafe acceptance, false rejection, repair, certificate replay, latency, cost | Fewer unsafe accepted changes than matched application checks, replay succeeds independently, and useful completion remains acceptable |
| 2 | **Decision review study** | UC-07 and UC-09 | Basis comprehension, missing-evidence and authority detection, valid challenges, time, calibration | Better review accuracy or calibration than strong matched dossiers/explanations without unacceptable workload |
| 3 | **Incident forensic exercise** | UC-08 | First-divergence accuracy, blast radius, recovery quality, time, confidence | Faster or more accurate reconstruction and recovery than ordinary logs under matched information |
| 4 | **Entity-resolution explanation study** | UC-13, grounded in UC-03 | False-merge acceptance, conflict/impact comprehension, deferral, time, privacy | Better adjudication than score and feature/rule explanations after controlling for information and explanation size |
| 5 | **Independent gateway conformance** | UC-11 | Semantic coverage, adapter/trusted code, consistent rejection, replay, swap cost | At least two independent proposers share the boundary without proposer-specific trusted acceptance logic |
| 6 | **T3 schema-transfer experiment** | UC-04 and UC-06 research mechanisms | Held-out structural transfer, valid reuse, false application, search/data/time | S8 beats S7 and strong S4/S6 baselines under matched information and resource governance |

## Metadata and evidence rules

Every use-case status update should record:

- owner and intended user population;
- implementation slice and public application boundary;
- protocol or preregistration identifier;
- comparator and information available to each arm;
- dataset or case manifest and provenance;
- primary outcome, failure taxonomy, margin, and decision rule;
- resource budget, latency, storage, and human-effort measures;
- immutable raw artifact and report locations;
- result status: supported, falsified, or inconclusive;
- known scope limits, replications, and unresolved challenges.

A mechanism demonstration may advance implementation status. Only a controlled result may advance validation status. A document, feature suite, or successful self-authored fixture must never be counted as external evidence.

## Maintenance policy

- Add a stable `UC-##` identifier before implementation begins.
- Keep each use case's README hypothesis alignment synchronized with this registry.
- Do not remove falsified or inactive use cases; mark their status and retain their evidence.
- Add new README hypothesis IDs only when the claim is materially independent of the current portfolio.
- Link every `Comparative pilot` or `External replication` status to its protocol, raw records, and regenerated report.
