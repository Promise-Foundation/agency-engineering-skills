/**
 * The installed plugin set (compile-time registration).
 *
 * Two read-only skills over static, file-backed sources -- LTP and Hypothesize --
 * plus one LIVE, writable demo (the ZPD-store stand-in). All three run on the
 * same shell, unchanged, which is the proof that mutable data hosts cleanly the
 * moment a real skill needs it.
 */

import type { AgencySkillPlugin } from "@agency/skill-sdk";
import { ltpPlugin } from "@agency/ltp-plugin";
import { hypothesizePlugin } from "@agency/hypothesize-plugin";
import { promisifyPlugin } from "@agency/promisify-plugin";
import { zpdDemoPlugin } from "./demo/zpd-demo";

export const installedPlugins: AgencySkillPlugin[] = [
  ltpPlugin,
  hypothesizePlugin,
  promisifyPlugin,
  zpdDemoPlugin,
];
