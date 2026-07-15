/**
 * Ambient module declarations for the web app.
 *
 * The shell imports design-token stylesheets as side effects
 * (`import "@agency/ui-kit/styles.css"`, `import "./styles.css"`). Those
 * specifiers resolve to real `.css` files, which TypeScript has no types for,
 * so we declare them as empty modules. The root tsconfig is off-limits, so the
 * declaration lives here inside `apps/web/src/`.
 */
declare module "*.css";
