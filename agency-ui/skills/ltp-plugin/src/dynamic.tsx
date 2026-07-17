import { useEffect, useMemo, useState } from "react";
import type { AgencyHost, ResourceComponentProps } from "@agency/skill-sdk";
import { Card, Chip, EmptyState, Field, type Tone } from "@agency/ui-kit";
import type {
  LtpLearningEvent,
  LtpModel,
  LtpPrediction,
  LtpPredictionEvaluation,
} from "./mapping";
import { scopedLtpId } from "./mapping";

export type DynamicSurface = "model" | "history" | "predictions" | "perspectives" | "attention";

export const DYNAMIC_SURFACES: { id: DynamicSurface; label: string }[] = [
  { id: "model", label: "Current model" },
  { id: "history", label: "Learning history" },
  { id: "predictions", label: "Predictions" },
  { id: "perspectives", label: "Perspectives" },
  { id: "attention", label: "Attention" },
];

function human(value: string | null | undefined): string {
  return (value ?? "—").replace(/[_-]/g, " ");
}

function tone(value?: string | null): Tone {
  if (["supported", "observed", "scrutinized", "complete", "kept"].includes(value ?? ""))
    return "positive";
  if (["contradicted", "falsified", "absent", "broken"].includes(value ?? "")) return "negative";
  if (["inconclusive", "disputed", "partial", "overdue"].includes(value ?? "")) return "warning";
  return "neutral";
}

function localId(scoped: string): string {
  return scoped.includes("::") ? scoped.slice(scoped.lastIndexOf("::") + 2) : scoped;
}

export function HistoryView({ model }: { model: LtpModel }) {
  const events = model.learning_history?.events ?? [];
  const first = events[0]?.occurred_at.slice(0, 10) ?? model.as_of ?? "";
  const last = model.as_of ?? events.at(-1)?.occurred_at.slice(0, 10) ?? "";
  const [cursor, setCursor] = useState(last);
  const [from, setFrom] = useState(first);
  const [to, setTo] = useState(last);
  const [playing, setPlaying] = useState(false);

  const orderedDates = useMemo(
    () => [...new Set(events.map((event) => event.occurred_at.slice(0, 10)))],
    [events],
  );
  useEffect(() => {
    if (!playing || orderedDates.length === 0) return;
    const timer = window.setInterval(() => {
      setCursor((current) => {
        const index = Math.max(0, orderedDates.indexOf(current));
        if (index >= orderedDates.length - 1) {
          setPlaying(false);
          return orderedDates.at(-1) ?? current;
        }
        return orderedDates[index + 1];
      });
    }, 900);
    return () => window.clearInterval(timer);
  }, [playing, orderedDates]);

  const asOf = events.filter((event) => !cursor || event.occurred_at.slice(0, 10) <= cursor);
  const diff = events.filter((event) => {
    const date = event.occurred_at.slice(0, 10);
    return (!from || date > from) && (!to || date <= to);
  });

  if (events.length === 0)
    return (
      <EmptyState
        title="No learning-history records are projected yet"
        hint="Generate the dashboard with an explicit as-of date or supply git, assessment, and research snapshots to the history projector."
      />
    );
  return (
    <div className="ltp-dynamic" data-testid="learning-history-view">
      <Card
        title="History cursor"
        subtitle={cursor ? `Viewing the semantic model as of ${cursor}` : "Current model"}
        actions={
          <button type="button" className="ltp-link" onClick={() => setPlaying((value) => !value)}>
            {playing ? "Pause" : "Play history"}
          </button>
        }
      >
        <label className="ltp-control">
          As of
          <input
            data-testid="history-cursor"
            type="date"
            value={cursor}
            onChange={(event) => setCursor(event.target.value)}
          />
        </label>
        <p className="ltp-muted">{asOf.length} semantic acts are present at this cursor.</p>
        <ol className="ltp-timeline" data-testid="history-asof">
          {asOf.map((event) => <HistoryEntry key={event.id} event={event} />)}
        </ol>
      </Card>

      <Card title="Semantic difference" subtitle="Model changes, not YAML lines">
        <div className="ltp-control-row">
          <label className="ltp-control">From <input type="date" value={from} onChange={(event) => setFrom(event.target.value)} /></label>
          <label className="ltp-control">To <input type="date" value={to} onChange={(event) => setTo(event.target.value)} /></label>
        </div>
        <ol className="ltp-timeline" data-testid="history-diff">
          {diff.map((event) => <HistoryEntry key={event.id} event={event} />)}
          {diff.length === 0 && <li className="ltp-muted">No semantic changes in this interval.</li>}
        </ol>
      </Card>
    </div>
  );
}

function HistoryEntry({ event }: { event: LtpLearningEvent }) {
  return (
    <li data-testid={`history-entry-${event.id}`}>
      <time>{event.occurred_at.slice(0, 10)}</time>
      <div>
        <strong>{event.summary}</strong>
        <span>{event.actor ? `${event.actor} · ` : ""}{event.reason ?? event.source}</span>
        <details>
          <summary>Underlying record</summary>
          <code>{event.source}</code>
          {event.previous !== undefined && <pre>{JSON.stringify(event.previous, null, 2)}</pre>}
          {event.current !== undefined && <pre>{JSON.stringify(event.current, null, 2)}</pre>}
        </details>
      </div>
    </li>
  );
}

function observedValue(model: LtpModel, prediction: LtpPrediction): string {
  const observations = (model.observations ?? []).filter((item) => item.prediction === prediction.id);
  const latest = observations.sort((a, b) => a.observed_at.localeCompare(b.observed_at)).at(-1);
  if (!latest && prediction.implementation_status === "complete" && prediction.review_by) return "Effect absent";
  if (!latest && prediction.implementation_status === "complete" && prediction.review_by)
    return "Effect absent";
  if (!latest) return "No observation";
  if (latest.change_percent != null) return `${latest.change_percent}%`;
  if (latest.value != null) return String(latest.value);
  return human(latest.result);
}

function expectedValue(prediction: LtpPrediction): string {
  if (prediction.expected_change_percent != null) return `${prediction.expected_change_percent}%`;
  return prediction.statement;
}

export function PredictionsView({ model, host, domain }: { model: LtpModel; host: AgencyHost; domain: string }) {
  const evaluations = new Map((model.prediction_evaluations ?? []).map((item) => [item.prediction, item]));
  if (!(model.predicted_effects ?? []).length)
    return <EmptyState title="No causal-outcome predictions are registered" />;
  return (
    <div className="ltp-predictions" data-testid="prediction-panel">
      {(model.predicted_effects ?? []).map((prediction) => {
        const evaluation = evaluations.get(prediction.id);
        const claim = model.causal_claims.find((item) => item.id === prediction.source_claim);
        return (
          <Card
            key={prediction.id}
            title={`${prediction.id} · ${prediction.indicator ?? "predicted effect"}`}
            subtitle={prediction.statement}
            actions={<Chip tone={tone(evaluation?.result)}>{human(evaluation?.result ?? "untested")}</Chip>}
          >
            <div className="ltp-comparison">
              <div data-testid="prediction-predicted"><span>Predicted</span><strong>{expectedValue(prediction)}</strong><small>by {prediction.expected_by ?? prediction.review_by ?? "unscheduled"}</small></div>
              <div data-testid="prediction-observed"><span>Observed</span><strong>{observedValue(model, prediction)}</strong><small>admitted operational fact</small></div>
              <div data-testid="prediction-interpretation"><span>Interpretation</span><strong>{human(evaluation?.result ?? "not evaluated")}</strong><small>{evaluation?.explanation ?? "No derived evaluation"}</small></div>
            </div>
            <div className="ltp-dimensions">
              <Field label="Implementation"><span data-testid="status-implementation">{human(prediction.implementation_status)}</span></Field>
              <Field label="Implementation fidelity">{prediction.implementation_fidelity == null ? "not assessed" : `${Math.round(prediction.implementation_fidelity * 100)}%`}</Field>
              <Field label="Logical (CLR)"><span>{human(claim?.logic_status)}</span></Field>
              <Field label="Empirical conclusion"><span data-testid="prediction-conclusion">{human(claim?.verification?.empirical_status ?? "not tested")}</span></Field>
            </div>
            <button type="button" className="ltp-link" onClick={() => host.selection.select({ type: "ltp.prediction", id: scopedLtpId(domain, prediction.id) })}>Inspect prediction ›</button>
            <button type="button" className="ltp-link" onClick={() => host.selection.select({ type: "ltp.claim", id: scopedLtpId(domain, prediction.source_claim) })}>Inspect causal claim ›</button>
          </Card>
        );
      })}
    </div>
  );
}

interface PromisifyExplorer {
  assessments?: { id: string; assessor: string; observedAt: string; promise: string; effectiveDomain: string; verdict: string; rationale?: string | null; evidence?: unknown[] }[];
  views?: { name: string; observer: string; conflictPolicy: string }[];
  trust?: { view: string; conflictPolicy: string; selectedAssessmentIds: string[] }[];
}

export function PerspectivesView({ host, model, domain }: { host: AgencyHost; model: LtpModel; domain: string }) {
  const [explorer, setExplorer] = useState<PromisifyExplorer | null>(null);
  const [view, setView] = useState("");
  useEffect(() => {
    let live = true;
    void host.resources.get({ type: "norms.model", id: "model" }).then((resource) => {
      if (!live) return;
      const data = (resource?.data ?? null) as PromisifyExplorer | null;
      setExplorer(data);
      setView((current) => current || data?.views?.[0]?.name || "all-assessors");
    });
    return () => { live = false; };
  }, [host]);
  const knownSubjects = new Set([
    ...model.causal_claims.map((claim) => claim.id),
    ...(model.semantic_relations ?? []).map((relation) => relation.id),
  ]);
  const assessments = (explorer?.assessments ?? []).filter((item) =>
    item.effectiveDomain.startsWith(domain) || [...knownSubjects].some((subject) => item.promise.includes(subject)),
  );
  const selected = explorer?.trust?.find((entry) => entry.view === view)?.selectedAssessmentIds;
  const visible = selected?.length ? assessments.filter((item) => selected.includes(item.id)) : assessments;
  const policy = explorer?.views?.find((item) => item.name === view)?.conflictPolicy ?? "preserve-disagreement";
  return (
    <div className="ltp-dynamic" data-testid="perspective-view">
      <Card title="Stakeholder perspectives" subtitle={`Conflict policy: ${human(policy)}`}>
        <label className="ltp-control">Observer view
          <select data-testid="observer-view-select" value={view} onChange={(event) => setView(event.target.value)}>
            {(explorer?.views ?? []).map((item) => <option key={item.name}>{item.name}</option>)}
            {!(explorer?.views ?? []).length && <option>all-assessors</option>}
          </select>
        </label>
        <div className="ltp-assessments">
          {visible.map((item) => (
            <article key={item.id} data-testid={`assessor-position-${item.assessor}`}>
              <div><strong>{item.assessor}</strong><Chip tone={tone(item.verdict)}>{human(item.verdict)}</Chip></div>
              <p>{item.rationale ?? "No reservation recorded."}</p>
              <small>{item.promise} · {item.observedAt}</small>
              {item.verdict === "disputed" && <small>retained minority hypothesis · available for reconsideration</small>}
            </article>
          ))}
          {visible.length === 0 && <p className="ltp-muted">No attributable assessments correlate to this domain yet. The absence is retained rather than rendered as consensus.</p>}
        </div>
      </Card>
    </div>
  );
}

export function AttentionView({ model, host, domain }: { model: LtpModel; host: AgencyHost; domain: string }) {
  const obligations = model.learning_obligations ?? [];
  return (
    <div className="ltp-dynamic" data-testid="attention-queue">
      <Card title="Attention required" subtitle={`Learning obligations as of ${model.as_of ?? "an unspecified date"}`}>
        {obligations.length === 0 ? (
          <p>No overdue learning obligations. This asserts operational currency only; logical consistency is reported separately.</p>
        ) : (
          <ul className="ltp-obligations">
            {obligations.map((item) => (
              <li key={item.id} data-testid={`attention-item-${item.kind}`}>
                <Chip tone={item.blocking ? "negative" : "warning"}>{human(item.kind)}</Chip>
                <div><strong>{item.target}</strong><span>Due {item.due_at}{item.owner ? ` · ${item.owner}` : ""}</span><p>{item.next_action}</p></div>
                <button type="button" className="ltp-link" onClick={() => host.selection.select({ type: "ltp.prediction", id: scopedLtpId(domain, item.target) })}>Open ›</button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

export function LifecycleInspector({ host, resource }: ResourceComponentProps) {
  const [model, setModel] = useState<LtpModel | null>(null);
  useEffect(() => {
    let live = true;
    if (!resource.domain) return;
    void host.resources.list({ type: "ltp.model", domain: resource.domain }).then((items) => {
      if (live) setModel((items[0]?.data ?? null) as LtpModel | null);
    });
    return () => { live = false; };
  }, [host, resource.domain]);
  const subject = localId(resource.id);
  const events = (model?.learning_history?.events ?? []).filter((event) => event.subject === subject);
  return (
    <Card title="Lifecycle" subtitle="Derived sequence, not an authored badge">
      <ol className="ltp-lifecycle" data-testid={`lifecycle-${subject}`}>
        {events.map((event) => <HistoryEntry key={event.id} event={event} />)}
        {events.length === 0 && <li className="ltp-muted">No lifecycle acts are projected for this record yet.</li>}
      </ol>
    </Card>
  );
}

export function PredictionInspector({ resource }: ResourceComponentProps) {
  const prediction = resource.data as LtpPrediction & { evaluation?: LtpPredictionEvaluation; observations?: { id: string; observed_at: string; result?: string; change_percent?: number | null }[] };
  return (
    <div className="ltp-detail">
      <p className="ltp-statement">{prediction.statement}</p>
      <Field label="Expected change">{prediction.expected_change_percent == null ? "—" : `${prediction.expected_change_percent}%`}</Field>
      <Field label="Review by">{prediction.review_by ?? "—"}</Field>
      <Field label="Implementation">{human(prediction.implementation_status)}</Field>
      <Field label="Outcome interpretation"><Chip tone={tone(prediction.evaluation?.result)}>{human(prediction.evaluation?.result ?? "not evaluated")}</Chip></Field>
    </div>
  );
}
