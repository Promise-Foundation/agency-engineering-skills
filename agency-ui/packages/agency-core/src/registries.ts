/** In-memory implementations of the SDK's small service interfaces. */

import type {
  AgencyActionResult,
  CapabilityId,
  CapabilityRegistry,
  CommandContext,
  CommandHandler,
  CommandRegistry,
  EventBus,
  NamespacedStorage,
  NavigationService,
  NotificationService,
  ResourceRef,
  ResourceService,
  SelectionService,
  SkillLogger,
  Unsubscribe,
} from "@agency/skill-sdk";

export class MapCapabilityRegistry implements CapabilityRegistry {
  private readonly map = new Map<CapabilityId, unknown>();

  register<T>(id: CapabilityId, implementation: T): Unsubscribe {
    if (this.map.has(id)) throw new Error(`capability ${id} already registered`);
    this.map.set(id, implementation);
    return () => {
      if (this.map.get(id) === implementation) this.map.delete(id);
    };
  }
  unregister(id: CapabilityId): void {
    this.map.delete(id);
  }
  get<T>(id: CapabilityId): T | undefined {
    return this.map.get(id) as T | undefined;
  }
  has(id: CapabilityId): boolean {
    return this.map.has(id);
  }
  list(): CapabilityId[] {
    return [...this.map.keys()].sort();
  }
}

export class Emitter implements EventBus {
  private readonly handlers = new Map<string, Set<(payload: unknown) => void>>();

  emit(type: string, payload?: unknown): void {
    for (const handler of this.handlers.get(type) ?? []) {
      try {
        handler(payload);
      } catch (error) {
        // Handler failures are isolated -- one bad listener can't break emit.
        console.error(`event handler for ${type} threw`, error);
      }
    }
  }
  on(type: string, handler: (payload: unknown) => void): Unsubscribe {
    let set = this.handlers.get(type);
    if (!set) {
      set = new Set();
      this.handlers.set(type, set);
    }
    set.add(handler);
    return () => set!.delete(handler);
  }
}

export class SelectionState implements SelectionService {
  private ref: ResourceRef | null = null;
  private readonly subscribers = new Set<(ref: ResourceRef | null) => void>();

  current(): ResourceRef | null {
    return this.ref;
  }
  select(ref: ResourceRef | null): void {
    this.ref = ref;
    for (const subscriber of this.subscribers) subscriber(ref);
  }
  subscribe(handler: (ref: ResourceRef | null) => void): Unsubscribe {
    this.subscribers.add(handler);
    return () => this.subscribers.delete(handler);
  }
}

export class CommandBus implements CommandRegistry {
  private readonly handlers = new Map<string, CommandHandler>();

  constructor(
    private readonly deps: {
      selection: SelectionService;
      resources: ResourceService;
      capabilities: CapabilityRegistry;
      events: EventBus;
    },
  ) {}

  register(id: string, handler: CommandHandler): Unsubscribe {
    if (this.handlers.has(id)) throw new Error(`command ${id} already registered`);
    this.handlers.set(id, handler);
    return () => {
      if (this.handlers.get(id) === handler) this.handlers.delete(id);
    };
  }
  unregister(id: string): void {
    this.handlers.delete(id);
  }
  list(): string[] {
    return [...this.handlers.keys()].sort();
  }
  async execute(id: string, args?: unknown): Promise<AgencyActionResult | void> {
    const handler = this.handlers.get(id);
    if (!handler) throw new Error(`no command ${id}`);
    const context: CommandContext = {
      selection: this.deps.selection.current(),
      resources: this.deps.resources,
      capabilities: this.deps.capabilities,
      args,
    };
    const result = await handler(context);
    this.deps.events.emit("command.executed", { commandId: id });
    return result;
  }
}

export function createMemoryStorage(namespace: string): NamespacedStorage {
  const store = new Map<string, unknown>();
  const key = (k: string) => `${namespace}:${k}`;
  return {
    async get<T>(k: string): Promise<T | null> {
      return (store.has(key(k)) ? (store.get(key(k)) as T) : null);
    },
    async set<T>(k: string, value: T): Promise<void> {
      store.set(key(k), value);
    },
    async remove(k: string): Promise<void> {
      store.delete(key(k));
    },
    async keys(): Promise<string[]> {
      const prefix = `${namespace}:`;
      return [...store.keys()].filter((k) => k.startsWith(prefix)).map((k) => k.slice(prefix.length));
    },
  };
}

export function createLogger(pluginId: string): SkillLogger {
  const tag = `[${pluginId}]`;
  return {
    debug: (...args) => console.debug(tag, ...args),
    info: (...args) => console.info(tag, ...args),
    warn: (...args) => console.warn(tag, ...args),
    error: (...args) => console.error(tag, ...args),
  };
}

export const consoleNotifications: NotificationService = {
  info: (message) => console.info(message),
  warn: (message) => console.warn(message),
  error: (message) => console.error(message),
};

export const noopNavigation: NavigationService = {
  navigate: () => {},
  currentPath: () => "/",
};
