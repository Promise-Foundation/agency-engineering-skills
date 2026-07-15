/**
 * The shell chrome: header (brand + activated skills), a left nav (built-in Home
 * plus contributed navigation), the router outlet, and the inspector. Every
 * plugin-owned region is filled purely from `host.contributions()` and the
 * resource services -- the shell hard-codes no skill.
 */

import { useEffect, useState } from "react";
import { BrowserRouter, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { Chip, EmptyState } from "@agency/ui-kit";
import type { ActivationResult, PluginHost } from "@agency/core";
import { bindNavigate } from "../runtime";
import { HostProvider, useHost } from "./host-context";
import { DashboardHome } from "./DashboardHome";
import { ResourceInspector } from "./ResourceInspector";
import { CommandPalette } from "./CommandPalette";
import { Toasts } from "./Toasts";

export function LoadingScreen() {
  return (
    <div className="boot">
      <div className="boot__spinner" aria-hidden="true" />
      <p className="boot__label">Activating skills…</p>
    </div>
  );
}

export function App({ host, activation }: { host: PluginHost; activation: ActivationResult }) {
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((isOpen) => !isOpen);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <HostProvider host={host}>
      <BrowserRouter>
        <NavBinder />
        <div className="shell">
          <Header onSearch={() => setPaletteOpen(true)} />
          {activation.failed.length > 0 ? <FailureBanner activation={activation} /> : null}
          <div className="shell__body">
            <Nav />
            <main className="shell__main">
              <Routes>
                <Route path="/" element={<DashboardHome />} />
                {host.contributions().routes.map((route) => {
                  const Component = route.component;
                  return (
                    <Route
                      key={route.id}
                      path={route.path}
                      element={<Component host={host.host} />}
                    />
                  );
                })}
                <Route
                  path="*"
                  element={
                    <EmptyState title="Not found" hint="No route matches this path." />
                  }
                />
              </Routes>
            </main>
            <aside className="shell__inspector">
              <ResourceInspector />
            </aside>
          </div>
        </div>
        <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
        <Toasts />
      </BrowserRouter>
    </HostProvider>
  );
}

/** Bridges the SDK NavigationService to react-router once the app has mounted. */
function NavBinder() {
  const navigate = useNavigate();
  useEffect(() => {
    bindNavigate((path) => navigate(path));
  }, [navigate]);
  return null;
}

function Header({ onSearch }: { onSearch: () => void }) {
  const host = useHost();
  const manifests = host.activatedManifests();
  return (
    <header className="shell__header">
      <div className="shell__brand">
        <span className="shell__brand-mark" aria-hidden="true">
          ◆
        </span>
        <span className="shell__brand-name">Agency Engineering</span>
      </div>
      <div className="shell__skills">
        {manifests.length === 0 ? (
          <span className="muted">No skills activated</span>
        ) : (
          manifests.map((manifest) => (
            <Chip key={manifest.id} tone="info">
              {manifest.name} v{manifest.version}
            </Chip>
          ))
        )}
      </div>
      <button type="button" className="btn" onClick={onSearch}>
        Search <kbd className="kbd">⌘K</kbd>
      </button>
    </header>
  );
}

function Nav() {
  const host = useHost();
  const navItems = host.contributions().navigation;
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `navlink${isActive ? " is-active" : ""}`;
  return (
    <nav className="shell__nav">
      <NavLink to="/" end className={linkClass}>
        Home
      </NavLink>
      {navItems.map((item) => (
        <NavLink key={item.id} to={item.to} className={linkClass}>
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

function FailureBanner({ activation }: { activation: ActivationResult }) {
  return (
    <div className="banner banner--error" role="alert">
      <strong>{activation.failed.length} skill(s) failed to activate.</strong>
      <span className="banner__detail">
        {activation.failed.map((failure) => `${failure.id}: ${failure.reason}`).join(" · ")}
      </span>
    </div>
  );
}
