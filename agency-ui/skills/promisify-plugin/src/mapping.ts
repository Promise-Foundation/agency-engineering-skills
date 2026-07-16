/** Types + ResourceSource mapping for the normalized model emitted by
 * `norms.py explorer` (the Promisify skill). The UI reads this; it
 * never re-implements inheritance, assessment selection, or trust scoring. */

import {
  DOMAIN_RESOURCE_TYPE,
  type AgencyResource,
  type DomainResourceData,
} from "@agency/skill-sdk";
import type { ManifestMapping } from "@agency/core";

export type Verdict = "kept" | "broken" | "unknown" | "not_applicable" | "disputed";

export interface DomainRecord {
  domain: string;
  parent: string | null;
  depth: number;
  children: string[];
  subjects: string[];
  declaredCount: number;
  effectivePromiseCount: number;
}

export interface EffectiveEntry {
  promise: string;
  declaredAt: string;
  inherited: boolean;
  title?: string | null;
  statement: string;
}

export interface Promise {
  address: string;
  domain: string;
  name: string;
  title?: string | null;
  tags: string[];
  statement: string;
  subjects: string[];
  criteria: { kind?: string; instructions?: string };
  source: { authority?: string; kind?: string; rationale?: string };
}

export interface Evidence {
  kind?: string;
  reference?: string;
  summary?: string;
}

export interface Assessment {
  id: string;
  assessor: string;
  observedAt: string;
  revision?: string | null;
  promise: string;
  effectiveDomain: string;
  verdict: Verdict;
  confidence?: number | null;
  rationale?: string | null;
  evidence: Evidence[];
}

export interface TrustView {
  name: string;
  description?: string | null;
  observer: string;
  domain: string;
  snapshot: { revision?: string };
  conflictPolicy: string;
  assessmentSelection: Record<string, unknown>;
}

export interface TrustEntry {
  view: string;
  domain: string;
  observer: string;
  snapshot: { revision?: string };
  score: number | null;
  coverage: number;
  effectivePromiseCount: number;
  counts: Record<Verdict, number>;
  conflictPolicy: string;
  selectedAssessmentIds: string[];
  unresolved: string[];
  results: { promise: string; verdict: Verdict; assessmentIds: string[] }[];
}

export interface Explorer {
  repository: { name?: string | null; description?: string | null; defaultView?: string | null };
  domains: DomainRecord[];
  effective: Record<string, EffectiveEntry[]>;
  promises: Promise[];
  assessments: Assessment[];
  views: TrustView[];
  trust: TrustEntry[];
}

export const MODEL_TYPE = "norms.model";
export const PROMISE_TYPE = "norms.promise";
const OWNER = "promisify";

export const promisifyMapping: ManifestMapping = {
  types: [DOMAIN_RESOURCE_TYPE, MODEL_TYPE, PROMISE_TYPE],
  toResources(manifest: unknown): AgencyResource[] {
    const model = manifest as Explorer;
    const provenance = { determinism: "static" as const, sourceId: "promisify:explorer" };
    const resources: AgencyResource[] = [
      {
        id: "model",
        type: MODEL_TYPE,
        ownerSkill: OWNER,
        schemaVersion: 1,
        title: model.repository?.name ?? "Normative promises",
        data: model,
        provenance,
      },
    ];
    for (const domain of model.domains ?? []) {
      const data: DomainResourceData = {
        path: domain.domain,
        parent: domain.parent,
        depth: domain.depth,
        children: domain.children,
        subjects: domain.subjects,
        declaredCount: domain.declaredCount,
        effectivePromiseCount: domain.effectivePromiseCount,
      };
      resources.push({
        id: domain.domain,
        type: DOMAIN_RESOURCE_TYPE,
        ownerSkill: OWNER,
        schemaVersion: 1,
        title: domain.domain,
        data,
        provenance,
      });
    }
    for (const promise of model.promises ?? []) {
      resources.push({
        id: promise.address,
        type: PROMISE_TYPE,
        ownerSkill: OWNER,
        schemaVersion: 1,
        title: promise.title ?? promise.statement,
        status: promise.domain,
        data: promise,
        provenance,
      });
    }
    return resources;
  },
};
