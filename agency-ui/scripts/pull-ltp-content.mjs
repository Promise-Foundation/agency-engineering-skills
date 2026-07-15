#!/usr/bin/env node
/**
 * Feed an LTP project's generated content into the shell.
 *
 * The LTP engine writes `<project>/ltp/generated/dashboard-model.json` when you
 * run `ltp sync`. This copies that file into the app's served location
 * (`apps/web/public/api/ltp/`), so the shell renders real, previously-generated
 * content -- no rebuild of the engine, no hand-editing.
 *
 *   node scripts/pull-ltp-content.mjs [ltpProjectRoot]
 *   npm run content:pull -- ../some/project
 *
 * Default project root: the committed demo at content/ltp-demo.
 */

import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const appPublic = resolve(here, "..", "apps", "web", "public", "api");

const projectRoot = resolve(process.cwd(), process.argv[2] ?? resolve(here, "..", "content", "ltp-demo"));
const source = join(projectRoot, "ltp", "generated", "dashboard-model.json");

if (!existsSync(source)) {
  console.error(`No generated LTP content at:\n  ${source}\n`);
  console.error(`Run \`ltp --root ${projectRoot} sync\` first (the engine writes the generated/ tree).`);
  process.exit(1);
}

const dest = join(appPublic, "ltp", "dashboard-model.json");
mkdirSync(dirname(dest), { recursive: true });
copyFileSync(source, dest);
console.log(`Pulled LTP content:\n  ${source}\n  -> ${dest}`);
console.log("The shell will serve it at /api/ltp/dashboard-model.json.");
