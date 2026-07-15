/**
 * Federates every registered source. Reads fan out and merge; writes route to
 * the one writable source owning the resource type. Crucially, callers cannot
 * tell whether a resource came from a `static` LTP manifest or a `live` ZPD
 * store -- that is the whole point of the seam.
 */

import type {
  AgencyActionResult,
  AgencyRelation,
  AgencyResource,
  ResourceChange,
  ResourceMutation,
  ResourceQuery,
  ResourceRef,
  ResourceService,
  ResourceSource,
  ResourceType,
  Unsubscribe,
} from "@agency/skill-sdk";

function requestedTypes(query?: ResourceQuery): ResourceType[] | null {
  if (!query || query.type === undefined) return null;
  return Array.isArray(query.type) ? query.type : [query.type];
}

function serves(source: ResourceSource, query?: ResourceQuery): boolean {
  const types = requestedTypes(query);
  if (!types) return true;
  return source.types.some((type) => types.includes(type));
}

function matchesResource(resource: AgencyResource, query?: ResourceQuery): boolean {
  if (!query) return true;
  const types = requestedTypes(query);
  if (types && !types.includes(resource.type)) return false;
  if (query.ownerSkill && resource.ownerSkill !== query.ownerSkill) return false;
  if (query.ids && !query.ids.includes(resource.id)) return false;
  if (query.search) {
    const needle = query.search.toLowerCase();
    const haystack = `${resource.title ?? ""} ${JSON.stringify(resource.data)}`.toLowerCase();
    if (!haystack.includes(needle)) return false;
  }
  return true;
}

export class FederatedResourceService implements ResourceService {
  private readonly _sources: ResourceSource[] = [];

  registerSource(source: ResourceSource): Unsubscribe {
    if (this._sources.some((existing) => existing.id === source.id)) {
      throw new Error(`resource source ${source.id} already registered`);
    }
    this._sources.push(source);
    return () => {
      const index = this._sources.indexOf(source);
      if (index >= 0) this._sources.splice(index, 1);
    };
  }

  sources(): ResourceSource[] {
    return [...this._sources];
  }

  async list(query?: ResourceQuery): Promise<AgencyResource[]> {
    const relevant = this._sources.filter((source) => serves(source, query));
    const batches = await Promise.all(relevant.map((source) => source.list(query)));
    return batches.flat().filter((resource) => matchesResource(resource, query));
  }

  async get(ref: ResourceRef): Promise<AgencyResource | null> {
    for (const source of this._sources) {
      if (!source.types.includes(ref.type)) continue;
      const resource = await source.get(ref);
      if (resource) return resource;
    }
    return null;
  }

  async relations(ref: ResourceRef): Promise<AgencyRelation[]> {
    // Ask every source: a cross-skill link (LTP claim -> hypothesis) is emitted
    // by whichever source knows about it, not necessarily the ref's owner.
    const batches = await Promise.all(this._sources.map((source) => source.relations(ref)));
    const byId = new Map<string, AgencyRelation>();
    for (const relation of batches.flat()) byId.set(relation.id, relation);
    return [...byId.values()];
  }

  watch(query: ResourceQuery, onChange: (change: ResourceChange) => void): Unsubscribe {
    const unsubscribes: Unsubscribe[] = [];
    for (const source of this._sources) {
      if (source.capabilities.watchable && source.watch && serves(source, query)) {
        unsubscribes.push(source.watch(query, onChange));
      }
    }
    return () => unsubscribes.forEach((unsubscribe) => unsubscribe());
  }

  canWrite(type: ResourceType): boolean {
    return this._sources.some(
      (source) => source.capabilities.writable && source.types.includes(type),
    );
  }

  async apply(mutation: ResourceMutation): Promise<AgencyActionResult> {
    const source = this._sources.find(
      (candidate) => candidate.capabilities.writable && candidate.types.includes(mutation.ref.type),
    );
    if (!source || !source.apply) {
      throw new Error(
        `no writable source for resource type ${mutation.ref.type} ` +
          `(this is expected for read-only skills)`,
      );
    }
    return source.apply(mutation);
  }
}
