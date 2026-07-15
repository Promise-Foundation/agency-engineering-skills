import { describe, expect, it, vi } from "vitest";
import type { AgencySkillPlugin, ResourceSource } from "@agency/skill-sdk";
import {
  checkPluginManifest,
  checkSourceContract,
  checkSourceRejectsWrites,
} from "@agency/skill-sdk/testing";
import {
  FederatedResourceService,
  PluginHost,
  createMemorySource,
  manifestSource,
  resolveOrder,
} from "@agency/core";

const staticSource = manifestSource({
  id: "ltp:manifest",
  ownerSkill: "ltp",
  load: async () => ({ items: [{ id: "CLM-1" }] }),
  mapping: {
    types: ["ltp.claim"],
    toResources: (m) =>
      (m as { items: { id: string }[] }).items.map((i) => ({
        id: i.id,
        type: "ltp.claim",
        ownerSkill: "ltp",
        schemaVersion: 1,
        data: i,
        provenance: { determinism: "static" as const, sourceId: "ltp:manifest" },
      })),
    toRelations: () => [
      {
        id: "rel-1",
        type: "VERIFIED_BY",
        from: { type: "ltp.claim", id: "CLM-1" },
        to: { type: "hypothesis", id: "HYP-1" },
      },
    ],
  },
});

const liveSource = createMemorySource({
  id: "zpd:store",
  ownerSkill: "zpd",
  types: ["zpd.learning-job"],
});

describe("source conformance", () => {
  it("a static manifest source passes and is not writable", async () => {
    expect(checkSourceContract(staticSource)).toEqual([]);
    expect(await checkSourceRejectsWrites(staticSource)).toEqual([]);
    expect(staticSource.determinism).toBe("static");
    expect(staticSource.capabilities.writable).toBe(false);
  });

  it("a live memory source passes and supports watch + apply", async () => {
    expect(checkSourceContract(liveSource)).toEqual([]);
    expect(liveSource.capabilities.writable).toBe(true);
    const seen = vi.fn();
    const stop = liveSource.watch!({ type: "zpd.learning-job" }, seen);
    await liveSource.apply!({ kind: "created", ref: { type: "zpd.learning-job", id: "42" }, data: { blocked: true } });
    expect(seen).toHaveBeenCalledOnce();
    expect(await liveSource.get({ type: "zpd.learning-job", id: "42" })).not.toBeNull();
    stop();
  });

  it("rejects a static source that claims to be writable (protects reproducibility)", () => {
    const cheating: ResourceSource = {
      ...staticSource,
      determinism: "static",
      capabilities: { readable: true, watchable: false, writable: true },
      apply: async () => ({ summary: "nope" }),
    };
    const problems = checkSourceContract(cheating).map((p) => p.code);
    expect(problems).toContain("static-must-not-write");
  });
});

describe("federation", () => {
  it("routes writes to the live source and rejects writes to read-only types", async () => {
    const resources = new FederatedResourceService();
    resources.registerSource(staticSource);
    resources.registerSource(createMemorySource({ id: "zpd:store2", ownerSkill: "zpd", types: ["zpd.learning-job"] }));

    expect(resources.canWrite("zpd.learning-job")).toBe(true);
    expect(resources.canWrite("ltp.claim")).toBe(false);

    await resources.apply({ kind: "created", ref: { type: "zpd.learning-job", id: "1" }, data: {} });
    await expect(
      resources.apply({ kind: "created", ref: { type: "ltp.claim", id: "X" }, data: {} }),
    ).rejects.toThrow(/no writable source/);
  });

  it("federates a cross-skill relation from whichever source knows it", async () => {
    const resources = new FederatedResourceService();
    resources.registerSource(staticSource);
    const relations = await resources.relations({ type: "hypothesis", id: "HYP-1" });
    expect(relations.map((r) => r.id)).toContain("rel-1");
  });
});

function plugin(
  id: string,
  extra: Partial<AgencySkillPlugin["manifest"]> = {},
  activate: AgencySkillPlugin["activate"] = () => ({}),
): AgencySkillPlugin {
  return { manifest: { id, name: id, version: "0.1.0", description: id, ...extra }, activate };
}

describe("plugin host", () => {
  it("activates a capability provider before its consumer", async () => {
    const provider = plugin("hypothesize", { provides: ["hypothesis.create.v1"] });
    const consumer = plugin("ltp", { requires: [{ capability: "hypothesis.create.v1" }] });
    const { order } = resolveOrder([consumer, provider]);
    expect(order.map((p) => p.manifest.id)).toEqual(["hypothesize", "ltp"]);
  });

  it("isolates a plugin with a missing required dependency", async () => {
    const host = new PluginHost();
    host.register(plugin("ok"));
    host.register(plugin("broken", { requires: [{ capability: "does.not.exist" }] }));
    const result = await host.activateAll();
    expect(result.activated).toContain("ok");
    expect(result.failed.map((f) => f.id)).toContain("broken");
  });

  it("aggregates contributions from activated plugins", async () => {
    const host = new PluginHost();
    const Comp = () => null;
    host.register(
      plugin("ltp", {
        contributions: { routes: [{ id: "ltp.home", path: "/ltp", title: "LTP", component: Comp }] },
      }),
    );
    await host.activateAll();
    expect(host.contributions().routes.map((r) => r.id)).toEqual(["ltp.home"]);
  });
});

describe("manifest conformance", () => {
  it("flags duplicate contribution ids and a bad version", () => {
    const bad = plugin("x", {
      version: "not-semver",
      contributions: {
        routes: [{ id: "dup", path: "/a", title: "A", component: () => null }],
        commands: [{ id: "dup", title: "dup" }],
      },
    });
    const codes = checkPluginManifest(bad).map((p) => p.code);
    expect(codes).toContain("bad-version");
    expect(codes).toContain("duplicate-contribution-id");
  });
});
