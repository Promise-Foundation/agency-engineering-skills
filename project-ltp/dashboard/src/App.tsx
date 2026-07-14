import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { parse } from "yaml";
import { DetailsPanel } from "./DetailsPanel";
import { Overview } from "./Overview";
import {
  indexModel,
  validateModel,
  validateThroughput,
  viewLabels,
  viewOrder,
  type Confidence,
  type DashboardMeta,
  type EntityStatus,
  type LtpModel,
  type ThroughputData,
  type TreeView,
} from "./model";

type Screen = "overview" | TreeView;
const TreeCanvas = lazy(() =>
  import("./TreeCanvas").then((module) => ({ default: module.TreeCanvas })),
);
const allStatuses: EntityStatus[] = ["observed", "confirmed", "inferred", "provisional", "disputed"];
const allConfidences: Confidence[] = ["high", "medium", "low"];

function fingerprint(meta: DashboardMeta): string {
  return JSON.stringify([
    meta.model.exists,
    meta.model.modified_ns,
    meta.model.size,
    meta.throughput.exists,
    meta.throughput.modified_ns,
    meta.throughput.size,
  ]);
}

async function fetchText(url: string): Promise<string | null> {
  const response = await fetch(url, { cache: "no-store" });
  if (response.status === 204 || response.status === 404) return null;
  if (!response.ok) throw new Error(`${url} returned ${response.status}`);
  return response.text();
}

export default function App() {
  const [model, setModel] = useState<LtpModel | null>(null);
  const [throughput, setThroughput] = useState<ThroughputData | null>(null);
  const [screen, setScreen] = useState<Screen>("overview");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [statuses, setStatuses] = useState<Set<EntityStatus>>(new Set(allStatuses));
  const [confidences, setConfidences] = useState<Set<Confidence>>(new Set(allConfidences));
  const [error, setError] = useState<string | null>(null);
  const [syncState, setSyncState] = useState<"loading" | "ready" | "updated" | "error">("loading");
  const fingerprintRef = useRef<string | null>(null);

  const loadData = useCallback(async (showUpdated = false) => {
    try {
      const [modelText, throughputText] = await Promise.all([
        fetchText("/api/model"),
        fetchText("/api/throughput"),
      ]);
      if (!modelText) throw new Error("ltp/ltp-model.yaml was not found");
      const nextModel = validateModel(parse(modelText));
      const nextThroughput = throughputText
        ? validateThroughput(parse(throughputText))
        : null;
      setModel(nextModel);
      setThroughput(nextThroughput);
      setError(null);
      setSyncState(showUpdated ? "updated" : "ready");
      if (showUpdated) window.setTimeout(() => setSyncState("ready"), 1600);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load the model");
      setSyncState("error");
    }
  }, []);

  useEffect(() => {
    void loadData();
    let cancelled = false;
    const poll = async () => {
      try {
        const response = await fetch("/api/meta", { cache: "no-store" });
        if (!response.ok) return;
        const meta = (await response.json()) as DashboardMeta;
        const nextFingerprint = fingerprint(meta);
        if (fingerprintRef.current && fingerprintRef.current !== nextFingerprint) {
          await loadData(true);
        }
        fingerprintRef.current = nextFingerprint;
      } catch {
        // The next successful poll will restore the sync indicator via loadData.
      }
    };
    const timer = window.setInterval(() => {
      if (!cancelled) void poll();
    }, 2000);
    void poll();
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [loadData]);

  const index = useMemo(() => (model ? indexModel(model) : null), [model]);
  const selected = selectedId && index ? index.entities.get(selectedId) ?? null : null;

  const chooseScreen = (next: Screen) => {
    setScreen(next);
    setSelectedId(null);
  };

  const toggleFilter = <T extends string>(value: T, set: Set<T>, update: (next: Set<T>) => void) => {
    const next = new Set(set);
    if (next.has(value)) {
      if (next.size > 1) next.delete(value);
    } else {
      next.add(value);
    }
    update(next);
  };

  if (!model || !index) {
    return (
      <main className="load-state">
        <div className={error ? "load-mark load-mark--error" : "load-mark"}>{error ? "!" : ""}</div>
        <h1>{error ? "The model needs attention" : "Tracing the logic…"}</h1>
        <p>{error ?? "Loading the shared causal model and its evidence."}</p>
        {error && <button className="primary-button" onClick={() => void loadData()}>Try again</button>}
      </main>
    );
  }

  const activeView = screen === "overview" ? null : screen;
  const activeViewDefinition = activeView ? model.views[activeView] : null;
  const activeLabel = activeView ? viewLabels[activeView] : null;

  return (
    <div className={`app-shell ${selected ? "has-details" : ""}`}>
      <header className="app-header">
        <button className="brand" type="button" onClick={() => chooseScreen("overview")}>
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span><strong>Project LTP</strong><small>{model.project.name}</small></span>
        </button>
        <div className="header-state">
          <span className={`sync-state sync-state--${syncState}`}>
            <i />{syncState === "updated" ? "Model updated" : syncState === "error" ? "Sync issue" : "Live model"}
          </span>
          <span className="read-only">Local · read only</span>
        </div>
      </header>

      <nav className="view-nav" aria-label="LTP views">
        <button className={screen === "overview" ? "is-active" : ""} onClick={() => chooseScreen("overview")}>
          <span>Overview</span><small>The whole story</small>
        </button>
        {viewOrder.map((view) => (
          <button
            key={view}
            className={screen === view ? "is-active" : ""}
            onClick={() => chooseScreen(view)}
            disabled={!model.views[view]}
          >
            <span>{viewLabels[view].short}</span><small>{viewLabels[view].title}</small>
          </button>
        ))}
      </nav>

      <div className="app-content">
        {screen === "overview" ? (
          <Overview
            model={model}
            index={index}
            throughput={throughput}
            onSelect={setSelectedId}
            onExplore={() => chooseScreen("current-reality")}
          />
        ) : (
          <main className="tree-screen">
            <header className="tree-heading">
              <div>
                <span className="eyebrow">{activeLabel!.purpose}</span>
                <h1>{activeViewDefinition?.title ?? activeLabel!.title}</h1>
                <p>{activeViewDefinition?.purpose ?? activeLabel!.question}</p>
              </div>
              <details className="filter-disclosure">
                <summary>Refine <span>{statuses.size + confidences.size}/{allStatuses.length + allConfidences.length}</span></summary>
                <div className="filter-panel">
                  <fieldset>
                    <legend>Status</legend>
                    {allStatuses.map((status) => (
                      <label key={status}>
                        <input
                          type="checkbox"
                          checked={statuses.has(status)}
                          onChange={() => toggleFilter(status, statuses, setStatuses)}
                        />
                        <i className={`status-mark status-mark--${status}`} />{status}
                      </label>
                    ))}
                  </fieldset>
                  <fieldset>
                    <legend>Confidence</legend>
                    {allConfidences.map((confidence) => (
                      <label key={confidence}>
                        <input
                          type="checkbox"
                          checked={confidences.has(confidence)}
                          onChange={() => toggleFilter(confidence, confidences, setConfidences)}
                        />
                        {confidence}
                      </label>
                    ))}
                  </fieldset>
                </div>
              </details>
            </header>
            <section className="tree-stage" aria-label={`${activeLabel!.purpose} diagram`}>
              <Suspense fallback={<div className="canvas-empty"><strong>Arranging the tree…</strong></div>}>
                <TreeCanvas
                  key={`${activeView}-${selected ? "detail" : "wide"}`}
                  model={model}
                  index={index}
                  view={activeView!}
                  statuses={statuses}
                  confidences={confidences}
                  onSelect={setSelectedId}
                />
              </Suspense>
              <details className="legend-disclosure">
                <summary>How to read this</summary>
                <div>
                  <span><i className="status-mark status-mark--observed" />Observed or confirmed</span>
                  <span><i className="status-mark status-mark--inferred" />Inferred or provisional</span>
                  <span><i className="status-mark status-mark--disputed" />Disputed</span>
                  <small>Select a node to see evidence and assumptions. Dragging changes only this view.</small>
                </div>
              </details>
            </section>
          </main>
        )}
      </div>

      <DetailsPanel entity={selected} model={model} index={index} onClose={() => setSelectedId(null)} />
    </div>
  );
}
