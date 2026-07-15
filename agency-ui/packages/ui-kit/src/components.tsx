/** A minimal set of genuinely-shared primitives. Promoted here only because the
 * shell and more than one plugin use them; skill-specific views stay in plugins. */

import type { ReactNode } from "react";

export type Tone = "neutral" | "positive" | "warning" | "negative" | "info";

export function Card({
  title,
  subtitle,
  actions,
  children,
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="ak-card">
      {(title || actions) && (
        <header className="ak-card__head">
          <div>
            {title && <h3 className="ak-card__title">{title}</h3>}
            {subtitle && <p className="ak-card__subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="ak-card__actions">{actions}</div>}
        </header>
      )}
      <div className="ak-card__body">{children}</div>
    </section>
  );
}

export function Chip({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`ak-chip ak-chip--${tone}`}>{children}</span>;
}

export function Field({ label, children }: { label: ReactNode; children: ReactNode }) {
  return (
    <div className="ak-field">
      <span className="ak-field__label">{label}</span>
      <span className="ak-field__value">{children}</span>
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: ReactNode }) {
  return (
    <div className="ak-empty">
      <strong>{title}</strong>
      {hint && <span>{hint}</span>}
    </div>
  );
}

export function Toolbar({ children }: { children: ReactNode }) {
  return <div className="ak-toolbar">{children}</div>;
}
