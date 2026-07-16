import { describe, expect, it } from "vitest";
import { ltpMapping, scopedLtpId, type LtpArtifactBundle, type LtpModel } from "../src/mapping";

function model(name: string): LtpModel {
  return {
    project: { name },
    entities: [
      { id: "G-1", kind: "goal", statement: `${name} goal` },
      { id: "NC-1", kind: "necessary_condition", statement: `${name} condition` },
    ],
    causal_claims: [],
    gates: [],
    views: {},
    health: {
      counts: { error: 0, warning: 0, info: 0 },
      publishable: true,
      diagnostics: [],
    },
  };
}

describe("LTP domain artifact mapping", () => {
  it("keeps equal local ids separate across domains", () => {
    const bundle: LtpArtifactBundle = {
      artifacts: [
        { domain: "/skills/ltp", manifest: model("LTP") },
        { domain: "/skills/zpd", manifest: model("ZPD") },
      ],
    };

    const resources = ltpMapping.toResources(bundle);
    const goals = resources.filter(
      (resource) => resource.type === "ltp.entity" && resource.data.id === "G-1",
    );

    expect(goals.map((resource) => resource.domain)).toEqual(["/skills/ltp", "/skills/zpd"]);
    expect(goals.map((resource) => resource.id)).toEqual([
      scopedLtpId("/skills/ltp", "G-1"),
      scopedLtpId("/skills/zpd", "G-1"),
    ]);
    expect(new Set(goals.map((resource) => resource.id)).size).toBe(2);
  });
});
