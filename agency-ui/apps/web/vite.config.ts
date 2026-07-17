import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";
import { join } from "node:path";

// Resolve workspace packages to their TypeScript source so Vite transpiles them
// (Vite does not transform TS inside linked node_modules workspace deps).
// More-specific subpaths must precede the bare package alias.
const at = (path: string) => fileURLToPath(new URL(path, import.meta.url));

export default defineConfig({
  plugins: [
    react(),
    {
      name: "dynamic-ltp-e2e-fixtures",
      configureServer(server) {
        server.middlewares.use((request, response, next) => {
          const fixture = request.headers["x-e2e-fixture"];
          if (typeof fixture !== "string" || !request.url?.startsWith("/api/")) {
            next();
            return;
          }
          const relative = request.url.split("?", 1)[0].replace(/^\/api\//, "");
          try {
            const fixtureDirectory = fixture.startsWith("history-") ? "history-baseline" : fixture;
            const path = join(at("../../features/fixtures/"), fixtureDirectory, relative);
            let body = JSON.parse(readFileSync(path, "utf8"));
            if (fixture === "history-clean" && relative === "ltp/artifacts.json") {
              const model = body.artifacts[0].manifest;
              model.learning_obligations = [];
              model.health = { counts: { error: 0, warning: 0, info: 0 }, publishable: true, diagnostics: [] };
            }
            if (fixture === "history-supported" && relative === "hypothesize/artifacts.json") {
              const manifest = body.artifacts[0].manifest;
              manifest.hypotheses[0].conclusion = "supported";
              manifest.hypotheses[0].evidence = ["STUDY-1"];
              manifest.evidence = [{
                id: "STUDY-1", title: "Qualified preregistered field study",
                maturity: "external_replication", outcome: "supported",
                qualified: true, preregistered: true, hypotheses: ["HYP-1"]
              }];
            }
            response.statusCode = 200;
            response.setHeader("content-type", "application/json");
            response.end(JSON.stringify(body));
          } catch {
            next();
          }
        });
      },
    },
  ],
  resolve: {
    alias: {
      "@agency/skill-sdk/testing": at("../../packages/agency-skill-sdk/src/testing.ts"),
      "@agency/skill-sdk": at("../../packages/agency-skill-sdk/src/index.ts"),
      "@agency/core": at("../../packages/agency-core/src/index.ts"),
      "@agency/ui-kit/styles.css": at("../../packages/ui-kit/src/styles.css"),
      "@agency/ui-kit": at("../../packages/ui-kit/src/index.ts"),
      "@agency/ltp-plugin": at("../../skills/ltp-plugin/src/index.ts"),
      "@agency/hypothesize-plugin": at("../../skills/hypothesize-plugin/src/index.ts"),
      "@agency/promisify-plugin": at("../../skills/promisify-plugin/src/index.ts"),
    },
  },
  server: { port: 5197, strictPort: true, host: "127.0.0.1" },
});
