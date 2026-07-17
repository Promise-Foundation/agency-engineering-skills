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

  it("publishes semantic relations and causal-outcome predictions without collapsing them into claims", () => {
    const dynamic = model("Dynamic");
    dynamic.causal_claims = [
      { id: "CLM-1", premises: ["G-1"], conclusion: "NC-1", logic_status: "scrutinized" },
    ];
    dynamic.semantic_relations = [
      { id: "REL-1", source: "G-1", target: "NC-1", relation: "prevents" },
    ];
    dynamic.predicted_effects = [
      { id: "PRED-1", source_claim: "CLM-1", statement: "Outcome changes" },
    ];
    dynamic.prediction_evaluations = [
      { id: "EVAL-PRED-1", prediction: "PRED-1", as_of: "2026-07-17", result: "inconclusive" },
    ];

    const bundle: LtpArtifactBundle = { artifacts: [{ domain: "/dynamic", manifest: dynamic }] };
    const resources = ltpMapping.toResources(bundle);
    expect(resources.find((resource) => resource.type === "ltp.relation")?.status).toBe("prevents");
    expect(resources.find((resource) => resource.type === "ltp.prediction")?.status).toBe("inconclusive");

    const relations = ltpMapping.toRelations?.(bundle) ?? [];
    expect(relations.map((relation) => relation.type)).toEqual(["PREVENTS", "PREDICTS"]);
  });
});
