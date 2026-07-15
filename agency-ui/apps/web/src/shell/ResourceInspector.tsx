/**
 * The right-hand inspector, driven entirely by the current selection.
 *
 * This is where the read-only/mutable seam is made visible. A resource is
 * either `static` (a pure function of committed files -- never writable) or
 * `live` (backed by a mutable source). The provenance badge reflects exactly
 * that: `!host.resources.canWrite(type)` (or an explicit `static` provenance)
 * renders a read-only "generated" chip; a writable type renders an
 * "editable / live" chip. Both code paths exist unconditionally -- adding a
 * mutable source later lights up the live path with zero shell changes.
 */

import { Card, Chip, EmptyState, Field } from "@agency/ui-kit";
import type { AgencyResource } from "@agency/skill-sdk";
import { refString } from "@agency/skill-sdk";
import { useHost, useSelection } from "./host-context";
import { useAsync } from "./hooks";

export function ResourceInspector() {
  const host = useHost();
  const selection = useSelection();
  const refKey = selection ? refString(selection) : null;

  const { value: resource, loading } = useAsync<AgencyResource | null>(
    () => (selection ? host.resources.get(selection) : Promise.resolve(null)),
    [refKey],
  );

  if (!selection) {
    return (
      <EmptyState
        title="Nothing selected"
        hint="Pick a resource -- from a card, a view, or ⌘K -- to inspect its provenance and relations."
      />
    );
  }
  if (loading && !resource) {
    return <div className="inspector__status">Loading {refKey}…</div>;
  }
  if (!resource) {
    return <EmptyState title="Resource not found" hint={refKey} />;
  }

  // The seam: writability is a property of the owning source, not a UI mode.
  const writable = host.resources.canWrite(resource.type);
  const isStatic = resource.provenance?.determinism === "static" || !writable;

  const views = host
    .contributions()
    .resourceViews.filter((view) => view.resourceTypes.includes(resource.type));
  const inspectors = host
    .contributions()
    .inspectors.filter((inspector) => inspector.resourceTypes.includes(resource.type));

  return (
    <div className="inspector">
      <header className="inspector__head">
        <h2 className="inspector__title">{resource.title ?? resource.id}</h2>
        <div className="inspector__chips">
          <Chip tone="neutral">{resource.type}</Chip>
          <Chip tone="neutral">{resource.ownerSkill}</Chip>
          {isStatic ? (
            <Chip tone="info">generated · read-only</Chip>
          ) : (
            <Chip tone="positive">editable · live</Chip>
          )}
        </div>
      </header>

      <Card title="Details">
        <Field label="Ref">{refKey}</Field>
        <Field label="Owner skill">{resource.ownerSkill}</Field>
        {resource.status ? <Field label="Status">{resource.status}</Field> : null}
        {resource.provenance ? (
          <Field label="Determinism">{resource.provenance.determinism}</Field>
        ) : null}
        {resource.updatedAt ? <Field label="Updated">{resource.updatedAt}</Field> : null}
      </Card>

      {views.map((view) => {
        const Component = view.component;
        return <Component key={view.id} host={host.host} resource={resource} />;
      })}
      {inspectors.map((inspector) => {
        const Component = inspector.component;
        return <Component key={inspector.id} host={host.host} resource={resource} />;
      })}

      <Relations resource={resource} refKey={refKey} />
    </div>
  );
}

function Relations({ resource, refKey }: { resource: AgencyResource; refKey: string | null }) {
  const host = useHost();
  const { value: relations, loading } = useAsync(
    () => host.resources.relations({ type: resource.type, id: resource.id }),
    [refKey],
  );
  const rels = relations ?? [];

  return (
    <Card title="Relations" subtitle={rels.length ? `${rels.length} linked` : undefined}>
      {loading && rels.length === 0 ? (
        <p className="muted">Loading…</p>
      ) : rels.length === 0 ? (
        <p className="muted">No relations.</p>
      ) : (
        <ul className="relations">
          {rels.map((relation) => {
            const other = refString(relation.from) === refKey ? relation.to : relation.from;
            return (
              <li key={relation.id}>
                <button
                  type="button"
                  className="relations__item"
                  onClick={() => host.selection.select(other)}
                >
                  <span className="relations__type">{relation.type}</span>
                  <span className="relations__ref">{refString(other)}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
