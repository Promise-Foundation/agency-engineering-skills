/**
 * The shell chrome: header, domain hierarchy, contributed skill navigation,
 * router outlet, and inspector. Promisify supplies domains through the shared
 * resource seam; every plugin-owned region still comes from contributions.
 */

import { useEffect, useMemo, useState } from "react";
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { EmptyState } from "@agency/ui-kit";
import type { ActivationResult, PluginHost } from "@agency/core";
import {
  DOMAIN_RESOURCE_TYPE,
  type AgencyResource,
  type DomainResourceData,
  type ResourceRef,
} from "@agency/skill-sdk";
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
        <Workspace host={host} activation={activation} onSearch={() => setPaletteOpen(true)} />
        <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
        <Toasts />
      </BrowserRouter>
    </HostProvider>
  );
}

function Workspace({
  host,
  activation,
  onSearch,
}: {
  host: PluginHost;
  activation: ActivationResult;
  onSearch: () => void;
}) {
  const domains = useDomains(host);
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedDomain = searchParams.get("domain");
  const activeDomain = useMemo(
    () =>
      domains.find((domain) => domain.id === requestedDomain) ??
      domains.find((domain) => domain.data.parent === null) ??
      domains[0] ??
      null,
    [domains, requestedDomain],
  );
  const domainRef: ResourceRef | null = activeDomain
    ? { type: DOMAIN_RESOURCE_TYPE, id: activeDomain.id }
    : null;

  useEffect(() => {
    if (!activeDomain || requestedDomain === activeDomain.id) return;
    const next = new URLSearchParams(searchParams);
    next.set("domain", activeDomain.id);
    setSearchParams(next, { replace: true });
  }, [activeDomain, requestedDomain, searchParams, setSearchParams]);

  const selectDomain = (path: string) => {
    const next = new URLSearchParams(searchParams);
    next.set("domain", path);
    setSearchParams(next);
  };

  return (
    <div className="shell" data-testid="agency-shell">
      <Header domain={domainRef} onSearch={onSearch} />
      {activation.failed.length > 0 ? <FailureBanner activation={activation} /> : null}
      <div className="shell__body">
        <Nav domains={domains} domain={domainRef} onSelectDomain={selectDomain} />
        <main className="shell__main">
          <Routes>
            <Route path="/" element={<DashboardHome domain={domainRef} />} />
            {host.contributions().routes.map((route) => {
              const Component = route.component;
              return (
                <Route
                  key={route.id}
                  path={route.path}
                  element={<Component host={host.host} domain={domainRef} />}
                />
              );
            })}
            <Route
              path="*"
              element={<EmptyState title="Not found" hint="No route matches this path." />}
            />
          </Routes>
        </main>
        <aside className="shell__inspector">
          <ResourceInspector />
        </aside>
      </div>
    </div>
  );
}

function useDomains(host: PluginHost): AgencyResource<DomainResourceData>[] {
  const [domains, setDomains] = useState<AgencyResource<DomainResourceData>[]>([]);
  useEffect(() => {
    let active = true;
    void host.resources.list({ type: DOMAIN_RESOURCE_TYPE }).then((resources) => {
      if (active) setDomains(orderDomains(resources as AgencyResource<DomainResourceData>[]));
    });
    return () => {
      active = false;
    };
  }, [host]);
  return domains;
}

function orderDomains(
  domains: AgencyResource<DomainResourceData>[],
): AgencyResource<DomainResourceData>[] {
  const byPath = new Map(domains.map((domain) => [domain.id, domain]));
  const ordered: AgencyResource<DomainResourceData>[] = [];
  const seen = new Set<string>();
  const visit = (path: string) => {
    if (seen.has(path)) return;
    const domain = byPath.get(path);
    if (!domain) return;
    seen.add(path);
    ordered.push(domain);
    domain.data.children.forEach(visit);
  };
  domains.filter((domain) => domain.data.parent === null).forEach((domain) => visit(domain.id));
  domains.forEach((domain) => visit(domain.id));
  return ordered;
}

/** Bridges the SDK NavigationService to react-router once the app has mounted. */
function NavBinder() {
  const navigate = useNavigate();
  useEffect(() => {
    bindNavigate((path) => navigate(path));
  }, [navigate]);
  return null;
}

function Header({ domain, onSearch }: { domain: ResourceRef | null; onSearch: () => void }) {
  return (
    <header className="shell__header">
      <Link className="shell__brand" to={{ pathname: "/", search: domainSearch(domain) }}>
        <span className="shell__brand-mark" aria-hidden="true">
          ◆
        </span>
        <span className="shell__brand-name">Agency Engineering</span>
      </Link>
      <div className="shell__context">
        <span className="shell__context-label">Domain</span>
        <code>{domain?.id ?? "Loading…"}</code>
      </div>
      <button type="button" className="btn" onClick={onSearch}>
        Search <kbd className="kbd">⌘K</kbd>
      </button>
    </header>
  );
}

function Nav({
  domains,
  domain,
  onSelectDomain,
}: {
  domains: AgencyResource<DomainResourceData>[];
  domain: ResourceRef | null;
  onSelectDomain: (path: string) => void;
}) {
  const host = useHost();
  const navItems = host.contributions().navigation;
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `navlink${isActive ? " is-active" : ""}`;
  return (
    <nav className="shell__nav">
      <section className="navsection navsection--domains" aria-labelledby="domains-heading">
        <h2 id="domains-heading" className="navsection__title">
          Domains
        </h2>
        <div className="domain-tree">
          {domains.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`domain-link${item.id === domain?.id ? " is-active" : ""}`}
              style={{ paddingLeft: 10 + item.data.depth * 14 }}
              onClick={() => onSelectDomain(item.id)}
              title={item.id}
            >
              <span className="domain-link__name">{domainLabel(item.id)}</span>
              <span className="domain-link__count">{item.data.effectivePromiseCount ?? 0}</span>
            </button>
          ))}
        </div>
      </section>
      <section className="navsection navsection--skills" aria-labelledby="skills-heading">
        <h2 id="skills-heading" className="navsection__title">
          Skills
        </h2>
        {navItems.map((item) => (
          <NavLink
            key={item.id}
            to={{ pathname: item.to, search: domainSearch(domain) }}
            className={linkClass}
          >
            {item.label}
          </NavLink>
        ))}
      </section>
    </nav>
  );
}

function domainSearch(domain: ResourceRef | null): string {
  if (!domain) return "";
  const params = new URLSearchParams({ domain: domain.id });
  return `?${params.toString()}`;
}

function domainLabel(path: string): string {
  if (path === "/") return "/";
  return path.split("/").filter(Boolean).at(-1) ?? path;
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
