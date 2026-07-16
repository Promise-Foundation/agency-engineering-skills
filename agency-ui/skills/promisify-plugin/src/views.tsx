/** Read-only views for the Promisify explorer: the dashboard card and
 * the promise inspector, plus the shared model hook and formatting helpers the
 * workspace reuses. Nothing here recomputes inheritance, assessment selection,
 * or trust — it renders exactly what `norms.py explorer` already produced. */

import { useEffect, useState } from "react";
import type { AgencyHost, HostProps, ResourceComponentProps } from "@agency/skill-sdk";
import { Card, Chip, Field, Toolbar, type Tone } from "@agency/ui-kit";
import { MODEL_TYPE } from "./mapping";
import type { Explorer, Promise as PromiseModel, Verdict } from "./mapping";

/** Load the single precomputed explorer model (the whole graph is one resource). */
export function useExplorer(host: AgencyHost): Explorer | null {
  const [model, setModel] = useState<Explorer | null>(null);
  useEffect(() => {
    let live = true;
    void host.resources.get({ type: MODEL_TYPE, id: "model" }).then((resource) => {
      if (live) setModel((resource?.data ?? null) as Explorer | null);
    });
    return () => {
      live = false;
    };
  }, [host]);
  return model;
}

/** 0..1 → "67%"; null/undefined → "n/a". */
export function pct(value: number | null | undefined): string {
  return value == null ? "n/a" : `${Math.round(value * 100)}%`;
}

/** First 7 characters of a revision hash. */
export function shortRev(revision: string | null | undefined): string {
  return revision ? revision.slice(0, 7) : "—";
}

/** "agent/static-analysis" → "Static analysis". */
export function humanizeAssessor(assessor: string): string {
  const tail = assessor.includes("/") ? assessor.slice(assessor.lastIndexOf("/") + 1) : assessor;
  const spaced = tail.replace(/[-_]/g, " ").trim();
  return spaced ? spaced.charAt(0).toUpperCase() + spaced.slice(1) : assessor;
}

/** Resolved-verdict → chip tone. unknown / not_applicable read as neutral. */
export function verdictTone(verdict: Verdict | null | undefined): Tone {
  switch (verdict) {
    case "kept":
      return "positive";
    case "broken":
      return "negative";
    case "disputed":
      return "warning";
    default:
      return "neutral";
  }
}

/** Compact dashboard summary: repository, counts, and the default view's trust. */
export function PromisesCard({ host, domain: domainRef }: HostProps) {
  const model = useExplorer(host);
  if (!model)
    return (
      <Card title="Normative promises">
        <span className="pf-muted">Loading…</span>
      </Card>
    );

  const repository = model.repository;
  const defaultView = repository.defaultView ?? model.views[0]?.name ?? "";
  const view = model.views.find((v) => v.name === defaultView) ?? model.views[0] ?? null;
  const requestedDomain = domainRef?.id ?? view?.domain ?? "/";
  const domain = model.domains.some((item) => item.domain === requestedDomain)
    ? requestedDomain
    : (view?.domain ?? "/");
  const entry = model.trust.find((t) => t.view === defaultView && t.domain === domain) ?? null;
  const effective = model.effective[domain] ?? [];
  const declared = effective.filter((promise) => !promise.inherited).length;

  return (
    <Card
      title="Normative promises"
      subtitle={repository.name ?? undefined}
      actions={
        <button className="pf-link" onClick={() => host.navigation.navigate("/promises")}>
          Open ›
        </button>
      }
    >
      <Toolbar>
        <Chip tone="info">{effective.length} effective</Chip>
        <Chip tone="info">{declared} declared here</Chip>
      </Toolbar>
      <div className="pf-card-trust">
        <Field label={`Default view · ${defaultView || "—"}`}>
          {entry ? (
            <>
              Trust <strong>{pct(entry.score)}</strong> · Coverage <strong>{pct(entry.coverage)}</strong>
            </>
          ) : (
            "no trust entry"
          )}
        </Field>
        <p className="pf-card-domain">scoped to {domain}</p>
      </div>
    </Card>
  );
}

/** Inspector view for a single `norms.promise` (opened via ⌘K search). */
export function PromiseView({ resource }: ResourceComponentProps) {
  const promise = resource.data as PromiseModel;
  return (
    <div className="pf-detail">
      <p className="pf-statement">{promise.statement}</p>
      <Field label="Canonical address">
        <code className="pf-addr">{promise.address}</code>
      </Field>
      <Field label="Tags">
        {promise.tags.length ? (
          <span className="pf-tags">
            {promise.tags.map((tag) => (
              <Chip key={tag}>{tag}</Chip>
            ))}
          </span>
        ) : (
          "—"
        )}
      </Field>
      <Field label="Subject scope">
        {promise.subjects.length ? promise.subjects.join(", ") : "—"}
      </Field>
      <Field label="Criterion">
        <span className="pf-crit__kind">{promise.criteria?.kind ?? "—"}</span>
        {promise.criteria?.instructions ? (
          <span className="pf-crit__note">{promise.criteria.instructions}</span>
        ) : null}
      </Field>
    </div>
  );
}
