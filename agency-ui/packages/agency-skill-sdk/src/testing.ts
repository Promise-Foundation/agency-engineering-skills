/**
 * The conformance kit. Every source and plugin passes the same checks, so the
 * mutation seam stays honest: a source's declared capabilities must match its
 * methods, and a `static` (reproducible, file-backed) source can *never* be
 * writable. These are pure functions returning problems, so any test framework
 * can drive them (`expect(checkSourceContract(src)).toEqual([])`).
 */

import type { AgencySkillPlugin } from "./plugin";
import type { ResourceMutation, ResourceSource } from "./resources";

export interface ConformanceProblem {
  code: string;
  message: string;
}

const SEMVER = /^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/;

export function checkSourceContract(source: ResourceSource): ConformanceProblem[] {
  const problems: ConformanceProblem[] = [];
  const push = (code: string, message: string) => problems.push({ code, message });

  if (source.capabilities.readable !== true) {
    push("readable-required", "every source must declare readable: true");
  }
  if (typeof source.list !== "function" || typeof source.get !== "function") {
    push("read-methods-required", "a source must implement list() and get()");
  }
  if (source.capabilities.watchable && typeof source.watch !== "function") {
    push("watchable-without-watch", "capabilities.watchable is true but watch() is missing");
  }
  if (!source.capabilities.watchable && typeof source.watch === "function") {
    push("watch-without-capability", "watch() is present but capabilities.watchable is false");
  }
  if (source.capabilities.writable && typeof source.apply !== "function") {
    push("writable-without-apply", "capabilities.writable is true but apply() is missing");
  }
  if (!source.capabilities.writable && typeof source.apply === "function") {
    push("apply-without-capability", "apply() is present but capabilities.writable is false");
  }
  // The invariant that protects reproducibility.
  if (source.determinism === "static" && source.capabilities.writable) {
    push(
      "static-must-not-write",
      "a static source cannot be writable -- that would break the reproducibility " +
        "guarantee read-only skills depend on",
    );
  }
  if (source.types.length === 0) {
    push("no-types", "a source must declare at least one resource type");
  }
  if (!source.id) push("no-id", "a source must have an id");
  if (!source.ownerSkill) push("no-owner", "a source must declare its ownerSkill");
  return problems;
}

/** Behavioral: a non-writable source must reject a mutation rather than silently accept it. */
export async function checkSourceRejectsWrites(
  source: ResourceSource,
): Promise<ConformanceProblem[]> {
  if (source.capabilities.writable) return [];
  const mutation: ResourceMutation = {
    kind: "created",
    ref: { type: source.types[0] ?? "x", id: "__conformance__" },
    data: {},
  };
  if (typeof source.apply !== "function") return []; // correct: no write path at all
  try {
    await source.apply(mutation);
    return [
      { code: "readonly-accepted-write", message: "a non-writable source accepted a mutation" },
    ];
  } catch {
    return [];
  }
}

export function checkPluginManifest(plugin: AgencySkillPlugin): ConformanceProblem[] {
  const problems: ConformanceProblem[] = [];
  const push = (code: string, message: string) => problems.push({ code, message });
  const { manifest } = plugin;

  if (!manifest.id) push("no-id", "manifest.id is required");
  if (!manifest.name) push("no-name", "manifest.name is required");
  if (!SEMVER.test(manifest.version)) {
    push("bad-version", `manifest.version ${manifest.version} is not semantic`);
  }
  if (typeof plugin.activate !== "function") {
    push("no-activate", "a plugin must implement activate()");
  }

  const c = manifest.contributions ?? {};
  const ids: string[] = [
    ...(c.navigation ?? []),
    ...(c.routes ?? []),
    ...(c.commands ?? []),
    ...(c.workspacePanels ?? []),
    ...(c.resourceViews ?? []),
    ...(c.inspectors ?? []),
    ...(c.dashboardCards ?? []),
    ...(c.promiseTypes ?? []),
  ].map((item) => item.id);
  const seen = new Set<string>();
  for (const id of ids) {
    if (seen.has(id)) push("duplicate-contribution-id", `duplicate contribution id ${id}`);
    seen.add(id);
  }
  for (const route of c.routes ?? []) {
    if (!route.path.startsWith("/")) {
      push("bad-route-path", `route ${route.id} path must start with "/" (${route.path})`);
    }
  }
  for (const capability of manifest.provides ?? []) {
    if (!capability) push("empty-capability", "provides[] contains an empty capability id");
  }
  return problems;
}

/** Convenience: throw with a readable summary if any problem is found. */
export function assertNoProblems(problems: ConformanceProblem[], label = "conformance"): void {
  if (problems.length) {
    throw new Error(
      `${label} failed:\n` + problems.map((p) => `  [${p.code}] ${p.message}`).join("\n"),
    );
  }
}
