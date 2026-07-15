import { useEffect, useState } from "react";
import type {
  AgencyHost,
  AgencyResource,
  HostProps,
  ResourceComponentProps,
  ResourceRef,
} from "@agency/skill-sdk";
import { Card, Chip, EmptyState, Field, Toolbar, type Tone } from "@agency/ui-kit";
import { LtpGraph } from "./graph";
import type { LtpClaim, LtpEntity, LtpModel } from "./mapping";

const MODEL_REF: ResourceRef = { type: "ltp.model", id: "model" };
const VIEW_ORDER = [
  "goal-tree",
  "current-reality",
  "evaporating-cloud",
  "future-reality",
  "prerequisite-tree",
  "transition-tree",
];

function useResource<T = unknown>(host: AgencyHost, ref: ResourceRef | null): AgencyResource<T> | null {
  const [resource, setResource] = useState<AgencyResource<T> | null>(null);
  useEffect(() => {
    let live = true;
    if (!ref) {
      setResource(null);
      return;
    }
    void host.resources.get(ref).then((value) => {
      if (live) setResource(value as AgencyResource<T> | null);
    });
    return () => {
      live = false;
    };
  }, [host, ref?.type, ref?.id]);
  return resource;
}

function severityTone(severity: string): Tone {
  return severity === "error" ? "negative" : severity === "warning" ? "warning" : "info";
}

export function LtpOverview({ host }: HostProps) {
  const model = useResource<LtpModel>(host, MODEL_REF);
  const [viewKey, setViewKey] = useState("current-reality");
  if (!model) return <EmptyState title="Loading the LTP model…" />;
  const data = model.data;
  const available = VIEW_ORDER.filter((key) => data.views?.[key] && !data.views[key].empty);
  const active = available.includes(viewKey) ? viewKey : (available[0] ?? viewKey);

  return (
    <div className="ltp-overview">
      <div className="ltp-overview__head">
        <div>
          <span className="ltp-eyebrow">Logical Thinking Processes</span>
          <h1>{data.project?.name ?? "LTP model"}</h1>
        </div>
        <Chip tone={data.health?.publishable ? "positive" : "negative"}>
          {data.health?.publishable ? "publishable" : "has errors"}
        </Chip>
      </div>

      <Toolbar>
        {available.map((key) => (
          <button
            key={key}
            className={`ltp-tab ${key === active ? "is-active" : ""}`}
            onClick={() => setViewKey(key)}
          >
            {data.views[key].title.split(" - ")[0]}
          </button>
        ))}
      </Toolbar>

      <LtpGraph
        model={data}
        viewKey={active}
        onSelect={(id) => {
          const gate = (data.gates ?? []).find((g) => g.id === id);
          if (gate) host.selection.select({ type: "ltp.claim", id: gate.claim });
          else if ((data.entities ?? []).some((e) => e.id === id))
            host.selection.select({ type: "ltp.entity", id });
        }}
      />
    </div>
  );
}

export function LtpHealthCard({ host }: HostProps) {
  const model = useResource<LtpModel>(host, MODEL_REF);
  if (!model) return <Card title="LTP model health">Loading…</Card>;
  const health = model.data.health;
  return (
    <Card
      title="LTP model health"
      subtitle={model.data.project?.name}
      actions={
        <button className="ltp-link" onClick={() => host.navigation.navigate("/ltp")}>
          Open ›
        </button>
      }
    >
      <Toolbar>
        <Chip tone={health.publishable ? "positive" : "negative"}>
          {health.publishable ? "publishable" : "invalid"}
        </Chip>
        <Chip tone="negative">{health.counts.error} errors</Chip>
        <Chip tone="warning">{health.counts.warning} warnings</Chip>
        <Chip tone="info">{health.counts.info} info</Chip>
      </Toolbar>
      <ul className="ltp-diaglist">
        {health.diagnostics.slice(0, 4).map((d, index) => (
          <li key={index}>
            <Chip tone={severityTone(d.severity)}>{d.code}</Chip>
            <button
              className="ltp-diaglist__target"
              disabled={!d.target}
              onClick={() => d.target && host.selection.select({ type: "ltp.entity", id: d.target })}
            >
              {d.message}
            </button>
          </li>
        ))}
        {health.diagnostics.length === 0 && <li className="ltp-muted">No diagnostics — clean.</li>}
      </ul>
    </Card>
  );
}

export function LtpEntityView({ resource }: ResourceComponentProps) {
  const entity = resource.data as LtpEntity;
  return (
    <div className="ltp-detail">
      <p className="ltp-statement">{entity.statement}</p>
      <Field label="Kind">{entity.kind.replace(/_/g, " ")}</Field>
      <Field label="Basis">{entity.basis ?? "-"}</Field>
      <Field label="Review">{entity.review_status ?? "-"}</Field>
      <Field label="Confidence">{entity.confidence ?? "-"}</Field>
      <Field label="Satisfaction">{entity.satisfaction ?? "-"}</Field>
      <Field label="Influence">{entity.influence ?? "-"}</Field>
      {entity.evidence_refs && entity.evidence_refs.length > 0 && (
        <Field label="Evidence">{entity.evidence_refs.join(", ")}</Field>
      )}
    </div>
  );
}

export function LtpClaimView({ host, resource }: ResourceComponentProps) {
  const claim = resource.data as LtpClaim;
  const clr = claim.clr ?? {};
  return (
    <div className="ltp-detail">
      <p className="ltp-flow">
        {(claim.premises ?? []).join(` ${(claim.operator ?? "single").toUpperCase()} `)} ⇒ {claim.conclusion}
      </p>
      <Field label="Logic status">
        <Chip tone={claim.logic_status === "scrutinized" ? "positive" : claim.logic_status === "contradicted" ? "negative" : "neutral"}>
          {claim.logic_status ?? "candidate"}
        </Chip>
      </Field>
      {claim.verification?.hypothesis_ref && (
        <Field label="Verified by">
          <button
            className="ltp-link"
            onClick={() =>
              host.selection.select({ type: "hypothesis", id: claim.verification!.hypothesis_ref })
            }
          >
            {claim.verification.hypothesis_ref} ›
          </button>
        </Field>
      )}
      <div className="ltp-clr">
        {Object.entries(clr).map(([name, check]) => (
          <div key={name} className="ltp-clr__row">
            <span>{name.replace(/_/g, " ")}</span>
            <Chip tone={check.result === "pass" ? "positive" : check.result === "fail" ? "negative" : "neutral"}>
              {check.result}
            </Chip>
          </div>
        ))}
      </div>
    </div>
  );
}

export function LtpModelView({ resource }: ResourceComponentProps) {
  const model = resource.data as LtpModel;
  return (
    <div className="ltp-detail">
      <Field label="Goal">{model.project?.goal ?? "-"}</Field>
      <Field label="Mode">{model.project?.analysis_mode ?? "-"}</Field>
      <Field label="Entities">{model.entities?.length ?? 0}</Field>
      <Field label="Claims">{model.causal_claims?.length ?? 0}</Field>
      <Field label="Publishable">{model.health?.publishable ? "yes" : "no"}</Field>
    </div>
  );
}
