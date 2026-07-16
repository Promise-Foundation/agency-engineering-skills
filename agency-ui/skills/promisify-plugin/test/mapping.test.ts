import { describe, expect, it } from "vitest";
import { DOMAIN_RESOURCE_TYPE } from "@agency/skill-sdk";
import { promisifyMapping, type Explorer } from "../src/mapping";

describe("promisify domain mapping", () => {
  it("publishes the discovered hierarchy through the shared domain resource type", () => {
    const explorer: Explorer = {
      repository: { name: "example" },
      domains: [
        {
          domain: "/",
          parent: null,
          depth: 0,
          children: ["/biology"],
          subjects: ["."],
          declaredCount: 0,
          effectivePromiseCount: 0,
        },
        {
          domain: "/biology",
          parent: "/",
          depth: 1,
          children: [],
          subjects: ["biology"],
          declaredCount: 1,
          effectivePromiseCount: 1,
        },
      ],
      effective: {},
      promises: [],
      assessments: [],
      views: [],
      trust: [],
    };

    const domains = promisifyMapping
      .toResources(explorer)
      .filter((resource) => resource.type === DOMAIN_RESOURCE_TYPE);

    expect(domains.map((resource) => resource.id)).toEqual(["/", "/biology"]);
    expect(domains[1].data).toMatchObject({
      path: "/biology",
      parent: "/",
      depth: 1,
      subjects: ["biology"],
    });
  });
});
