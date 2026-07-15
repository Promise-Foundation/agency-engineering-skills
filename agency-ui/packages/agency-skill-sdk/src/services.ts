/**
 * The narrow host services a plugin receives. Deliberately small and stable: a
 * plugin never touches the shell's router, store, or database directly, so the
 * shell can evolve underneath it.
 */

import type { AgencyActionResult } from "./actions";
import type {
  AgencyRelation,
  AgencyResource,
  ResourceChange,
  ResourceMutation,
  ResourceQuery,
  ResourceRef,
  ResourceSource,
  ResourceType,
  Unsubscribe,
} from "./resources";

export type CapabilityId = string;

export interface CapabilityRegistry {
  register<T>(id: CapabilityId, implementation: T): Unsubscribe;
  unregister(id: CapabilityId): void;
  get<T>(id: CapabilityId): T | undefined;
  has(id: CapabilityId): boolean;
  list(): CapabilityId[];
}

/**
 * Federates every registered {@link ResourceSource}. Reads fan out and merge;
 * writes route to the single writable source owning the resource type. This is
 * the layer that makes a `static` LTP source and a `live` ZPD source look
 * identical to everything that renders them.
 */
export interface ResourceService {
  registerSource(source: ResourceSource): Unsubscribe;
  sources(): ResourceSource[];

  list(query?: ResourceQuery): Promise<AgencyResource[]>;
  get(ref: ResourceRef): Promise<AgencyResource | null>;
  relations(ref: ResourceRef): Promise<AgencyRelation[]>;
  watch(query: ResourceQuery, onChange: (change: ResourceChange) => void): Unsubscribe;

  /** True iff a writable source can serve this resource type. Drives whether the UI offers mutation. */
  canWrite(type: ResourceType): boolean;
  /** Route a mutation to the writable source owning the ref's type. Rejects if none. */
  apply(mutation: ResourceMutation): Promise<AgencyActionResult>;
}

export interface CommandContext {
  selection: ResourceRef | null;
  resources: ResourceService;
  capabilities: CapabilityRegistry;
  args?: unknown;
}

export type CommandHandler = (
  context: CommandContext,
) => Promise<AgencyActionResult | void> | AgencyActionResult | void;

export interface CommandRegistry {
  register(id: string, handler: CommandHandler): Unsubscribe;
  unregister(id: string): void;
  execute(id: string, args?: unknown): Promise<AgencyActionResult | void>;
  list(): string[];
}

export interface EventBus {
  emit(type: string, payload?: unknown): void;
  on(type: string, handler: (payload: unknown) => void): Unsubscribe;
}

/** Plugin-owned, namespaced key/value state. Separate from shared resources. */
export interface NamespacedStorage {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  remove(key: string): Promise<void>;
  keys(): Promise<string[]>;
}

export interface SelectionService {
  current(): ResourceRef | null;
  select(ref: ResourceRef | null): void;
  subscribe(handler: (ref: ResourceRef | null) => void): Unsubscribe;
}

export interface NavigationService {
  navigate(path: string): void;
  currentPath(): string;
}

export interface NotificationService {
  info(message: string): void;
  warn(message: string): void;
  error(message: string): void;
}

export interface SkillLogger {
  debug(...args: unknown[]): void;
  info(...args: unknown[]): void;
  warn(...args: unknown[]): void;
  error(...args: unknown[]): void;
}

/**
 * The shared services available both to a plugin's `activate()` (via the
 * context) and to its React components (passed as a prop). Excludes the
 * plugin-private surfaces (id, namespaced storage, logger).
 */
export interface AgencyHost {
  resources: ResourceService;
  capabilities: CapabilityRegistry;
  commands: CommandRegistry;
  events: EventBus;
  selection: SelectionService;
  navigation: NavigationService;
  notifications: NotificationService;
}
