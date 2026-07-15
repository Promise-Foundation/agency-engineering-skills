/**
 * The plugin runtime: resolve dependencies, activate plugins in order, build each
 * plugin's narrow context, and aggregate their contributions for the shell.
 * Activation failures are isolated -- one plugin cannot break the others.
 */

import type {
  AgencyHost,
  AgencySkillContext,
  AgencySkillManifest,
  AgencySkillPlugin,
  AgencySkillRuntime,
  CommandContribution,
  DashboardCardContribution,
  InspectorContribution,
  NavigationContribution,
  NavigationService,
  NotificationService,
  PanelContribution,
  ResourceViewContribution,
  RouteContribution,
  SkillId,
} from "@agency/skill-sdk";
import {
  CommandBus,
  Emitter,
  MapCapabilityRegistry,
  SelectionState,
  consoleNotifications,
  createLogger,
  createMemoryStorage,
  noopNavigation,
} from "./registries";
import { FederatedResourceService } from "./resource-service";

export interface HostOptions {
  navigation?: NavigationService;
  notifications?: NotificationService;
}

export interface ActivationResult {
  activated: SkillId[];
  failed: { id: SkillId; reason: string }[];
}

type Tagged<T> = T & { skillId: SkillId };

export interface AggregatedContributions {
  navigation: Tagged<NavigationContribution>[];
  routes: Tagged<RouteContribution>[];
  commands: Tagged<CommandContribution>[];
  dashboardCards: Tagged<DashboardCardContribution>[];
  resourceViews: Tagged<ResourceViewContribution>[];
  inspectors: Tagged<InspectorContribution>[];
  workspacePanels: Tagged<PanelContribution>[];
}

interface Resolution {
  order: AgencySkillPlugin[];
  failures: { id: SkillId; reason: string }[];
}

/** Topologically order plugins so every capability provider activates before its consumers. */
export function resolveOrder(plugins: AgencySkillPlugin[]): Resolution {
  const byId = new Map(plugins.map((p) => [p.manifest.id, p]));
  const capabilityProviders = new Map<string, SkillId[]>();
  for (const plugin of plugins) {
    for (const capability of plugin.manifest.provides ?? []) {
      capabilityProviders.set(capability, [
        ...(capabilityProviders.get(capability) ?? []),
        plugin.manifest.id,
      ]);
    }
  }

  const failures: { id: SkillId; reason: string }[] = [];
  const failed = new Set<SkillId>();
  const requiredProviders = new Map<SkillId, Set<SkillId>>();

  for (const plugin of plugins) {
    const providers = new Set<SkillId>();
    for (const dependency of plugin.manifest.requires ?? []) {
      let resolved: SkillId[] = [];
      if (dependency.skillId) resolved = byId.has(dependency.skillId) ? [dependency.skillId] : [];
      else if (dependency.capability) resolved = capabilityProviders.get(dependency.capability) ?? [];
      if (resolved.length === 0) {
        const what = dependency.capability ?? dependency.skillId ?? "unknown";
        failures.push({ id: plugin.manifest.id, reason: `missing required dependency: ${what}` });
        failed.add(plugin.manifest.id);
        break;
      }
      resolved.forEach((id) => providers.add(id));
    }
    requiredProviders.set(plugin.manifest.id, providers);
  }

  // Kahn's algorithm over the non-failed plugins.
  const live = plugins.filter((p) => !failed.has(p.manifest.id));
  const indegree = new Map<SkillId, number>();
  const dependents = new Map<SkillId, SkillId[]>();
  for (const plugin of live) indegree.set(plugin.manifest.id, 0);
  for (const plugin of live) {
    for (const provider of requiredProviders.get(plugin.manifest.id) ?? []) {
      if (failed.has(provider)) continue;
      indegree.set(plugin.manifest.id, (indegree.get(plugin.manifest.id) ?? 0) + 1);
      dependents.set(provider, [...(dependents.get(provider) ?? []), plugin.manifest.id]);
    }
  }
  const queue = live.filter((p) => (indegree.get(p.manifest.id) ?? 0) === 0).map((p) => p.manifest.id);
  const order: AgencySkillPlugin[] = [];
  while (queue.length) {
    const id = queue.shift()!;
    order.push(byId.get(id)!);
    for (const dependent of dependents.get(id) ?? []) {
      indegree.set(dependent, (indegree.get(dependent) ?? 0) - 1);
      if (indegree.get(dependent) === 0) queue.push(dependent);
    }
  }
  for (const plugin of live) {
    if (!order.includes(plugin)) {
      failures.push({ id: plugin.manifest.id, reason: "dependency cycle" });
    }
  }
  return { order, failures };
}

export class PluginHost {
  readonly resources = new FederatedResourceService();
  readonly capabilities = new MapCapabilityRegistry();
  readonly events = new Emitter();
  readonly selection = new SelectionState();
  readonly navigation: NavigationService;
  readonly notifications: NotificationService;
  readonly commands: CommandBus;
  readonly host: AgencyHost;

  private readonly plugins: AgencySkillPlugin[] = [];
  private readonly runtimes = new Map<SkillId, AgencySkillRuntime>();
  private readonly activatedIds: SkillId[] = [];

  constructor(options: HostOptions = {}) {
    this.navigation = options.navigation ?? noopNavigation;
    this.notifications = options.notifications ?? consoleNotifications;
    this.commands = new CommandBus({
      selection: this.selection,
      resources: this.resources,
      capabilities: this.capabilities,
      events: this.events,
    });
    this.host = {
      resources: this.resources,
      capabilities: this.capabilities,
      commands: this.commands,
      events: this.events,
      selection: this.selection,
      navigation: this.navigation,
      notifications: this.notifications,
    };
  }

  register(plugin: AgencySkillPlugin): void {
    this.plugins.push(plugin);
  }

  async activateAll(): Promise<ActivationResult> {
    const { order, failures } = resolveOrder(this.plugins);
    const failed = [...failures];
    for (const plugin of order) {
      const context: AgencySkillContext = {
        ...this.host,
        pluginId: plugin.manifest.id,
        storage: createMemoryStorage(plugin.manifest.id),
        logger: createLogger(plugin.manifest.id),
      };
      try {
        const runtime = await plugin.activate(context);
        this.runtimes.set(plugin.manifest.id, runtime);
        this.activatedIds.push(plugin.manifest.id);
      } catch (error) {
        failed.push({ id: plugin.manifest.id, reason: String(error) });
      }
    }
    return { activated: [...this.activatedIds], failed };
  }

  activatedManifests(): AgencySkillManifest[] {
    return this.activatedIds
      .map((id) => this.plugins.find((p) => p.manifest.id === id)!.manifest)
      .filter(Boolean);
  }

  contributions(): AggregatedContributions {
    const collect = <T extends { order?: number; id: string }>(
      pick: (m: AgencySkillManifest) => T[] | undefined,
    ): Tagged<T>[] =>
      this.activatedManifests()
        .flatMap((manifest) =>
          (pick(manifest) ?? []).map((item) => ({ ...item, skillId: manifest.id })),
        )
        .sort((a, b) => (a.order ?? 0) - (b.order ?? 0) || a.id.localeCompare(b.id));

    return {
      navigation: collect((m) => m.contributions?.navigation),
      routes: collect((m) => m.contributions?.routes),
      commands: collect((m) => m.contributions?.commands),
      dashboardCards: collect((m) => m.contributions?.dashboardCards),
      resourceViews: collect((m) => m.contributions?.resourceViews),
      inspectors: collect((m) => m.contributions?.inspectors),
      workspacePanels: collect((m) => m.contributions?.workspacePanels),
    };
  }

  async deactivateAll(): Promise<void> {
    for (const runtime of this.runtimes.values()) await runtime.deactivate?.();
    this.runtimes.clear();
  }
}
