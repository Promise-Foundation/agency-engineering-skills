/**
 * A `live` ResourceSource backed by an in-memory store: readable, watchable, and
 * writable. This is the stand-in for a skill (ZPD) that fetches from a mutable
 * store -- and the proof that adding mutation later is one new source, not a
 * shell rewrite. The exact same interface, different capabilities.
 */

import type {
  AgencyActionResult,
  AgencyRelation,
  AgencyResource,
  ResourceChange,
  ResourceMutation,
  ResourceQuery,
  ResourceRef,
  ResourceSource,
  ResourceType,
  SkillId,
  Unsubscribe,
} from "@agency/skill-sdk";
import { refString } from "@agency/skill-sdk";

export interface MemorySourceOptions {
  id: string;
  ownerSkill: SkillId;
  types: ResourceType[];
  seedResources?: AgencyResource[];
  seedRelations?: AgencyRelation[];
}

interface Watcher {
  query: ResourceQuery;
  onChange: (change: ResourceChange) => void;
}

export function createMemorySource(options: MemorySourceOptions): ResourceSource {
  const resources = new Map<string, AgencyResource>();
  const relations = new Map<string, AgencyRelation>();
  const watchers = new Set<Watcher>();

  for (const resource of options.seedResources ?? []) {
    resources.set(refString({ type: resource.type, id: resource.id }), resource);
  }
  for (const relation of options.seedRelations ?? []) relations.set(relation.id, relation);

  function matches(query: ResourceQuery, ref: ResourceRef): boolean {
    if (query.type === undefined) return true;
    const types = Array.isArray(query.type) ? query.type : [query.type];
    return types.includes(ref.type);
  }

  function notify(change: ResourceChange): void {
    for (const watcher of watchers) {
      if (matches(watcher.query, change.ref)) watcher.onChange(change);
    }
  }

  return {
    id: options.id,
    ownerSkill: options.ownerSkill,
    determinism: "live",
    types: options.types,
    capabilities: { readable: true, watchable: true, writable: true },

    async list(): Promise<AgencyResource[]> {
      return [...resources.values()];
    },
    async get(ref: ResourceRef): Promise<AgencyResource | null> {
      return resources.get(refString(ref)) ?? null;
    },
    async relations(ref: ResourceRef): Promise<AgencyRelation[]> {
      const key = refString(ref);
      return [...relations.values()].filter(
        (relation) => refString(relation.from) === key || refString(relation.to) === key,
      );
    },
    watch(query: ResourceQuery, onChange: (change: ResourceChange) => void): Unsubscribe {
      const watcher: Watcher = { query, onChange };
      watchers.add(watcher);
      return () => watchers.delete(watcher);
    },
    async apply(mutation: ResourceMutation): Promise<AgencyActionResult> {
      const key = refString(mutation.ref);
      if (mutation.kind === "deleted") {
        resources.delete(key);
        notify({ kind: "deleted", ref: mutation.ref });
        return { summary: `deleted ${key}` };
      }
      const now = new Date().toISOString();
      const existing = resources.get(key);
      const resource: AgencyResource = {
        id: mutation.ref.id,
        type: mutation.ref.type,
        ownerSkill: options.ownerSkill,
        schemaVersion: 1,
        createdAt: existing?.createdAt ?? now,
        updatedAt: now,
        createdBy: existing?.createdBy ?? { kind: "user", id: "local" },
        data: mutation.data ?? existing?.data ?? {},
        provenance: { determinism: "live", sourceId: options.id, generatedAt: now },
      };
      resources.set(key, resource);
      const kind = existing ? "updated" : "created";
      notify({ kind, ref: mutation.ref, resource });
      return {
        summary: `${kind} ${key}`,
        createdResources: existing ? undefined : [key],
        updatedResources: existing ? [key] : undefined,
      };
    },
  };
}
