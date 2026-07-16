import { useEffect, useState } from "react";
import type {
  AgencyHost,
  AgencyResource,
  HostProps,
  ResourceComponentProps,
} from "@agency/skill-sdk";
import { Card, Chip, EmptyState, Field, Toolbar, type Tone } from "@agency/ui-kit";
import { LtpGraph } from "./graph";
import { scopedLtpId, type LtpClaim, type LtpEntity, type LtpModel } from "./mapping";

const VIEW_ORDER = [
  "goal-tree",
  "current-reality",
  "evaporating-cloud",
  "future-reality",
  "prerequisite-tree",
  "transition-tree",
];

function useDomainModel(
  host: AgencyHost,
  domain: string | null,
): { model: AgencyResource<LtpModel> | null; loading: boolean } {
  const [resource, setResource] = useState<AgencyResource<LtpModel> | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let live = true;
    if (!domain) {
      setResource(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    void host.resources.list({ type: "ltp.model", domain }).then((items) => {
      if (!live) return;
      setResource((items[0] ?? null) as AgencyResource<LtpModel> | null);
      setLoading(false);
    });
    return () => {
      live = false;
    };
  }, [host, domain]);
  return { model: resource, loading };
}

function severityTone(severity: string): Tone {
  return severity === "error" ? "negative" : severity === "warning" ? "warning" : "info";
}

export function LtpOverview({ host, domain }: HostProps) {
  const domainPath = domain?.id ?? null;
  const { model, loading } = useDomainModel(host, domainPath);
  const [viewKey, setViewKey] = useState("current-reality");
  if (loading) return <EmptyState title="Loading the LTP model…" />;
  if (!model) {
    return (
      <EmptyState
        title={`LTP has not been generated for ${domainPath ?? "this domain"}`}
        hint="Generate an LTP artifact for this domain before its trees can be shown."
      />
    );
  }
  const data = model.data;
  const available = VIEW_ORDER.filter((key) => data.views?.[key] && !data.views[key].empty);
  const active = available.includes(viewKey) ? viewKey : (available[0] ?? viewKey);

  return (
    <div className="ltp-overview">
      <div className="ltp-overview__head">
        <div>
          <span className="ltp-eyebrow">
            Logical Thinking Processes · working domain {domainPath ?? "not selected"}
          </span>
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
          if (gate && domainPath)
            host.selection.select({ type: "ltp.claim", id: scopedLtpId(domainPath, gate.claim) });
          else if ((data.entities ?? []).some((e) => e.id === id))
            host.selection.select({
              type: "ltp.entity",
              id: scopedLtpId(domainPath ?? "/", id),
            });
        }}
      />
    </div>
  );
}

export function LtpHealthCard({ host, domain }: HostProps) {
  const domainPath = domain?.id ?? null;
  const { model, loading } = useDomainModel(host, domainPath);
  if (loading) return <Card title="LTP model health">Loading…</Card>;
  if (!model)
    return (
      <Card title="LTP model health" subtitle={domainPath}>
        Not generated for this domain.
      </Card>
    );
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
              onClick={() =>
                d.target &&
                domainPath &&
                host.selection.select({ type: "ltp.entity", id: scopedLtpId(domainPath, d.target) })
              }
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
              host.selection.select({
                type: "hypothesis",
                id: `${encodeURIComponent(resource.domain ?? "/")}::${claim.verification!.hypothesis_ref}`,
              })
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
