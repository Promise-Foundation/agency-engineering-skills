import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

const resolve = (path: string) => fileURLToPath(new URL(path, import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      "@agency/skill-sdk/testing": resolve("./packages/agency-skill-sdk/src/testing.ts"),
      "@agency/skill-sdk": resolve("./packages/agency-skill-sdk/src/index.ts"),
      "@agency/core": resolve("./packages/agency-core/src/index.ts"),
      "@agency/ui-kit": resolve("./packages/ui-kit/src/index.ts"),
    },
  },
  test: {
    environment: "node",
    include: ["packages/*/test/**/*.test.ts", "skills/*/test/**/*.test.ts"],
  },
});
