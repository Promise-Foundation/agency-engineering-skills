import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

// Resolve workspace packages to their TypeScript source so Vite transpiles them
// (Vite does not transform TS inside linked node_modules workspace deps).
// More-specific subpaths must precede the bare package alias.
const at = (path: string) => fileURLToPath(new URL(path, import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@agency/skill-sdk/testing": at("../../packages/agency-skill-sdk/src/testing.ts"),
      "@agency/skill-sdk": at("../../packages/agency-skill-sdk/src/index.ts"),
      "@agency/core": at("../../packages/agency-core/src/index.ts"),
      "@agency/ui-kit/styles.css": at("../../packages/ui-kit/src/styles.css"),
      "@agency/ui-kit": at("../../packages/ui-kit/src/index.ts"),
      "@agency/ltp-plugin": at("../../skills/ltp-plugin/src/index.ts"),
      "@agency/hypothesize-plugin": at("../../skills/hypothesize-plugin/src/index.ts"),
    },
  },
  server: { port: 5178, host: "127.0.0.1" },
});
