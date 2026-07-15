/**
 * A `static` ResourceSource backed by a generated JSON manifest (LTP's
 * dashboard-model.json, hypothesize's research-status.json). Pure function of
 * committed files: reproducible, never writable. The plugin supplies a mapping
 * from its manifest shape to resources + relations.
 */

import type {
  AgencyRelation,
  AgencyResource,
  ResourceRef,
  ResourceSource,
  ResourceType,
  SkillId,
} from "@agency/skill-sdk";
import { refString } from "@agency/skill-sdk";

export interface ManifestMapping {
  types: ResourceType[];
  toResources(manifest: unknown): AgencyResource[];
  toRelations?(manifest: unknown): AgencyRelation[];
}

export interface ManifestSourceOptions {
  id: string;
  ownerSkill: SkillId;
  load: () => Promise<unknown>;
  mapping: ManifestMapping;
}

interface Cache {
  resources: AgencyResource[];
  relations: AgencyRelation[];
  byRef: Map<string, AgencyResource>;
}

export function manifestSource(options: ManifestSourceOptions): ResourceSource {
  let cache: Cache | null = null;

  async function ensure(): Promise<Cache> {
    if (cache) return cache;
    const manifest = await options.load();
    const resources = options.mapping.toResources(manifest);
    const relations = options.mapping.toRelations?.(manifest) ?? [];
    cache = {
      resources,
      relations,
      byRef: new Map(resources.map((r) => [refString({ type: r.type, id: r.id }), r])),
    };
    return cache;
  }

  return {
    id: options.id,
    ownerSkill: options.ownerSkill,
    determinism: "static",
    types: options.mapping.types,
    capabilities: { readable: true, watchable: false, writable: false },

    async list(): Promise<AgencyResource[]> {
      return (await ensure()).resources;
    },
    async get(ref: ResourceRef): Promise<AgencyResource | null> {
      return (await ensure()).byRef.get(refString(ref)) ?? null;
    },
    async relations(ref: ResourceRef): Promise<AgencyRelation[]> {
      const { relations } = await ensure();
      const key = refString(ref);
      return relations.filter(
        (relation) => refString(relation.from) === key || refString(relation.to) === key,
      );
    },
  };
}
