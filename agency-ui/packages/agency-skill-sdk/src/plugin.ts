/**
 * `AgencySkillPlugin` is the UI adapter for an agency-engineering skill -- kept
 * deliberately separate from the agentic skill itself (its Python engine, CLI,
 * and SKILL.md). The `manifest` is declarative and inspectable; `activate()`
 * connects behavior (sources, capabilities, commands) to the host.
 */

import type { Contributions } from "./contributions";
import type { SkillId } from "./resources";
import type {
  AgencyHost,
  CapabilityId,
  NamespacedStorage,
  SkillLogger,
} from "./services";

export interface SkillDependency {
  /** Prefer targeting a capability over a specific skill. */
  skillId?: SkillId;
  capability?: CapabilityId;
  version?: string;
  reason?: string;
}

export interface AgencySkillManifest {
  id: SkillId;
  name: string;
  version: string;
  description: string;

  requires?: SkillDependency[];
  /** Offer this dependency first, but keep the plugin usable without it. */
  recommendedDependencies?: SkillDependency[];
  /** Use silently when present; absence never blocks or prompts. */
  optionalDependencies?: SkillDependency[];
  provides?: CapabilityId[];

  contributions?: Contributions;
}

/** The narrow, stable API a plugin receives at activation. */
export interface AgencySkillContext extends AgencyHost {
  pluginId: SkillId;
  storage: NamespacedStorage;
  logger: SkillLogger;
}

export interface AgencySkillRuntime {
  deactivate?(): void | Promise<void>;
}

export interface AgencySkillPlugin {
  manifest: AgencySkillManifest;
  activate(
    context: AgencySkillContext,
  ): AgencySkillRuntime | Promise<AgencySkillRuntime>;
}
