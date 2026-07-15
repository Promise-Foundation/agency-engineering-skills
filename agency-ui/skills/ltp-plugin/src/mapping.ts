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
  verification?: { hypothesis_ref: string; role?: string };
  clr?: Record<string, { result: string; reservation?: string }>;
  [key: string]: unknown;
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

const OWNER = "ltp";

export const ltpMapping: ManifestMapping = {
  types: ["ltp.model", "ltp.entity", "ltp.claim"],

  toResources(manifest: unknown): AgencyResource[] {
    const model = manifest as LtpModel;
    const provenance = {
      determinism: "static" as const,
      sourceId: "ltp:dashboard",
      sourceHash: model.build?.source_hash,
    };
    const resources: AgencyResource[] = [
      {
        id: "model",
        type: "ltp.model",
        ownerSkill: OWNER,
        schemaVersion: 2,
        title: model.project?.name ?? "LTP model",
        status: model.health?.publishable ? "publishable" : "invalid",
        data: model,
        provenance,
      },
    ];
    for (const entity of model.entities ?? []) {
      resources.push({
        id: entity.id,
        type: "ltp.entity",
        ownerSkill: OWNER,
        schemaVersion: 2,
        title: entity.statement,
        status: entity.review_status,
        data: entity,
        provenance,
      });
    }
    for (const claim of model.causal_claims ?? []) {
      resources.push({
        id: claim.id,
        type: "ltp.claim",
        ownerSkill: OWNER,
        schemaVersion: 2,
        title: claim.id,
        status: claim.logic_status,
        data: claim,
        provenance,
      });
    }
    return resources;
  },

  toRelations(manifest: unknown): AgencyRelation[] {
    const model = manifest as LtpModel;
    const relations: AgencyRelation[] = [];
    for (const claim of model.causal_claims ?? []) {
      if (claim.verification?.hypothesis_ref) {
        relations.push({
          id: `ltp:verified-by:${claim.id}`,
          type: "VERIFIED_BY",
          from: { type: "ltp.claim", id: claim.id },
          to: { type: "hypothesis", id: claim.verification.hypothesis_ref },
          metadata: { role: claim.verification.role },
        });
      }
    }
    return relations;
  },
};
