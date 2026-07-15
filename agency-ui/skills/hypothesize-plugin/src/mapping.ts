import type { AgencyResource } from "@agency/skill-sdk";
import type { ManifestMapping } from "@agency/core";

export interface HypothesisRow {
  id: string;
  title: string;
  summary?: string;
  conclusion?: string;
  capability_status?: string;
  evidence_maturity?: string;
  evidence_health?: string;
  [key: string]: unknown;
}

export interface HypothesizeManifest {
  portfolio?: { title?: string; thesis?: string };
  hypotheses: HypothesisRow[];
  build?: { source_hash?: string };
}

export const hypothesizeMapping: ManifestMapping = {
  types: ["hypothesis"],
  toResources(manifest: unknown): AgencyResource[] {
    const data = manifest as HypothesizeManifest;
    const provenance = {
      determinism: "static" as const,
      sourceId: "hypothesize:research-status",
      sourceHash: data.build?.source_hash,
    };
    return (data.hypotheses ?? []).map((hypothesis) => ({
      id: hypothesis.id,
      type: "hypothesis",
      ownerSkill: "hypothesize",
      schemaVersion: 1,
      title: hypothesis.title,
      status: hypothesis.conclusion,
      data: hypothesis,
      provenance,
    }));
  },
};
