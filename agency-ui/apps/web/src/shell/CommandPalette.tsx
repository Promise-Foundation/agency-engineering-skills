/**
 * The ⌘K / Ctrl-K palette. Two live sources merged into one list:
 *   - contributed commands (`host.contributions().commands`), run through
 *     `host.commands.execute(id)` with errors caught and toasted; and
 *   - a resource search (`host.resources.list({ search })`) whose hits select
 *     the resource (lighting up the inspector).
 * The shell has no idea what any command or resource is -- it only routes.
 */

import { useEffect, useMemo, useState } from "react";
import { DOMAIN_RESOURCE_TYPE, type AgencyResource } from "@agency/skill-sdk";
import { useHost } from "./host-context";

type Item =
  | { kind: "command"; key: string; id: string; title: string }
  | { kind: "resource"; key: string; resource: AgencyResource };

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const host = useHost();
  const [query, setQuery] = useState("");
  const [resources, setResources] = useState<AgencyResource[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);

  // Reset each time the palette opens.
  useEffect(() => {
    if (open) {
      setQuery("");
      setResources([]);
      setActiveIndex(0);
    }
  }, [open]);

  // Live resource search, cancellation-safe.
  useEffect(() => {
    if (!open) return;
    const needle = query.trim();
    if (!needle) {
      setResources([]);
      return;
    }
    let active = true;
    host.resources.list({ search: needle }).then(
      (list) => {
        if (active) setResources(list.slice(0, 8));
      },
      () => {
        if (active) setResources([]);
      },
    );
    return () => {
      active = false;
    };
  }, [query, open, host]);

  const commands = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return host
      .contributions()
      .commands.filter((command) => command.title.toLowerCase().includes(needle));
  }, [query, host]);

  const items = useMemo<Item[]>(
    () => [
      ...commands.map((command) => ({
        kind: "command" as const,
        key: `cmd:${command.id}`,
        id: command.id,
        title: command.title,
      })),
      ...resources.map((resource) => ({
        kind: "resource" as const,
        key: `res:${resource.type}:${resource.id}`,
        resource,
      })),
    ],
    [commands, resources],
  );

  async function runItem(item: Item): Promise<void> {
    if (item.kind === "command") {
      try {
        await host.commands.execute(item.id);
      } catch (error) {
        host.notifications.error(`Command "${item.title}" failed: ${String(error)}`);
      }
    } else if (item.resource.type === DOMAIN_RESOURCE_TYPE) {
      const params = new URLSearchParams({ domain: item.resource.id });
      host.navigation.navigate(`${host.navigation.currentPath()}?${params.toString()}`);
    } else {
      host.selection.select({ type: item.resource.type, id: item.resource.id });
    }
    onClose();
  }

  if (!open) return null;

  return (
    <div className="palette__overlay" onClick={onClose}>
      <div
        className="palette"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            onClose();
          } else if (event.key === "ArrowDown") {
            event.preventDefault();
            setActiveIndex((index) => Math.min(index + 1, Math.max(items.length - 1, 0)));
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActiveIndex((index) => Math.max(index - 1, 0));
          } else if (event.key === "Enter") {
            event.preventDefault();
            const item = items[activeIndex];
            if (item) void runItem(item);
          }
        }}
      >
        <input
          autoFocus
          className="palette__input"
          placeholder="Search commands and resources…"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setActiveIndex(0);
          }}
        />
        <div className="palette__list">
          {items.length === 0 ? <div className="palette__empty">No matches</div> : null}

          {commands.length > 0 ? <div className="palette__section">Commands</div> : null}
          {items.map((item, index) =>
            item.kind !== "command" ? null : (
              <button
                key={item.key}
                type="button"
                className={`palette__item${index === activeIndex ? " is-active" : ""}`}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => void runItem(item)}
              >
                <span className="palette__label">{item.title}</span>
                <span className="palette__hint">command</span>
              </button>
            ),
          )}

          {resources.length > 0 ? <div className="palette__section">Resources</div> : null}
          {items.map((item, index) =>
            item.kind !== "resource" ? null : (
              <button
                key={item.key}
                type="button"
                className={`palette__item${index === activeIndex ? " is-active" : ""}`}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => void runItem(item)}
              >
                <span className="palette__label">
                  {item.resource.title ?? item.resource.id}
                </span>
                <span className="palette__hint">{item.resource.type}</span>
              </button>
            ),
          )}
        </div>
      </div>
    </div>
  );
}
