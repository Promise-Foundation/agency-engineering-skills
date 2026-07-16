/**
 * The installed plugin set (compile-time registration).
 *
 * Three read-only skills over static, file-backed sources -- Promisify, LTP,
 * and Hypothesize -- plus a live, writable ZPD stand-in. They all run through
 * the same domain and resource contracts.
 */

import type { AgencySkillPlugin } from "@agency/skill-sdk";
import { ltpPlugin } from "@agency/ltp-plugin";
import { hypothesizePlugin } from "@agency/hypothesize-plugin";
import { promisifyPlugin } from "@agency/promisify-plugin";
import { zpdPlugin } from "./demo/zpd-demo";

export const installedPlugins: AgencySkillPlugin[] = [
  ltpPlugin,
  hypothesizePlugin,
  promisifyPlugin,
  zpdPlugin,
];
