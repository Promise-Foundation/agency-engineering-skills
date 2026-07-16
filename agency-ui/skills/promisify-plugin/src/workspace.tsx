/** The Promisify explorer route (/promises): a read-only, two-pane
 * workspace over one precomputed `norms.py explorer` model — effective promises
 * for the shell-selected domain and an evidence + trust explanation — under an
 * observer/view trust header. It also offers a safe
 * "draft a promise" composer that only writes an *agent instruction*, never
 * files. All inheritance, assessment selection, and trust are read, not
 * recomputed. */

import { useEffect, useState } from "react";
import type { AgencyHost, HostProps } from "@agency/skill-sdk";
import { Chip, EmptyState, Field } from "@agency/ui-kit";
import type {
  EffectiveEntry,
  Explorer,
  Promise as PromiseModel,
  TrustEntry,
} from "./mapping";
import { humanizeAssessor, pct, shortRev, useExplorer, verdictTone } from "./views";

const NAME_PATTERN = /^_[a-z0-9]+(?:_[a-z0-9]+)*$/;

/** ISO instant → "2026-07-15 09:00" (stable, timezone-free). */
function formatInstant(value: string | null | undefined): string {
  if (!value) return "—";
  const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/.exec(value);
  return match ? `${match[1]} ${match[2]}` : value;
}

function confidencePct(value: number | null | undefined): string {
  return value == null ? "—" : `${Math.round(value * 100)}%`;
}

/** Assessor-relative status for a promise in the selected domain: prefer the
 * assessments recorded against this effective domain, else any for the promise. */
function assessmentSummary(model: Explorer, address: string, domain: string): string {
  const all = model.assessments.filter((a) => a.promise === address);
  const scoped = all.filter((a) => a.effectiveDomain === domain);
  const relevant = scoped.length ? scoped : all;
  if (relevant.length === 0) return "Not yet assessed";
  const verdicts = new Set(relevant.map((a) => a.verdict));
  if (verdicts.size > 1) return "Assessors disagree";
  const verdict = relevant[0].verdict;
  const assessors = [...new Set(relevant.map((a) => a.assessor))];
  if (assessors.length === 1) return `${humanizeAssessor(assessors[0])} assessed ${verdict}`;
  return `${assessors.length} assessors assessed ${verdict}`;
}

export function PromisesWorkspace({ host, domain: domainRef }: HostProps) {
  const model = useExplorer(host);
  const [activeView, setActiveView] = useState<string | null>(null);
  const [selectedPromise, setSelectedPromise] = useState<string | null>(null);
  const [drafting, setDrafting] = useState(false);

  useEffect(() => {
    setSelectedPromise(null);
  }, [domainRef?.id]);

  if (!model) return <EmptyState title="Loading Promisify…" />;

  const views = model.views;
  const defaultViewName = model.repository.defaultView ?? views[0]?.name ?? "";
  const viewName =
    activeView && views.some((v) => v.name === activeView) ? activeView : defaultViewName;
  const activeViewDomain = views.find((v) => v.name === viewName)?.domain ?? "/";
  const requestedDomain = domainRef?.id ?? activeViewDomain;
  const domain = model.domains.some((item) => item.domain === requestedDomain)
    ? requestedDomain
    : activeViewDomain;

  const trustEntry = model.trust.find((t) => t.view === viewName && t.domain === domain) ?? null;
  const effective = model.effective[domain] ?? [];
  const inherited = effective.filter((e) => e.inherited);
  const declared = effective.filter((e) => !e.inherited);
  const selected = selectedPromise
    ? model.promises.find((p) => p.address === selectedPromise) ?? null
    : null;

  return (
    <div className="pf-workspace">
      <header className="pf-trust">
        <div className="pf-trust__top">
          <label className="pf-observer">
            <span className="pf-observer__label">Observer view</span>
            <select
              className="pf-select"
              value={viewName}
              onChange={(event) => setActiveView(event.target.value)}
            >
              {views.map((view) => (
                <option key={view.name} value={view.name}>
                  {view.name}
                </option>
              ))}
            </select>
          </label>
          <button className="pf-btn" onClick={() => setDrafting(true)}>
            Draft a promise
          </button>
        </div>
        {trustEntry ? (
          <div className="pf-trust__line">
            <span className="pf-metric">
              Trust: <strong className="pf-metric__v">{pct(trustEntry.score)}</strong>
            </span>
            <span className="pf-metric">
              Coverage: <strong className="pf-metric__v">{pct(trustEntry.coverage)}</strong>
            </span>
            <span className="pf-metric">
              {trustEntry.counts.kept} kept, {trustEntry.counts.broken} broken,{" "}
              {trustEntry.counts.disputed} disputed
            </span>
            <span className="pf-metric">Observer: {trustEntry.observer}</span>
            <span className="pf-metric">Snapshot: {shortRev(trustEntry.snapshot?.revision)}</span>
            <span className="pf-metric">Conflict policy: {trustEntry.conflictPolicy}</span>
          </div>
        ) : (
          <div className="pf-trust__line">
            <span className="pf-muted">
              No trust entry for {viewName || "this view"} × {domain}.
            </span>
          </div>
        )}
      </header>

      <div className="pf-panes">
        <section className="pf-pane pf-effective">
          <h2 className="pf-pane__title">
            Effective promises
            <span className="pf-pane__sub">{domain}</span>
          </h2>
          {effective.length === 0 ? (
            <EmptyState
              title="No effective promises here"
              hint="Nothing is declared at this domain or inherited from an ancestor."
            />
          ) : (
            <>
              <PromiseGroup
                heading="Inherited from ancestors"
                entries={inherited}
                model={model}
                domain={domain}
                trustEntry={trustEntry}
                selected={selectedPromise}
                onSelect={setSelectedPromise}
              />
              <PromiseGroup
                heading="Declared here"
                entries={declared}
                model={model}
                domain={domain}
                trustEntry={trustEntry}
                selected={selectedPromise}
                onSelect={setSelectedPromise}
              />
            </>
          )}
        </section>

        <section className="pf-pane pf-explain">
          <h2 className="pf-pane__title">Explanation</h2>
          {selected ? (
            <ExplanationPanel
              model={model}
              promise={selected}
              domain={domain}
              trustEntry={trustEntry}
            />
          ) : (
            <EmptyState
              title="Select a promise"
              hint="Pick a promise to see why it applies, who assessed it, the evidence, and its effect on trust."
            />
          )}
        </section>
      </div>

      {drafting ? (
        <DraftDialog
          key={domain}
          model={model}
          defaultDomain={domain}
          host={host}
          onClose={() => setDrafting(false)}
        />
      ) : null}
    </div>
  );
}

function PromiseGroup({
  heading,
  entries,
  model,
  domain,
  trustEntry,
  selected,
  onSelect,
}: {
  heading: string;
  entries: EffectiveEntry[];
  model: Explorer;
  domain: string;
  trustEntry: TrustEntry | null;
  selected: string | null;
  onSelect: (address: string) => void;
}) {
  return (
    <div className="pf-group">
      <h3 className="pf-group__heading">
        {heading}
        <span className="pf-group__count">{entries.length}</span>
      </h3>
      {entries.length === 0 ? (
        <p className="pf-group__empty">None</p>
      ) : (
        entries.map((entry) => {
          const result = trustEntry?.results.find((r) => r.promise === entry.promise) ?? null;
          return (
            <button
              key={entry.promise}
              className={`pf-card${selected === entry.promise ? " is-active" : ""}`}
              onClick={() => onSelect(entry.promise)}
            >
              <span className="pf-card__title">{entry.title ?? entry.statement}</span>
              {entry.title ? <span className="pf-card__statement">{entry.statement}</span> : null}
              <span className="pf-card__status">
                <span className="pf-card__assessor">
                  {assessmentSummary(model, entry.promise, domain)}
                </span>
                {result ? <Chip tone={verdictTone(result.verdict)}>{result.verdict}</Chip> : null}
              </span>
            </button>
          );
        })
      )}
    </div>
  );
}

function ExplanationPanel({
  model,
  promise,
  domain,
  trustEntry,
}: {
  model: Explorer;
  promise: PromiseModel;
  domain: string;
  trustEntry: TrustEntry | null;
}) {
  const effectiveEntry = (model.effective[domain] ?? []).find((e) => e.promise === promise.address);
  const declaredHere = effectiveEntry ? !effectiveEntry.inherited : promise.domain === domain;
  const declaredAt = effectiveEntry?.declaredAt ?? promise.domain;
  const claims = model.assessments.filter((a) => a.promise === promise.address);
  const result = trustEntry?.results.find((r) => r.promise === promise.address) ?? null;
  const unresolved = trustEntry?.unresolved.includes(promise.address) ?? false;

  return (
    <div className="pf-explain__body">
      <div className="pf-explain__head">
        <span className="pf-eyebrow">Why this applies</span>
        <h3 className="pf-explain__title">{promise.title ?? promise.statement}</h3>
        {promise.title ? <p className="pf-explain__statement">{promise.statement}</p> : null}
      </div>

      <Field label="Canonical address">
        <code className="pf-addr">{promise.address}</code>
      </Field>
      <Field label="Inheritance path">
        {declaredHere ? (
          "Declared here"
        ) : (
          <>
            Declared at <code className="pf-addr">{declaredAt}</code> → effective here by inheritance
          </>
        )}
      </Field>
      <Field label="Subject scope">
        {promise.subjects.length ? promise.subjects.join(", ") : "—"}
      </Field>
      <Field label="Assessment criterion">
        <span className="pf-crit__kind">{promise.criteria?.kind ?? "—"}</span>
        {promise.criteria?.instructions ? (
          <span className="pf-crit__note">{promise.criteria.instructions}</span>
        ) : null}
      </Field>

      <section className="pf-section">
        <h4 className="pf-subhead">
          Claims by assessor <span className="pf-count">{claims.length}</span>
        </h4>
        {claims.length === 0 ? (
          <p className="pf-muted">No assessments recorded for this promise.</p>
        ) : (
          claims.map((claim) => (
            <article key={claim.id} className="pf-claim">
              <div className="pf-claim__head">
                <span className="pf-claim__assessor">{humanizeAssessor(claim.assessor)}</span>
                <Chip tone={verdictTone(claim.verdict)}>{claim.verdict}</Chip>
              </div>
              <div className="pf-claim__meta">
                <span>confidence {confidencePct(claim.confidence)}</span>
                <span>observed {formatInstant(claim.observedAt)}</span>
                <span>rev {shortRev(claim.revision)}</span>
                <span className="pf-claim__scope">for {claim.effectiveDomain}</span>
              </div>
              {claim.rationale ? <p className="pf-claim__rationale">{claim.rationale}</p> : null}
              {claim.evidence.length > 0 ? (
                <ul className="pf-evidence">
                  {claim.evidence.map((item, index) => (
                    <li key={index}>
                      <span className="pf-evidence__kind">{item.kind ?? "evidence"}</span>
                      {" — "}
                      {item.summary ?? item.reference ?? "—"}
                    </li>
                  ))}
                </ul>
              ) : null}
            </article>
          ))
        )}
      </section>

      <section className="pf-section">
        <h4 className="pf-subhead">Effect on the active trust calculation</h4>
        {!trustEntry ? (
          <p className="pf-muted">No trust view is active for this domain.</p>
        ) : result ? (
          <>
            <p className="pf-effect">
              Under <strong>{trustEntry.view}</strong>, this promise resolves to{" "}
              <Chip tone={verdictTone(result.verdict)}>{result.verdict}</Chip>
              {result.assessmentIds.length > 0
                ? `, drawing on ${result.assessmentIds.length} selected assessment${
                    result.assessmentIds.length > 1 ? "s" : ""
                  }.`
                : ", with no selected assessments."}
            </p>
            {unresolved ? (
              <p className="pf-effect__flag">
                Counted as unresolved for this view — excluded from the trust score.
              </p>
            ) : null}
          </>
        ) : (
          <p className="pf-muted">This promise is not part of this domain's trust calculation.</p>
        )}
      </section>
    </div>
  );
}

/** Minimal, side-effect-free authoring: collects the four fields a declaration
 * needs, previews the canonical address and inherited reach, and composes an
 * instruction for the agent. It never writes files. */
function DraftDialog({
  model,
  defaultDomain,
  host,
  onClose,
}: {
  model: Explorer;
  defaultDomain: string;
  host: AgencyHost;
  onClose: () => void;
}) {
  const [statement, setStatement] = useState("");
  const [domain, setDomain] = useState(defaultDomain);
  const [name, setName] = useState("_");
  const [subjectsText, setSubjectsText] = useState("");
  const [composed, setComposed] = useState(false);

  const nameValid = NAME_PATTERN.test(name);
  const address = domain === "/" ? "/" + name : domain + "/" + name;
  const subjects = subjectsText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const canCompose = statement.trim().length > 0 && nameValid;
  const instruction = buildInstruction({ statement, domain, name, address, subjects });

  const copy = () => {
    void navigator.clipboard
      .writeText(instruction)
      .then(() => host.notifications.info("Agent instruction copied to clipboard."))
      .catch(() => host.notifications.warn("Copy failed — select the text and copy manually."));
  };

  const reset = () => setComposed(false);

  return (
    <div className="pf-modal__overlay" onClick={onClose}>
      <div
        className="pf-modal"
        role="dialog"
        aria-label="Draft a promise"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="pf-modal__head">
          <h3 className="pf-modal__title">Draft a promise</h3>
          <button className="pf-icon-btn" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>
        <div className="pf-modal__body">
          <label className="pf-field">
            <span className="pf-field__label">Normative statement</span>
            <textarea
              className="pf-input pf-textarea"
              rows={3}
              value={statement}
              placeholder="Subjects in this domain OUGHT to…"
              onChange={(event) => {
                setStatement(event.target.value);
                reset();
              }}
            />
          </label>

          <label className="pf-field">
            <span className="pf-field__label">Declaring domain</span>
            <select
              className="pf-input pf-select"
              value={domain}
              onChange={(event) => {
                setDomain(event.target.value);
                reset();
              }}
            >
              {model.domains.map((record) => (
                <option key={record.domain} value={record.domain}>
                  {record.domain}
                </option>
              ))}
            </select>
          </label>

          <label className="pf-field">
            <span className="pf-field__label">Local name</span>
            <input
              className="pf-input"
              value={name}
              spellCheck={false}
              autoComplete="off"
              onChange={(event) => {
                setName(event.target.value);
                reset();
              }}
            />
            {nameValid ? null : (
              <span className="pf-hint pf-hint--warn">
                Must start with “_” and be lowercase snake_case, e.g. _uses_pydantic.
              </span>
            )}
          </label>

          <label className="pf-field">
            <span className="pf-field__label">Subject paths (one per line)</span>
            <textarea
              className="pf-input pf-textarea"
              rows={3}
              value={subjectsText}
              placeholder={"python.class\ndomain content"}
              onChange={(event) => {
                setSubjectsText(event.target.value);
                reset();
              }}
            />
          </label>

          <div className="pf-preview">
            <Field label="Canonical address">
              <code className="pf-addr">{nameValid ? address : "—"}</code>
            </Field>
            <Field label="Inherited reach">
              effective in <code className="pf-addr">{domain}</code> and all descendant domains
            </Field>
          </div>

          {composed ? (
            <div className="pf-compose">
              <div className="pf-compose__head">
                <span className="pf-field__label">Agent instruction</span>
                <button className="pf-btn pf-btn--sm" onClick={copy}>
                  Copy
                </button>
              </div>
              <pre className="pf-instruction">{instruction}</pre>
            </div>
          ) : (
            <button
              className="pf-btn pf-btn--primary"
              disabled={!canCompose}
              onClick={() => setComposed(true)}
            >
              Compose agent instruction
            </button>
          )}

          <p className="pf-note">
            Read-only composer — this writes no files. Copy the instruction and hand it to the
            agent, which runs the Promisify skill and <code>norms.py validate</code>.
          </p>
        </div>
      </div>
    </div>
  );
}

function buildInstruction(input: {
  statement: string;
  domain: string;
  name: string;
  address: string;
  subjects: string[];
}): string {
  const subjectList = input.subjects.length ? input.subjects.join(", ") : "(none specified)";
  return [
    "Using the Promisify skill, declare a promise.",
    `Normative statement: "${input.statement.trim()}".`,
    `Declaring domain: \`${input.domain}\`.`,
    `Local name: \`${input.name}\` (canonical address \`${input.address}\`).`,
    `Subject paths: ${subjectList}.`,
    "Then validate with `norms.py validate`.",
  ].join(" ");
}
