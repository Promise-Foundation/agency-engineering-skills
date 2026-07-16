import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { AgencyResource, HostProps, ResourceComponentProps } from "@agency/skill-sdk";
import { parseRef } from "@agency/skill-sdk";
import { Card, Chip, EmptyState, Field, type Tone } from "@agency/ui-kit";
import type { HypothesisRow, TraceItem } from "./mapping";

/** Same value→tone reading the whole surface uses: capability, evidence
 * maturity, and conclusion are distinct dimensions, so a chip's colour reflects
 * standing, never which dimension it came from. */
function toneFor(value?: string): Tone {
  if (!value) return "neutral";
  if (["supported", "implemented", "kept", "current"].includes(value)) return "positive";
  if (["falsified", "failing", "regressed", "broken"].includes(value)) return "negative";
  if (["inconclusive", "partial", "internal_pilot"].includes(value)) return "warning";
  if (["comparative_pilot", "external_replication", "mechanism"].includes(value)) return "info";
  return "neutral";
}

function label(value?: string): string {
  return (value ?? "—").replaceAll("_", " ");
}

function StatusChip({ value }: { value?: string }) {
  return <Chip tone={toneFor(value)}>{label(value)}</Chip>;
}

function useHypotheses(
  host: HostProps["host"],
  domain: string | null,
): { rows: AgencyResource<HypothesisRow>[]; loading: boolean } {
  const [rows, setRows] = useState<AgencyResource<HypothesisRow>[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let live = true;
    if (!domain) {
      setRows([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    void host.resources.list({ type: "hypothesis", domain }).then((items) => {
      if (!live) return;
      setRows(items as AgencyResource<HypothesisRow>[]);
      setLoading(false);
    });
    return () => {
      live = false;
    };
  }, [host, domain]);
  return { rows, loading };
}

type Filter = "all" | "needs-outcome" | "unresolved";

export function HypothesisTable({ host, domain }: HostProps) {
  const domainPath = domain?.id ?? null;
  const { rows, loading } = useHypotheses(host, domainPath);
  const [filter, setFilter] = useState<Filter>("all");

  const needsOutcome = useMemo(
    () => rows.filter((r) => (r.data.conclusion ?? "not_tested") === "not_tested"),
    [rows],
  );
  const inconclusive = useMemo(
    () => rows.filter((r) => r.data.conclusion === "inconclusive"),
    [rows],
  );
  const visible =
    filter === "needs-outcome" ? needsOutcome : filter === "unresolved" ? inconclusive : rows;

  if (loading) return <EmptyState title="Loading hypotheses…" />;
  if (rows.length === 0)
    return (
      <EmptyState
        title={`Hypothesize has not been generated for ${domainPath ?? "this domain"}`}
        hint="Generate a Hypothesize artifact for this domain before its propositions can be shown."
      />
    );

  const select = (ref: string) => {
    try {
      const parsed = parseRef(ref);
      const id =
        domainPath && (parsed.type.startsWith("ltp.") || parsed.type.startsWith("zpd."))
          ? `${encodeURIComponent(domainPath)}::${parsed.id}`
          : parsed.id;
      host.selection.select({ ...parsed, id });
    } catch {
      /* an illustrative ref that isn't a valid "type:id" — ignore */
    }
  };

  return (
    <div className="hyp-page">
      <div className="hyp-page__head">
        <div>
          <h1>Hypotheses</h1>
          <p>
            Working domain {domainPath ?? "not selected"} · generated from registered sources
          </p>
        </div>
        <Chip tone="info">generated · read-only</Chip>
      </div>

      <div className="hyp-filters" role="tablist" aria-label="Hypothesis filters">
        <FilterButton active={filter === "all"} onClick={() => setFilter("all")}>
          All {rows.length}
        </FilterButton>
        <FilterButton
          active={filter === "needs-outcome"}
          onClick={() => setFilter("needs-outcome")}
        >
          Needs outcome evidence {needsOutcome.length}
        </FilterButton>
        <FilterButton active={filter === "unresolved"} onClick={() => setFilter("unresolved")}>
          Inconclusive {inconclusive.length}
        </FilterButton>
      </div>

      <div className="hyp-table-wrap">
        <table className="hyp-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Proposition</th>
              <th>Host subject</th>
              <th>Capability</th>
              <th>Evidence</th>
              <th>Conclusion</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((row) => (
              <tr
                key={row.id}
                onClick={() => host.selection.select({ type: "hypothesis", id: row.id })}
              >
                <td className="hyp-id">{row.data.id}</td>
                <td className="hyp-prop">
                  <strong>{row.data.title}</strong>
                  {row.data.scope && <span>{row.data.scope}</span>}
                </td>
                <td>
                  {row.data.subject ? (
                    <button
                      type="button"
                      className="hyp-ref"
                      onClick={(event) => {
                        event.stopPropagation();
                        select(row.data.subject as string);
                      }}
                    >
                      {row.data.subject}
                    </button>
                  ) : (
                    <span className="hyp-muted">—</span>
                  )}
                </td>
                <td>
                  <StatusChip value={row.data.capability_status} />
                </td>
                <td>
                  <StatusChip value={row.data.evidence_maturity} />
                </td>
                <td>
                  <StatusChip value={row.data.conclusion ?? "not_tested"} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      className={`hyp-filter${active ? " is-active" : ""}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export function HypothesisCard({ host, domain }: HostProps) {
  const domainPath = domain?.id ?? null;
  const { rows, loading } = useHypotheses(host, domainPath);
  if (loading) return <Card title="Hypotheses">Loading…</Card>;
  if (rows.length === 0)
    return (
      <Card title="Hypotheses" subtitle={domainPath}>
        Not generated for this domain.
      </Card>
    );
  const supported = rows.filter((r) => r.data.conclusion === "supported").length;
  const needsOutcome = rows.filter(
    (r) => (r.data.conclusion ?? "not_tested") === "not_tested",
  ).length;
  return (
    <Card
      title="Hypotheses"
      subtitle="Capability, evidence, and conclusion kept separate"
      actions={
        <button className="hyp-linkbtn" onClick={() => host.navigation.navigate("/hypotheses")}>
          Open ›
        </button>
      }
    >
      <div className="hyp-card-chips">
        <Chip tone="info">{rows.length} tracked</Chip>
        <Chip tone="positive">{supported} supported</Chip>
        <Chip tone="neutral">{needsOutcome} need outcome</Chip>
      </div>
    </Card>
  );
}

export function HypothesisView({ host, resource }: ResourceComponentProps) {
  const hypothesis = resource.data as HypothesisRow;
  const selectRef = (ref: string) => {
    try {
      const parsed = parseRef(ref);
      const id =
        resource.domain && (parsed.type.startsWith("ltp.") || parsed.type.startsWith("zpd."))
          ? `${encodeURIComponent(resource.domain)}::${parsed.id}`
          : parsed.id;
      host.selection.select({ ...parsed, id });
    } catch {
      /* illustrative ref that isn't a valid "type:id" */
    }
  };

  return (
    <div className="hyp-detail">
      <Card title="Empirical standing">
        <div className="hyp-dimensions">
          <div className="hyp-dimension">
            <span className="hyp-dimension__label">Capability</span>
            <StatusChip value={hypothesis.capability_status} />
          </div>
          <div className="hyp-dimension">
            <span className="hyp-dimension__label">Evidence</span>
            <StatusChip value={hypothesis.evidence_maturity} />
          </div>
          <div className="hyp-dimension">
            <span className="hyp-dimension__label">Conclusion</span>
            <StatusChip value={hypothesis.conclusion ?? "not_tested"} />
          </div>
        </div>
        {hypothesis.subject && (
          <Field label="Host subject">
            <button
              type="button"
              className="hyp-ref hyp-ref--inline"
              onClick={() => selectRef(hypothesis.subject as string)}
            >
              {hypothesis.subject}
            </button>
          </Field>
        )}
        {hypothesis.scope && <Field label="Scope">{hypothesis.scope}</Field>}
        {hypothesis.statement && <Field label="Statement">{hypothesis.statement}</Field>}
      </Card>

      {hypothesis.consequences && hypothesis.consequences.length > 0 && (
        <Card title="Expected consequences">
          <ul className="hyp-list">
            {hypothesis.consequences.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </Card>
      )}

      {hypothesis.defeaters && hypothesis.defeaters.length > 0 && (
        <Card title="Defeaters">
          <ul className="hyp-list">
            {hypothesis.defeaters.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </Card>
      )}

      {hypothesis.trace && hypothesis.trace.length > 0 && (
        <Card title="Evidence trace" subtitle="What actually stands behind each dimension">
          <div className="hyp-trace">
            {hypothesis.trace.map((item, index) => (
              <TraceRow key={item.id ?? `none-${index}`} item={item} />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

function TraceRow({ item }: { item: TraceItem }) {
  return (
    <article className="hyp-trace__item">
      <div className="hyp-trace__top">
        <span className="hyp-trace__title">{item.title}</span>
        <span className="hyp-trace__relation">{item.relation}</span>
      </div>
      {item.summary && <p className="hyp-trace__summary">{item.summary}</p>}
      {item.tags.length > 0 && (
        <div className="hyp-trace__meta">
          {item.tags.map((tag) => (
            <Chip key={tag} tone={toneFor(tag)}>
              {label(tag)}
            </Chip>
          ))}
        </div>
      )}
    </article>
  );
}
