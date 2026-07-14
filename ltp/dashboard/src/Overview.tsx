import {
  humanize,
  viewLabels,
  viewOrder,
  viewToPlanKey,
  type DashboardModel,
  type Entity,
  type ModelIndex,
  type PlanItem,
} from "./model";

interface OverviewProps {
  model: DashboardModel;
  index: ModelIndex;
  onSelect: (id: string) => void;
  onExplore: () => void;
}

interface StoryStep {
  label: string;
  statement: string;
  meta?: string;
  selectId?: string;
}

function planTone(status?: string): string {
  if (status === "done") return "positive";
  if (status === "skipped" || status === "deferred") return "muted";
  return "neutral";
}

export function Overview({ model, index, onSelect, onExplore }: OverviewProps) {
  const { analysis, project, health } = model;

  const goal = project.goal ? index.entities.get(project.goal) : undefined;
  const constraint = analysis.current_constraint
    ? index.entities.get(analysis.current_constraint)
    : undefined;
  const effect = analysis.expected_effect
    ? index.entities.get(analysis.expected_effect)
    : undefined;

  const actionId = analysis.recommended_next_action;
  const actionEntity = actionId ? index.entities.get(actionId) : undefined;
  const actionTransition = actionId
    ? model.transitions.find((transition) => transition.id === actionId)
    : undefined;
  const actionActionEntity = actionTransition
    ? index.entities.get(actionTransition.action)
    : undefined;

  const story: StoryStep[] = [
    {
      label: "Current constraint",
      statement: constraint?.statement ?? "Not identified",
      meta: constraint ? `${constraint.id} · ${constraint.confidence ?? "?"} confidence` : undefined,
      selectId: constraint?.id,
    },
    {
      label: "Next move",
      statement: actionEntity?.statement ?? actionActionEntity?.statement ?? actionId ?? "Not selected",
      meta: actionEntity
        ? `${actionEntity.id} · ${actionEntity.confidence ?? "?"} confidence`
        : actionTransition
          ? `${actionTransition.id} · ${humanize(actionTransition.estimated_size ?? "transition")}`
          : undefined,
      selectId: actionEntity?.id ?? actionActionEntity?.id,
    },
    {
      label: "Expected shift",
      statement: effect?.statement ?? "Not modelled",
      meta: effect ? `${effect.id} · ${effect.confidence ?? "?"} confidence` : undefined,
      selectId: effect?.id,
    },
  ];

  const kindCounts = new Map<Entity["kind"], number>();
  for (const entity of model.entities) {
    kindCounts.set(entity.kind, (kindCounts.get(entity.kind) ?? 0) + 1);
  }
  const kinds = [...kindCounts.entries()].sort((a, b) => b[1] - a[1]);

  const lists: Array<{ label: string; items: string[]; emptyNote: string }> = [
    { label: "Open questions", items: model.open_questions, emptyNote: "None recorded" },
    { label: "Contradictions", items: model.contradictions, emptyNote: "None found" },
    { label: "Coverage gaps", items: model.coverage_gaps, emptyNote: "None flagged" },
  ];

  return (
    <main className="overview">
      <section className="overview-hero">
        <div>
          <span className="eyebrow">The system at a glance</span>
          <h1>{project.name}</h1>
          <p>
            {humanize(project.analysis_mode ?? "forward")} analysis
            {project.analyzed_path ? ` of ${project.analyzed_path}` : ""}. Follow the limiting
            condition to the next action and the effect it is meant to create.
          </p>
          {goal && (
            <p className="hero-goal">
              <span className="eyebrow">Goal</span>
              {goal.statement}
            </p>
          )}
        </div>
        <button type="button" className="primary-button" onClick={onExplore}>
          Explore the logic <span>&rarr;</span>
        </button>
      </section>

      <section className="logic-story" aria-label="Constraint to action story">
        {story.map((step, stepIndex) => (
          <div className="story-step-wrap" key={step.label}>
            <button
              type="button"
              className={`story-step story-step--${stepIndex + 1}`}
              disabled={!step.selectId}
              onClick={() => step.selectId && onSelect(step.selectId)}
            >
              <span>{step.label}</span>
              <strong>{step.statement}</strong>
              {step.meta && <small>{step.meta}</small>}
            </button>
            {stepIndex < story.length - 1 && (
              <span className="story-arrow" aria-hidden="true">
                &rarr;
              </span>
            )}
          </div>
        ))}
      </section>

      <section className="plan-section">
        <header className="section-heading">
          <div>
            <span className="eyebrow">The analysis plan</span>
            <h2>What was examined</h2>
            <p>
              {humanize(model.analysis_plan.mode ?? "full")} run. Each thinking process is marked
              with how far it was taken.
            </p>
          </div>
        </header>
        <div className="plan-grid">
          {viewOrder.map((view) => {
            const item = model.analysis_plan[viewToPlanKey[view]] as PlanItem | undefined;
            const status = item?.status ?? "required";
            return (
              <article className="plan-item" key={view} data-tone={planTone(status)}>
                <div className="plan-item__top">
                  <span>{viewLabels[view].purpose}</span>
                  <em className={`plan-badge plan-badge--${planTone(status)}`}>{humanize(status)}</em>
                </div>
                {item?.reason && <small>{item.reason}</small>}
              </article>
            );
          })}
        </div>
      </section>

      <section className="plan-section">
        <header className="section-heading">
          <div>
            <span className="eyebrow">Model health</span>
            <h2>{health.publishable ? "Ready to publish" : "Needs attention"}</h2>
            <p>
              {health.diagnostics.length
                ? `${health.diagnostics.length} diagnostic${health.diagnostics.length === 1 ? "" : "s"} to review.`
                : "No diagnostics were raised for this model."}
            </p>
          </div>
          <span className={`publish-badge ${health.publishable ? "is-ok" : "is-blocked"}`}>
            {health.publishable ? "Publishable" : "Blocked"}
          </span>
        </header>
        <div className="model-health">
          <article>
            <strong>{health.counts.error}</strong>
            <span>errors</span>
          </article>
          <article>
            <strong>{health.counts.warning}</strong>
            <span>warnings</span>
          </article>
          <article>
            <strong>{health.counts.info}</strong>
            <span>info notices</span>
          </article>
          <article>
            <strong>{model.entities.length}</strong>
            <span>conditions in the model</span>
          </article>
        </div>
      </section>

      <section className="plan-section">
        <header className="section-heading">
          <div>
            <span className="eyebrow">Composition</span>
            <h2>Conditions by kind</h2>
            <p>{model.entities.length} entities and {model.evidence.length} evidence items.</p>
          </div>
        </header>
        <div className="kind-grid">
          {kinds.map(([kind, count]) => (
            <article className="kind-card" key={kind}>
              <strong>{count}</strong>
              <span>{humanize(kind)}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="plan-section">
        <header className="section-heading">
          <div>
            <span className="eyebrow">Where the model is unfinished</span>
            <h2>Questions, contradictions, gaps</h2>
          </div>
        </header>
        <div className="list-columns">
          {lists.map((list) => (
            <article className="list-card" key={list.label}>
              <h3>
                {list.label} <span>{list.items.length}</span>
              </h3>
              {list.items.length ? (
                <ul>
                  {list.items.map((item, itemIndex) => (
                    <li key={itemIndex}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="muted">{list.emptyNote}</p>
              )}
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
