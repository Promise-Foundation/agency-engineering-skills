/**
 * UI extension points. A plugin contributes routes, panels, resource views,
 * inspectors, dashboard cards, and commands -- *not* a fixed set of pages. The
 * shell owns stable locations (slots); the plugin owns what fills them.
 */

import type { ComponentType } from "react";
import type { AgencyHost } from "./services";
import type { AgencyResource, ResourceRef, ResourceType } from "./resources";

export type UiSlot =
  | "workspace.sidebar"
  | "workspace.main"
  | "workspace.inspector"
  | "resource.tabs"
  | "resource.actions"
  | "dashboard";

export interface ContextPredicate {
  selectionRequired?: boolean;
  resourceTypes?: ResourceType[];
  capability?: string;
}

/** Props every plugin-contributed component receives. */
export interface HostProps {
  host: AgencyHost;
}

export interface SlotProps extends HostProps {
  selection: ResourceRef | null;
}

export interface ResourceComponentProps extends HostProps {
  resource: AgencyResource;
}

export interface NavigationContribution {
  id: string;
  label: string;
  to: string;
  icon?: ComponentType;
  order?: number;
}

export interface RouteContribution {
  id: string;
  path: string;
  title: string;
  component: ComponentType<HostProps>;
  icon?: ComponentType;
  order?: number;
}

export interface PanelContribution {
  id: string;
  slot: UiSlot;
  component: ComponentType<SlotProps>;
  when?: ContextPredicate;
  order?: number;
}

export interface ResourceTypeContribution {
  type: ResourceType;
  label: string;
  icon?: ComponentType;
}

export interface ResourceViewContribution {
  id: string;
  resourceTypes: ResourceType[];
  component: ComponentType<ResourceComponentProps>;
  order?: number;
}

export interface InspectorContribution {
  id: string;
  resourceTypes: ResourceType[];
  component: ComponentType<ResourceComponentProps>;
  order?: number;
}

export interface DashboardCardContribution {
  id: string;
  title: string;
  component: ComponentType<HostProps>;
  order?: number;
}

export interface CommandContribution {
  id: string;
  title: string;
  when?: ContextPredicate;
  icon?: ComponentType;
}

export interface Contributions {
  navigation?: NavigationContribution[];
  routes?: RouteContribution[];
  commands?: CommandContribution[];
  workspacePanels?: PanelContribution[];
  resourceTypes?: ResourceTypeContribution[];
  resourceViews?: ResourceViewContribution[];
  inspectors?: InspectorContribution[];
  dashboardCards?: DashboardCardContribution[];
}
