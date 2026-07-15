/**
 * Agent- and user-invoked actions produce a standard result, and risky writes
 * are expressed as confirmable proposed changes. This keeps mutation auditable
 * wherever it appears -- and, because a `static` source has no `apply`, it is
 * simply unreachable for read-only skills.
 */

import type { ResourceMutation } from "./resources";

export interface EvidenceReference {
  ref: string;
  note?: string;
}

export interface NextAction {
  commandId: string;
  title: string;
  args?: unknown;
}

export interface AgencyActionResult {
  summary: string;
  createdResources?: string[];
  updatedResources?: string[];
  proposedChanges?: ProposedChange[];
  nextActions?: NextAction[];
  evidence?: EvidenceReference[];
}

export type ChangeRisk = "low" | "medium" | "high";

/**
 * A described, confirmable write. The shell can render and gate it before it is
 * applied to a source. Mission/promise-level changes set `requiresConfirmation`.
 */
export interface ProposedChange {
  id: string;
  description: string;
  risk: ChangeRisk;
  requiresConfirmation: boolean;
  mutations: ResourceMutation[];
}
