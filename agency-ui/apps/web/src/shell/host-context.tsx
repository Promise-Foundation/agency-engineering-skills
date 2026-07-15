/**
 * The host React context. The whole shell reads the live {@link PluginHost}
 * through {@link useHost}; selection is exposed via {@link useSelection}, an
 * external store bridged into React with `useSyncExternalStore` so any code
 * (a command, a related-ref click, a plugin) that calls `host.selection.select`
 * re-renders the inspector.
 */

import { createContext, useCallback, useContext, useSyncExternalStore } from "react";
import type { ReactNode } from "react";
import type { PluginHost } from "@agency/core";
import type { ResourceRef } from "@agency/skill-sdk";

const HostContext = createContext<PluginHost | null>(null);

export function HostProvider({
  host,
  children,
}: {
  host: PluginHost;
  children: ReactNode;
}) {
  return <HostContext.Provider value={host}>{children}</HostContext.Provider>;
}

/** The shell-facing host. Plugin components instead receive the narrow `host.host`. */
export function useHost(): PluginHost {
  const host = useContext(HostContext);
  if (!host) throw new Error("useHost must be used within <HostProvider>");
  return host;
}

/** Current selection, kept in sync with `host.selection` via useSyncExternalStore. */
export function useSelection(): ResourceRef | null {
  const host = useHost();
  const subscribe = useCallback(
    (onStoreChange: () => void) => host.selection.subscribe(() => onStoreChange()),
    [host],
  );
  const getSnapshot = useCallback(() => host.selection.current(), [host]);
  return useSyncExternalStore(subscribe, getSnapshot);
}
