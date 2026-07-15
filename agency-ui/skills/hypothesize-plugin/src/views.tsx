import { useEffect, useState } from "react";
import type { AgencyResource, HostProps, ResourceComponentProps } from "@agency/skill-sdk";
import { Card, Chip, EmptyState, Field, Toolbar, type Tone } from "@agency/ui-kit";
import type { HypothesisRow } from "./mapping";

function conclusionTone(conclusion?: string): Tone {
  if (conclusion === "supported") return "positive";
  if (conclusion === "falsified") return "negative";
  if (conclusion === "inconclusive") return "warning";
  return "neutral";
}

function useHypotheses(host: HostProps["host"]): AgencyResource<HypothesisRow>[] {
  const [rows, setRows] = useState<AgencyResource<HypothesisRow>[]>([]);
  useEffect(() => {
    let live = true;
    void host.resources.list({ type: "hypothesis" }).then((items) => {
      if (live) setRows(items as AgencyResource<HypothesisRow>[]);
    });
    return () => {
      live = false;
    };
  }, [host]);
  return rows;
}

export function HypothesisTable({ host }: HostProps) {
  const rows = useHypotheses(host);
  if (rows.length === 0) return <EmptyState title="Loading hypotheses…" />;
  return (
    <div className="hyp-table">
      <h1>Hypotheses</h1>
      <p className="hyp-sub">Empirical status is kept separate from any linked LTP logic.</p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Hypothesis</th>
            <th>Capability</th>
            <th>Evidence</th>
            <th>Conclusion</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} onClick={() => host.selection.select({ type: "hypothesis", id: row.id })}>
              <td>{row.id}</td>
              <td>{row.title}</td>
              <td>{row.data.capability_status ?? "-"}</td>
              <td>{row.data.evidence_maturity ?? "-"}</td>
              <td>
                <Chip tone={conclusionTone(row.data.conclusion)}>{row.data.conclusion ?? "not_tested"}</Chip>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function HypothesisCard({ host }: HostProps) {
  const rows = useHypotheses(host);
  const supported = rows.filter((r) => r.data.conclusion === "supported").length;
  return (
    <Card
      title="Hypotheses"
      actions={
        <button className="hyp-link" onClick={() => host.navigation.navigate("/hypotheses")}>
          Open ›
        </button>
      }
    >
      <Toolbar>
        <Chip tone="info">{rows.length} tracked</Chip>
        <Chip tone="positive">{supported} supported</Chip>
      </Toolbar>
    </Card>
  );
}

export function HypothesisView({ resource }: ResourceComponentProps) {
  const hypothesis = resource.data as HypothesisRow;
  return (
    <div className="hyp-detail">
      {hypothesis.summary && <p className="hyp-summary">{hypothesis.summary}</p>}
      <Field label="Conclusion">
        <Chip tone={conclusionTone(hypothesis.conclusion)}>{hypothesis.conclusion ?? "not_tested"}</Chip>
      </Field>
      <Field label="Capability">{hypothesis.capability_status ?? "-"}</Field>
      <Field label="Evidence maturity">{hypothesis.evidence_maturity ?? "-"}</Field>
      <Field label="Evidence health">{hypothesis.evidence_health ?? "-"}</Field>
      <p className="hyp-note">Linked LTP claims appear under Relations — a green test proves behavior, not the modelled causation.</p>
    </div>
  );
}
