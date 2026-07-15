/**
 * Boot. Construct the host, register the installed plugins, activate them all,
 * then mount the shell. A loading screen is shown while activation is in flight;
 * activation failures are surfaced by the shell (they never block boot -- one
 * bad plugin cannot take down the others).
 */

import { createRoot } from "react-dom/client";
import { PluginHost } from "@agency/core";
import "@agency/ui-kit/styles.css";
import "./styles.css";
import { navigation } from "./runtime";
import { toastNotifications } from "./shell/notifications";
import { installedPlugins } from "./plugins";
import { App, LoadingScreen } from "./shell/App";

async function boot(): Promise<void> {
  const host = new PluginHost({ navigation, notifications: toastNotifications });
  installedPlugins.forEach((plugin) => host.register(plugin));

  const container = document.getElementById("root");
  if (!container) throw new Error("missing #root element");
  const root = createRoot(container);

  root.render(<LoadingScreen />);
  const activation = await host.activateAll();
  root.render(<App host={host} activation={activation} />);
}

void boot();
