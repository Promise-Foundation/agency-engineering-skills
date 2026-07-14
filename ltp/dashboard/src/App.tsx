import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DetailsPanel } from "./DetailsPanel";
import { Overview } from "./Overview";
import {
  basisValues,
  confidenceValues,
  indexModel,
  parseDashboard,
  reviewStatusValues,
  satisfactionValues,
  viewLabels,
  viewOrder,
  type Basis,
  type Confidence,
  type DashboardMeta,
  type DashboardModel,
  type Filters,
  type ReviewStatus,
  type Satisfaction,
  type TreeView,
} from "./model";

type Screen = "overview" | TreeView;

const TreeCanvas = lazy(() =>
  import("./TreeCanvas").then((module) => ({ default: module.TreeCanvas })),
);

function fingerprint(meta: DashboardMeta): string {
  return JSON.stringify([meta.model.exists, meta.model.modified_ns, meta.model.size]);
}

function FilterDimension<T extends string>({
  legend,
  values,
  active,
  onToggle,
}: {
  legend: string;
  values: T[];
  active: Set<T>;
  onToggle: (value: T) => void;
}) {
  return (
    <fieldset>
      <legend>{legend}</legend>
      {values.map((value) => (
        <label key={value}>
          <input
            type="checkbox"
            checked={active.has(value)}
            onChange={() => onToggle(value)}
          />
          <span>{value.replaceAll("_", " ")}</span>
        </label>
      ))}
    </fieldset>
  );
}

export default function App() {
  const [model, setModel] = useState<DashboardModel | null>(null);
  const [screen, setScreen] = useState<Screen>("overview");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [basis, setBasis] = useState<Set<Basis>>(() => new Set(basisValues));
  const [review, setReview] = useState<Set<ReviewStatus>>(() => new Set(reviewStatusValues));
  const [confidence, setConfidence] = useState<Set<Confidence>>(() => new Set(confidenceValues));
  const [satisfaction, setSatisfaction] = useState<Set<Satisfaction>>(
    () => new Set(satisfactionValues),
  );
  const [error, setError] = useState<string | null>(null);
  const [syncState, setSyncState] = useState<"loading" | "ready" | "updated" | "error">("loading");
  const fingerprintRef = useRef<string | null>(null);

  const loadData = useCallback(async (showUpdated = false) => {
    try {
      const response = await fetch("/api/dashboard", { cache: "no-store" });
      if (response.status === 404 || response.status === 204) {
        throw new Error(
          "No dashboard model yet. Run the ltp analysis to generate dashboard-model.json.",
        );
      }
      if (!response.ok) throw new Error(`/api/dashboard returned ${response.status}`);
      const payload = (await response.json()) as unknown;
      setModel(parseDashboard(payload));
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
        // The next successful poll restores the sync indicator via loadData.
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
  const filters = useMemo<Filters>(
    () => ({ basis, review_status: review, confidence, satisfaction }),
    [basis, review, confidence, satisfaction],
  );

  const chooseScreen = (next: Screen) => {
    setScreen(next);
    setSelectedId(null);
  };

  const toggleFilter = <T extends string>(
    value: T,
    set: Set<T>,
    update: (next: Set<T>) => void,
  ) => {
    const next = new Set(set);
    if (next.has(value)) {
      if (next.size > 1) next.delete(value); // keep at least one per dimension
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
        {error && (
          <button className="primary-button" onClick={() => void loadData()}>
            Try again
          </button>
        )}
      </main>
    );
  }

  const { health } = model;
  const activeView = screen === "overview" ? null : screen;
  const activeViewDefinition = activeView ? model.views[activeView] : null;
  const activeLabel = activeView ? viewLabels[activeView] : null;
  const selectedCount = basis.size + review.size + confidence.size + satisfaction.size;
  const totalCount =
    basisValues.length +
    reviewStatusValues.length +
    confidenceValues.length +
    satisfactionValues.length;

  return (
    <div className={`app-shell ${selectedId ? "has-details" : ""}`}>
      <header className="app-header">
        <button className="brand" type="button" onClick={() => chooseScreen("overview")}>
          <span className="brand-mark" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span>
            <strong>LTP</strong>
            <small>{model.project.name}</small>
          </span>
        </button>
        <div className="header-state">
          <details className="health-disclosure">
            <summary>
              <i className={`health-dot health-dot--${health.publishable ? "ok" : "blocked"}`} />
              Health
              <span className="health-counts">
                {health.counts.error > 0 && <em className="sev sev--error">{health.counts.error}</em>}
                {health.counts.warning > 0 && (
                  <em className="sev sev--warning">{health.counts.warning}</em>
                )}
                {health.counts.info > 0 && <em className="sev sev--info">{health.counts.info}</em>}
                {health.counts.error + health.counts.warning + health.counts.info === 0 && (
                  <em className="sev sev--ok">OK</em>
                )}
              </span>
            </summary>
            <div className="health-panel">
              <div className="health-panel__head">
                <strong>{health.publishable ? "Publishable" : "Blocked"}</strong>
                <span>
                  {health.counts.error} errors · {health.counts.warning} warnings ·{" "}
                  {health.counts.info} info
                </span>
              </div>
              {health.diagnostics.length === 0 ? (
                <p className="muted">No diagnostics were raised for this model.</p>
              ) : (
                <ul className="diagnostic-list">
                  {health.diagnostics.map((diagnostic, diagnosticIndex) => (
                    <li
                      key={`${diagnostic.code}-${diagnosticIndex}`}
                      className={`diagnostic diagnostic--${diagnostic.severity}`}
                    >
                      <div className="diagnostic__head">
                        <span className={`sev sev--${diagnostic.severity}`}>
                          {diagnostic.severity}
                        </span>
                        <code>{diagnostic.code}</code>
                      </div>
                      <strong>{diagnostic.title}</strong>
                      <p>{diagnostic.message}</p>
                      {diagnostic.target &&
                        (index.entities.has(diagnostic.target) ? (
                          <button
                            type="button"
                            className="diagnostic__target"
                            onClick={() => setSelectedId(diagnostic.target ?? null)}
                          >
                            {diagnostic.target} &rarr;
                          </button>
                        ) : (
                          <span className="diagnostic__target is-plain">{diagnostic.target}</span>
                        ))}
                      {diagnostic.hint && <small>{diagnostic.hint}</small>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </details>
          <span className={`sync-state sync-state--${syncState}`}>
            <i />
            {syncState === "updated"
              ? "Model updated"
              : syncState === "error"
                ? "Sync issue"
                : "Live model"}
          </span>
          <span className="read-only">Local · read only</span>
        </div>
      </header>

      <nav className="view-nav" aria-label="LTP views">
        <button
          className={screen === "overview" ? "is-active" : ""}
          onClick={() => chooseScreen("overview")}
        >
          <span>Overview</span>
          <small>The whole story</small>
        </button>
        {viewOrder.map((view) => (
          <button
            key={view}
            className={screen === view ? "is-active" : ""}
            onClick={() => chooseScreen(view)}
            disabled={model.views[view]?.empty ?? true}
          >
            <span>{viewLabels[view].short}</span>
            <small>{viewLabels[view].title}</small>
          </button>
        ))}
      </nav>

      <div className="app-content">
        {screen === "overview" ? (
          <Overview
            model={model}
            index={index}
            onSelect={setSelectedId}
            onExplore={() => chooseScreen("current-reality")}
          />
        ) : (
          <main className="tree-screen">
            <header className="tree-heading">
              <div>
                <span className="eyebrow">{activeLabel!.purpose}</span>
                <h1>{activeViewDefinition?.title ?? activeLabel!.title}</h1>
                <p>{activeLabel!.question}</p>
              </div>
              <details className="filter-disclosure">
                <summary>
                  Refine{" "}
                  <span>
                    {selectedCount}/{totalCount}
                  </span>
                </summary>
                <div className="filter-panel">
                  <FilterDimension
                    legend="Basis"
                    values={basisValues}
                    active={basis}
                    onToggle={(value) => toggleFilter(value, basis, setBasis)}
                  />
                  <FilterDimension
                    legend="Review"
                    values={reviewStatusValues}
                    active={review}
                    onToggle={(value) => toggleFilter(value, review, setReview)}
                  />
                  <FilterDimension
                    legend="Confidence"
                    values={confidenceValues}
                    active={confidence}
                    onToggle={(value) => toggleFilter(value, confidence, setConfidence)}
                  />
                  <FilterDimension
                    legend="Satisfaction"
                    values={satisfactionValues}
                    active={satisfaction}
                    onToggle={(value) => toggleFilter(value, satisfaction, setSatisfaction)}
                  />
                </div>
              </details>
            </header>
            <section className="tree-stage" aria-label={`${activeLabel!.purpose} diagram`}>
              <Suspense
                fallback={
                  <div className="canvas-empty">
                    <strong>Arranging the tree…</strong>
                  </div>
                }
              >
                <TreeCanvas
                  key={`${activeView}-${selectedId ? "detail" : "wide"}`}
                  model={model}
                  index={index}
                  view={activeView!}
                  filters={filters}
                  onSelect={setSelectedId}
                />
              </Suspense>
              <details className="legend-disclosure">
                <summary>How to read this</summary>
                <div>
                  <span>
                    <i className="status-mark status-mark--positive" />
                    Corroborated or confirmed
                  </span>
                  <span>
                    <i className="status-mark status-mark--neutral" />
                    Unreviewed or inferred
                  </span>
                  <span>
                    <i className="status-mark status-mark--negative" />
                    Disputed or invalidated
                  </span>
                  <span>
                    <i className="legend-gate" aria-hidden="true" />
                    Logic gate (AND / OR)
                  </span>
                  <small>
                    Dashed = necessary-for · red = conflict. Select a node to see evidence and
                    assumptions. Dragging changes only this view.
                  </small>
                </div>
              </details>
            </section>
          </main>
        )}
      </div>

      <DetailsPanel
        selectedId={selectedId}
        model={model}
        index={index}
        onSelect={setSelectedId}
        onClose={() => setSelectedId(null)}
      />
    </div>
  );
}
