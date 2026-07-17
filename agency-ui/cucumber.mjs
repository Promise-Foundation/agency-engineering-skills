// Cucumber config for agency-ui's dynamic-dashboard acceptance suite.
//
// Introduced by the dynamic-ltp program (docs/dynamic-ltp/ROADMAP.md, Workstream E),
// mirroring the reference project Turing_College/djosep-AE.AFA.1.5. agency-ui's unit
// layer stays on vitest (`npm test`); this is the browser-driven BDD layer.
//
// Every scenario runs against the real shell through its public surface. The
// deterministic fixture source is selected by the browser context's E2E header.
const config = {
  paths: ["features/**/*.feature"],
  import: [
    "tsx/esm",
    "features/support/**/*.ts",
    "features/step_definitions/**/*.ts",
  ],
  format: ["progress"],
  formatOptions: { snippetInterface: "async-await" },
  parallel: 1,
  tags: "not @manual",
};

export default config;
