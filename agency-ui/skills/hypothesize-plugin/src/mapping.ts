/**
 * Maps hypothesize's generated `research-status.json` into agency resources +
 * relations. The manifest is genuine `hypothesize sync` output: three derived
 * status dimensions (capability / evidence maturity / conclusion) plus the
 * authored epistemic envelope each hypothesis carries — its host subject, scope,
 * expected consequences, defeaters, and illustrative cross-skill relations.
 *
 * A resource view only ever receives its own resource, never the whole manifest,
 * so the evidence trace the inspector renders is assembled HERE (joining each
 * hypothesis to its capabilities and admitted evidence) and carried on the
 * resource's data.
 */

import type { AgencyRelation, AgencyResource } from "@agency/skill-sdk";
import { parseRef } from "@agency/skill-sdk";
import type { ManifestMapping } from "@agency/core";

/** A single admitted evidence artifact, as normalized into the manifest. */
export interface EvidenceArtifact {
  id: string;
  title?: string;
  summary?: string;
  relation?: string;
  tags?: string[];
  kind?: string;
  maturity?: string;
  outcome?: string;
  qualified?: boolean;
  preregistered?: boolean;
  hypotheses?: string[];
  [key: string]: unknown;
}

/** A derived capability row. */
export interface CapabilityRow {
  id: string;
  title?: string;
  summary?: string;
  status?: string;
  hypotheses?: string[];
  scenario_counts?: Record<string, number>;
  [key: string]: unknown;
}

/** An authored cross-skill relation: `[type, "ownerType:id"]`. */
export type EnvelopeRelation = [string, string];

/** One row in the inspector's evidence trace. */
export interface TraceItem {
  id: string | null;
  title: string;
  relation: string;
  summary: string;
  tags: string[];
}

export interface HypothesisRow {
  id: string;
  title: string;
  statement?: string;
  summary?: string;
  subject?: string;
  scope?: string;
  consequences?: string[];
  defeaters?: string[];
  relations?: EnvelopeRelation[];
  conclusion?: string;
  capability_status?: string;
  evidence_maturity?: string;
  evidence_health?: string;
  /** ids of the admitted evidence linked to this hypothesis. */
  evidence?: string[];
  /** Assembled by the mapping for the inspector; not present in the manifest. */
  trace?: TraceItem[];
  [key: string]: unknown;
}

export interface HypothesizeManifest {
  portfolio?: { title?: string; thesis?: string; last_reviewed?: string };
  hypotheses: HypothesisRow[];
  capabilities?: CapabilityRow[];
  evidence?: EvidenceArtifact[];
  build?: { source_hash?: string };
}

function capabilityRelation(status?: string): string {
  if (status === "implemented") return "demonstrates capability";
  if (status === "partial") return "demonstrates mechanism";
  if (status === "regressed" || status === "failing") return "capability regressed";
  return "specifies capability";
}

function capabilitySummary(capability: CapabilityRow): string {
  if (capability.summary) return capability.summary;
  const counts = capability.scenario_counts ?? {};
  const passed = counts.passed ?? 0;
  const total = Object.values(counts).reduce((sum, n) => sum + n, 0);
  return `${passed} of ${total} required scenarios pass.`;
}

function evidenceRelation(evidence: EvidenceArtifact): string {
  if (evidence.relation) return evidence.relation;
  if (evidence.outcome && evidence.outcome !== "not_tested") return `result: ${evidence.outcome}`;
  return "informs";
}

function evidenceTags(evidence: EvidenceArtifact): string[] {
  if (evidence.tags && evidence.tags.length) return evidence.tags;
  const tags: string[] = [];
  if (evidence.maturity) tags.push(evidence.maturity);
  if (evidence.kind) tags.push(evidence.kind);
  return tags;
}

/** Join a hypothesis to the capabilities and evidence that stand behind it. */
function buildTrace(
  hypothesis: HypothesisRow,
  capabilities: CapabilityRow[],
  evidenceById: Map<string, EvidenceArtifact>,
): TraceItem[] {
  const items: TraceItem[] = [];

  for (const capability of capabilities) {
    if (!(capability.hypotheses ?? []).includes(hypothesis.id)) continue;
    items.push({
      id: `capability:${capability.id}`,
      title: capability.title ?? capability.id,
      relation: capabilityRelation(capability.status),
      summary: capabilitySummary(capability),
      tags: [capability.status ?? "specified", "acceptance tests"],
    });
  }

  const linkedEvidence = (hypothesis.evidence ?? [])
    .map((id) => evidenceById.get(id))
    .filter((item): item is EvidenceArtifact => Boolean(item));
  for (const evidence of linkedEvidence) {
    items.push({
      id: `evidence:${evidence.id}`,
      title: evidence.title ?? evidence.id,
      relation: evidenceRelation(evidence),
      summary: evidence.summary ?? "",
      tags: evidenceTags(evidence),
    });
  }

  // Mirror the honest "nothing admitted yet" row: a proposition can have a fully
  // implemented capability and still carry no outcome evidence at all.
  if (linkedEvidence.length === 0) {
    items.push({
      id: null,
      title: "Outcome evidence",
      relation: "none admitted",
      summary: "No qualified study is linked to this proposition.",
      tags: ["no study", "no conclusion change"],
    });
  }

  return items;
}

export const hypothesizeMapping: ManifestMapping = {
  types: ["hypothesis"],

  toResources(manifest: unknown): AgencyResource[] {
    const data = manifest as HypothesizeManifest;
    const capabilities = data.capabilities ?? [];
    const evidenceById = new Map((data.evidence ?? []).map((item) => [item.id, item]));
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
      data: { ...hypothesis, trace: buildTrace(hypothesis, capabilities, evidenceById) },
      provenance,
    }));
  },

  // Cross-skill relations are authored on each hypothesis (illustrative links to
  // the LTP claims, promises, and ZPD probes the surface sits alongside). We only
  // republish them as federated relations; we never invent or rewrite them.
  toRelations(manifest: unknown): AgencyRelation[] {
    const data = manifest as HypothesizeManifest;
    const relations: AgencyRelation[] = [];
    for (const hypothesis of data.hypotheses ?? []) {
      for (const [type, ref] of hypothesis.relations ?? []) {
        relations.push({
          id: `hypothesize:${hypothesis.id}:${type}:${ref}`,
          type,
          from: { type: "hypothesis", id: hypothesis.id },
          to: parseRef(ref),
        });
      }
    }
    return relations;
  },
};
