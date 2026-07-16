/**
 * The resource seam.
 *
 * Nothing in the shell or in a plugin ever talks to "a file" or "a database".
 * Everything reads and writes resources through a {@link ResourceSource}.
 * Read-only vs. mutable is a *declared capability of the source*, not a
 * different code path -- so hosting a mutable store later (ZPD's append-only
 * learning evidence) is one new source implementation, with zero change to the
 * shell, to other plugins, or to the resource shape.
 */

import type { AgencyActionResult } from "./actions";

export type SkillId = string;
export type ResourceType = string;

/**
 * The shared resource type for a workspace domain. A domain provider (currently
 * Promisify) owns discovery and hierarchy; the shell and every skill consume
 * only this neutral resource contract.
 */
export const DOMAIN_RESOURCE_TYPE = "agency.domain";

export interface DomainResourceData {
  path: string;
  parent: string | null;
  depth: number;
  children: string[];
  /** Repository-relative paths this domain describes, supplied by Promisify. */
  subjects: string[];
  declaredCount?: number;
  effectivePromiseCount?: number;
}

/** A stable reference to a resource, e.g. `hypothesis:71`. */
export interface ResourceRef {
  type: ResourceType;
  id: string;
}

export function refString(ref: ResourceRef): string {
  return `${ref.type}:${ref.id}`;
}

export function parseRef(value: string): ResourceRef {
  const index = value.indexOf(":");
  if (index < 0) {
    throw new Error(`invalid resource ref "${value}" (expected "type:id")`);
  }
  return { type: value.slice(0, index), id: value.slice(index + 1) };
}

/**
 * `static`  -- a pure function of committed files (LTP, hypothesize): reproducible,
 *              git-committable, CI-checkable. Never writable.
 * `live`    -- backed by a mutable store (ZPD): may be watchable and writable.
 */
export type Determinism = "static" | "live";

export interface SourceCapabilities {
  /** Every source can be read. */
  readonly readable: true;
  /** Emits change notifications via {@link ResourceSource.watch}. */
  readonly watchable: boolean;
  /** Accepts mutations via {@link ResourceSource.apply}. Never true for `static`. */
  readonly writable: boolean;
}

export interface Provenance {
  determinism: Determinism;
  sourceId: string;
  /** Present for `static` sources: the hash the data was generated from. */
  sourceHash?: string;
  generatedAt?: string;
}

export interface AgencyResource<T = unknown> {
  id: string;
  type: ResourceType;
  ownerSkill: SkillId;
  /** Domain this generated or live artifact applies to. Unscoped resources never satisfy a domain query. */
  domain?: string;
  schemaVersion: number;
  title?: string;
  status?: string;
  createdAt?: string;
  updatedAt?: string;
  createdBy?: { kind: "user" | "agent" | "skill"; id: string };
  data: T;
  provenance?: Provenance;
}

export interface AgencyRelation {
  id: string;
  /** e.g. SUPPORTED_BY, CHALLENGED_BY, MOTIVATES, BLOCKED_BY, EVALUATES. */
  type: string;
  from: ResourceRef;
  to: ResourceRef;
  metadata?: Record<string, unknown>;
}

export interface ResourceQuery {
  type?: ResourceType | ResourceType[];
  ownerSkill?: SkillId;
  domain?: string;
  ids?: string[];
  search?: string;
}

export type ResourceChangeKind = "created" | "updated" | "deleted";

export interface ResourceChange {
  kind: ResourceChangeKind;
  ref: ResourceRef;
  resource?: AgencyResource;
}

/** A low-level write, submitted to a writable source's {@link ResourceSource.apply}. */
export interface ResourceMutation {
  kind: ResourceChangeKind;
  ref: ResourceRef;
  domain?: string;
  data?: unknown;
  /** Optimistic-concurrency guard for `live` sources. */
  expectedVersion?: number;
}

export type Unsubscribe = () => void;

/**
 * The single interface the shell federates over. A plugin registers one (or
 * more) of these in {@link AgencySkillContext.resources} during activation.
 */
export interface ResourceSource {
  readonly id: string;
  readonly ownerSkill: SkillId;
  readonly determinism: Determinism;
  /** Resource types this source can serve (used to route reads/writes). */
  readonly types: ResourceType[];
  readonly capabilities: SourceCapabilities;

  // --- read (every source) ---
  list(query?: ResourceQuery): Promise<AgencyResource[]>;
  get(ref: ResourceRef): Promise<AgencyResource | null>;
  relations(ref: ResourceRef): Promise<AgencyRelation[]>;

  // --- watch (present iff capabilities.watchable) ---
  watch?(query: ResourceQuery, onChange: (change: ResourceChange) => void): Unsubscribe;

  // --- write (present iff capabilities.writable; never on `static`) ---
  apply?(mutation: ResourceMutation): Promise<AgencyActionResult>;
}
