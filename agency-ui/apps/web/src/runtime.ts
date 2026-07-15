/** Bridges the SDK NavigationService to react-router, which only exists after
 * the app mounts. The shell binds the real navigate() via <NavBinder/>. */

import type { NavigationService } from "@agency/skill-sdk";

let navigateFn: (path: string) => void = () => {};

export function bindNavigate(fn: (path: string) => void): void {
  navigateFn = fn;
}

export const navigation: NavigationService = {
  navigate: (path) => navigateFn(path),
  currentPath: () => window.location.pathname,
};
