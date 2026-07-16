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

export interface LtpArtifactBundle {
  artifacts: { domain: string; manifest: LtpModel }[];
}

const OWNER = "ltp";

export function scopedLtpId(domain: string, localId: string): string {
  return `${encodeURIComponent(domain)}::${localId}`;
}

export const ltpMapping: ManifestMapping = {
  types: ["ltp.model", "ltp.entity", "ltp.claim"],

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
        schemaVersion: 2,
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
          schemaVersion: 2,
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
          schemaVersion: 2,
          title: claim.id,
          status: claim.logic_status,
          data: claim,
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
    }
    return relations;
  },
};
