import {
  humanize,
  operatorLabel,
  reviewTone,
  viewLabels,
  viewOrder,
  type CLRCheck,
  type DashboardCausalClaim,
  type DashboardModel,
  type Entity,
  type Evidence,
  type Gate,
  type LogicStatus,
  type ModelIndex,
  type Tone,
} from "./model";

interface DetailsPanelProps {
  selectedId: string | null;
  model: DashboardModel;
  index: ModelIndex;
  onSelect: (id: string | null) => void;
  onClose: () => void;
}

const CLR_ORDER = [
  "clarity",
  "entity_existence",
  "causality_existence",
  "cause_insufficiency",
  "additional_cause",
  "cause_effect_reversal",
  "predicted_effect_existence",
  "tautology",
] as const;

function logicTone(status?: LogicStatus): Tone {
  if (status === "scrutinized") return "positive";
  if (status === "contradicted") return "negative";
  return "neutral";
}

function RefLine({
  id,
  statement,
  onSelect,
  variant,
}: {
  id: string;
  statement?: string;
  onSelect: (id: string | null) => void;
  variant?: string;
}) {
  return (
    <button
      type="button"
      className={`ref-line ${variant ?? ""}`}
      onClick={() => onSelect(id)}
      disabled={!statement}
    >
      <code>{id}</code>
      <span>{statement ?? "—"}</span>
    </button>
  );
}

function EntityBody({
  entity,
  model,
  index,
  onSelect,
}: {
  entity: Entity;
  model: DashboardModel;
  index: ModelIndex;
  onSelect: (id: string | null) => void;
}) {
  const tone = reviewTone(entity.review_status);
  const evidence = (entity.evidence_refs ?? [])
    .map((id) => index.evidence.get(id))
    .filter((item): item is Evidence => Boolean(item));
  const assumptions = (entity.assumption_refs ?? []).map((id) => ({
    id,
    entity: index.entities.get(id),
  }));
  const appearsIn = viewOrder.filter((view) =>
    model.views[view]?.node_ids.includes(entity.id),
  );

  return (
    <>
      <div className="entity-identity">
        <strong>{entity.id}</strong>
        <span>{humanize(entity.kind)}</span>
      </div>
      <h2>{entity.statement}</h2>
      <div className="fact-row">
        <span>
          <i className={`status-mark status-mark--${tone}`} />
          {humanize(entity.review_status ?? "unreviewed")}
        </span>
        {entity.basis && <span>{entity.basis} basis</span>}
        {entity.confidence && <span>{entity.confidence} confidence</span>}
        {entity.satisfaction && <span>{humanize(entity.satisfaction)}</span>}
        {entity.influence && <span>{humanize(entity.influence)}</span>}
      </div>

      {entity.satisfaction_criterion && (
        <section className="detail-section">
          <h3>Satisfaction criterion</h3>
          <p>{entity.satisfaction_criterion}</p>
        </section>
      )}
      {entity.reasoning && (
        <section className="detail-section">
          <h3>Why this is in the model</h3>
          <p>{entity.reasoning}</p>
        </section>
      )}

      <details className="detail-disclosure" open={evidence.length > 0}>
        <summary>
          Evidence <span>{evidence.length}</span>
        </summary>
        <div className="disclosure-body">
          {!evidence.length && <p className="muted">No evidence attached.</p>}
          {evidence.map((item) => (
            <article className="evidence-card" key={item.id}>
              <div>
                <strong>{item.id}</strong>
                <code>
                  {item.source}
                  {item.lines ? `:${item.lines}` : ""}
                </code>
              </div>
              <p>{item.observation}</p>
              {item.interpretation && <small>{item.interpretation}</small>}
            </article>
          ))}
        </div>
      </details>

      <details className="detail-disclosure">
        <summary>
          Assumptions <span>{assumptions.length}</span>
        </summary>
        <div className="disclosure-body">
          {!assumptions.length && <p className="muted">No assumptions attached.</p>}
          {assumptions.map((assumption) =>
            assumption.entity ? (
              <RefLine
                key={assumption.id}
                id={assumption.id}
                statement={assumption.entity.statement}
                onSelect={onSelect}
              />
            ) : (
              <p key={assumption.id} className="muted">
                <code>{assumption.id}</code>
              </p>
            ),
          )}
        </div>
      </details>

      <div className="view-membership">
        <span className="eyebrow">Appears in</span>
        <p>{appearsIn.map((view) => viewLabels[view].purpose).join(" · ") || "No view"}</p>
      </div>
    </>
  );
}

function ClaimBody({
  claim,
  gate,
  index,
  onSelect,
}: {
  claim: DashboardCausalClaim;
  gate?: Gate;
  index: ModelIndex;
  onSelect: (id: string | null) => void;
}) {
  const premises = (claim.premises ?? []).map((id) => ({
    id,
    entity: index.entities.get(id),
  }));
  const conclusion = index.entities.get(claim.conclusion);
  const empirical = claim.verification?.empirical_status;
  const clr = (claim.clr ?? {}) as Record<string, CLRCheck | undefined>;
  const clrEntries = CLR_ORDER.map((name) => [name as string, clr[name]] as const).filter(
    (entry): entry is readonly [string, CLRCheck] => Boolean(entry[1]),
  );
  const tone = logicTone(claim.logic_status);

  return (
    <>
      <div className="entity-identity">
        <strong>{gate ? gate.id : claim.id}</strong>
        <span>causal claim</span>
      </div>
      <h2>{conclusion?.statement ?? claim.conclusion}</h2>
      <div className="fact-row">
        <span>
          <i className={`status-mark status-mark--${tone}`} />
          {humanize(claim.logic_status ?? "candidate")}
        </span>
        {claim.operator && <span>{operatorLabel(claim.operator)} logic</span>}
        {claim.confidence && <span>{claim.confidence} confidence</span>}
        {empirical && <span>{humanize(empirical)}</span>}
      </div>

      <section className="detail-section claim-flow">
        <h3>Premises to conclusion</h3>
        <div className="claim-flow-body">
          {premises.map((premise) => (
            <RefLine
              key={premise.id}
              id={premise.id}
              statement={premise.entity?.statement}
              onSelect={onSelect}
            />
          ))}
          <div className="claim-operator" aria-hidden="true">
            {operatorLabel(claim.operator)}
          </div>
          <RefLine
            id={claim.conclusion}
            statement={conclusion?.statement}
            onSelect={onSelect}
            variant="ref-line--conclusion"
          />
        </div>
      </section>

      <details className="detail-disclosure" open>
        <summary>
          CLR checks <span>{clrEntries.length}</span>
        </summary>
        <div className="disclosure-body">
          {!clrEntries.length && <p className="muted">No CLR checks recorded.</p>}
          {clrEntries.map(([name, check]) => (
            <div className="clr-row" key={name}>
              <div className="clr-head">
                <span className="clr-name">{humanize(name)}</span>
                <span className={`clr-result clr-result--${check.result ?? "untested"}`}>
                  {humanize(check.result ?? "untested")}
                </span>
              </div>
              {check.reservation && <p className="clr-note">{check.reservation}</p>}
              {check.proposed_additional_premise && (
                <p className="clr-note clr-note--proposed">
                  Proposed premise: {check.proposed_additional_premise}
                </p>
              )}
            </div>
          ))}
        </div>
      </details>
    </>
  );
}

export function DetailsPanel({ selectedId, model, index, onSelect, onClose }: DetailsPanelProps) {
  if (!selectedId) return null;
  const entity = index.entities.get(selectedId);
  const gate = entity ? undefined : index.gates.get(selectedId);
  const claim = entity ? undefined : index.claims.get(gate?.claim ?? selectedId);
  const label = entity ? "Selected node" : claim ? "Selected claim" : "Selection";

  return (
    <aside className="details-panel" aria-label={`Details for ${selectedId}`}>
      <div className="details-panel__topline">
        <span className="eyebrow">{label}</span>
        <button className="icon-button" type="button" onClick={onClose} aria-label="Close details">
          ×
        </button>
      </div>
      {entity ? (
        <EntityBody entity={entity} model={model} index={index} onSelect={onSelect} />
      ) : claim ? (
        <ClaimBody claim={claim} gate={gate} index={index} onSelect={onSelect} />
      ) : (
        <p className="muted">
          Nothing to show for <code>{selectedId}</code>.
        </p>
      )}
    </aside>
  );
}
