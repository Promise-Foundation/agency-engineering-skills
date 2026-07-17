/** Maps LTP's generated `dashboard-model.json` into agency resources + relations.
 * The one cross-skill link -- a causal claim `VERIFIED_BY` a hypothesis -- is
 * emitted here from the data the LTP engine already produces. */

import type { AgencyRelation, AgencyResource } from "@agency/skill-sdk";
import type { ManifestMapping } from "@agency/core";

export interface LtpDiagnostic {
  code: string;
  severity: "error" | "warning" | "info";
  message: string;
  target?: string | null;
}

export interface LtpEntity {
  id: string;
  kind: string;
  statement: string;
  basis?: string;
  review_status?: string;
  confidence?: string;
  satisfaction?: string;
  influence?: string;
  evidence_refs?: string[];
  [key: string]: unknown;
}

export interface LtpClaim {
  id: string;
  premises?: string[];
  operator?: string;
  conclusion?: string;
  confidence?: string;
  logic_status?: string;
  verification?: { hypothesis_ref: string; role?: string; empirical_status?: string };
  clr?: Record<string, { result: string; reservation?: string }>;
  [key: string]: unknown;
}

export interface LtpSemanticRelation {
  id: string;
  source: string;
  target: string;
  relation: string;
  reasoning?: string | null;
  evidence_refs?: string[];
}

export interface LtpPrediction {
  id: string;
  source_claim: string;
  statement: string;
  indicator?: string | null;
  baseline?: number | null;
  expected_change_percent?: number | null;
  tolerance_percent?: number;
  expected_by?: string | null;
  review_by?: string | null;
  owner?: string | null;
  implementation_status?: string;
  implemented_at?: string | null;
  implementation_fidelity?: number | null;
  minimum_fidelity?: number | null;
  waived?: boolean;
  waiver_reason?: string | null;
}

export interface LtpObservation {
  id: string;
  prediction: string;
  observed_at: string;
  result?: string;
  value?: number | null;
  change_percent?: number | null;
  source?: string | null;
}

export interface LtpPredictionEvaluation {
  id: string;
  prediction: string;
  as_of: string;
  result: "supported" | "contradicted" | "inconclusive" | "not_yet_due";
  observation?: string | null;
  explanation?: string | null;
}

export interface LtpLearningObligation {
  id: string;
  kind: string;
  target: string;
  due_at: string;
  next_action: string;
  owner?: string | null;
  blocking?: boolean;
}

export interface LtpLearningEvent {
  id: string;
  occurred_at: string;
  kind: string;
  subject: string;
  summary: string;
  source: string;
  actor?: string;
  reason?: string;
  previous?: unknown;
  current?: unknown;
  metadata?: Record<string, unknown>;
}

export interface LtpView {
  title: string;
  empty: boolean;
  node_ids: string[];
  edges: { source: string; target: string; relation: string; claim?: string }[];
}

export interface LtpGate {
  id: string;
  operator: string;
  claim: string;
  logic_status?: string;
}

export interface LtpModel {
  project: { name: string; goal?: string; analysis_mode?: string };
  analysis?: Record<string, unknown>;
  entities: LtpEntity[];
  causal_claims: LtpClaim[];
  semantic_relations?: LtpSemanticRelation[];
  predicted_effects?: LtpPrediction[];
  observations?: LtpObservation[];
  prediction_evaluations?: LtpPredictionEvaluation[];
  learning_obligations?: LtpLearningObligation[];
  learning_history?: { events: LtpLearningEvent[]; digest?: string };
  as_of?: string;
  gates: LtpGate[];
  views: Record<string, LtpView>;
  health: {
    counts: { error: number; warning: number; info: number };
    publishable: boolean;
    diagnostics: LtpDiagnostic[];
  };
  build?: { source_hash?: string };
  [key: string]: unknown;
}

export interface LtpArtifactBundle {
  artifacts: { domain: string; manifest: LtpModel }[];
}

const OWNER = "ltp";

export function scopedLtpId(domain: string, localId: string): string {
  return `${encodeURIComponent(domain)}::${localId}`;
}

export const ltpMapping: ManifestMapping = {
  types: ["ltp.model", "ltp.entity", "ltp.claim", "ltp.relation", "ltp.prediction"],

  toResources(manifest: unknown): AgencyResource[] {
    const resources: AgencyResource[] = [];
    for (const artifact of (manifest as LtpArtifactBundle).artifacts ?? []) {
      const { domain, manifest: model } = artifact;
      const provenance = {
        determinism: "static" as const,
        sourceId: `ltp:dashboard:${domain}`,
        sourceHash: model.build?.source_hash,
      };
      resources.push({
        id: scopedLtpId(domain, "model"),
        type: "ltp.model",
        ownerSkill: OWNER,
        domain,
        schemaVersion: 3,
        title: model.project?.name ?? "LTP model",
        status: model.health?.publishable ? "publishable" : "invalid",
        data: model,
        provenance,
      });
      for (const entity of model.entities ?? []) {
        resources.push({
          id: scopedLtpId(domain, entity.id),
          type: "ltp.entity",
          ownerSkill: OWNER,
          domain,
          schemaVersion: 3,
          title: entity.statement,
          status: entity.review_status,
          data: entity,
          provenance,
        });
      }
      for (const claim of model.causal_claims ?? []) {
        resources.push({
          id: scopedLtpId(domain, claim.id),
          type: "ltp.claim",
          ownerSkill: OWNER,
          domain,
          schemaVersion: 3,
          title: claim.id,
          status: claim.logic_status,
          data: claim,
          provenance,
        });
      }
      for (const relation of model.semantic_relations ?? []) {
        resources.push({
          id: scopedLtpId(domain, relation.id),
          type: "ltp.relation",
          ownerSkill: OWNER,
          domain,
          schemaVersion: 3,
          title: `${relation.source} ${relation.relation.replaceAll("_", " ")} ${relation.target}`,
          status: relation.relation,
          data: relation,
          provenance,
        });
      }
      for (const prediction of model.predicted_effects ?? []) {
        const evaluation = (model.prediction_evaluations ?? []).find(
          (item) => item.prediction === prediction.id,
        );
        resources.push({
          id: scopedLtpId(domain, prediction.id),
          type: "ltp.prediction",
          ownerSkill: OWNER,
          domain,
          schemaVersion: 3,
          title: prediction.statement,
          status: evaluation?.result ?? "untested",
          data: {
            ...prediction,
            evaluation,
            observations: (model.observations ?? []).filter(
              (item) => item.prediction === prediction.id,
            ),
          },
          provenance,
        });
      }
    }
    return resources;
  },

  toRelations(manifest: unknown): AgencyRelation[] {
    const relations: AgencyRelation[] = [];
    for (const { domain, manifest: model } of (manifest as LtpArtifactBundle).artifacts ?? []) {
      for (const claim of model.causal_claims ?? []) {
        if (claim.verification?.hypothesis_ref) {
          relations.push({
            id: `ltp:${encodeURIComponent(domain)}:verified-by:${claim.id}`,
            type: "VERIFIED_BY",
            from: { type: "ltp.claim", id: scopedLtpId(domain, claim.id) },
            to: {
              type: "hypothesis",
              id: `${encodeURIComponent(domain)}::${claim.verification.hypothesis_ref}`,
            },
            metadata: { role: claim.verification.role, domain },
          });
        }
      }
      for (const relation of model.semantic_relations ?? []) {
        relations.push({
          id: `ltp:${encodeURIComponent(domain)}:semantic:${relation.id}`,
          type: relation.relation.toUpperCase(),
          from: { type: "ltp.entity", id: scopedLtpId(domain, relation.source) },
          to: { type: "ltp.entity", id: scopedLtpId(domain, relation.target) },
          metadata: { relation: relation.id, domain },
        });
      }
      for (const prediction of model.predicted_effects ?? []) {
        relations.push({
          id: `ltp:${encodeURIComponent(domain)}:predicts:${prediction.id}`,
          type: "PREDICTS",
          from: { type: "ltp.claim", id: scopedLtpId(domain, prediction.source_claim) },
          to: { type: "ltp.prediction", id: scopedLtpId(domain, prediction.id) },
          metadata: { domain },
        });
      }
    }
    return relations;
  },
};
