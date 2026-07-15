/**
 * The "/" route. Renders every contributed dashboard card inside a titled
 * {@link Card}. The shell knows nothing about what a card contains -- it only
 * knows the slot. Cards receive the narrow `host.host` (an AgencyHost).
 */

import { Card, EmptyState } from "@agency/ui-kit";
import { useHost } from "./host-context";

export function DashboardHome() {
  const host = useHost();
  const cards = host.contributions().dashboardCards;

  if (cards.length === 0) {
    return (
      <EmptyState
        title="Nothing on the dashboard yet"
        hint="Activated skills contribute cards into this slot."
      />
    );
  }

  return (
    <div className="dash">
      {cards.map((card) => {
        const Component = card.component;
        return (
          <Card key={card.id} title={card.title} subtitle={card.skillId}>
            <Component host={host.host} />
          </Card>
        );
      })}
    </div>
  );
}
