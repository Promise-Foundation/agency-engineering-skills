import type { AgencySkillPlugin } from "@agency/skill-sdk";
import { manifestSource } from "@agency/core";
import { ltpMapping } from "./mapping";
import { LifecycleInspector, PredictionInspector } from "./dynamic";
import {
  LtpClaimView,
  LtpEntityView,
  LtpHealthCard,
  LtpLearningCard,
  LtpModelView,
  LtpOverview,
  LtpRelationView,
} from "./views";

/** LTP as a read-only plugin over domain-addressed generated dashboard models. */
export const ltpPlugin: AgencySkillPlugin = {
  manifest: {
    id: "ltp",
    name: "LTP",
    version: "0.1.0",
    description: "Reconstruct a repository's logic as one validated Theory-of-Constraints model.",
    recommendedDependencies: [
      {
        capability: "norms.read.v1",
        reason: "Reuse Promisify domains and expose LTP-owned types and tokens for assessment.",
      },
    ],
    optionalDependencies: [
      {
        capability: "hypothesis.read.v1",
        reason: "Show empirical standing linked to LTP-owned causal claims.",
      },
    ],
    provides: ["ltp.model.v1"],
    contributions: {
      navigation: [{ id: "ltp.nav", label: "LTP", to: "/ltp", order: 10 }],
      routes: [{ id: "ltp.overview", path: "/ltp", title: "LTP", component: LtpOverview }],
      dashboardCards: [
        { id: "ltp.health", title: "LTP model health", component: LtpHealthCard, order: 10 },
        { id: "ltp.learning", title: "LTP learning loop", component: LtpLearningCard, order: 11 },
      ],
      resourceTypes: [
        { type: "ltp.model", label: "LTP model" },
        { type: "ltp.entity", label: "LTP entity" },
        { type: "ltp.claim", label: "Causal claim" },
        { type: "ltp.relation", label: "Semantic relation" },
        { type: "ltp.prediction", label: "Causal-outcome prediction" },
      ],
      promiseTypes: [
        {
          id: "ltp.entities.promise-type",
          resourceType: "ltp.entity",
          domainPrefix: "/skills/ltp/entities",
          subtypeField: "kind",
          typeAssessments: "maintainer",
          tokenAssessments: "user",
        },
        {
          id: "ltp.causal-claims.promise-type",
          resourceType: "ltp.claim",
          domainPrefix: "/skills/ltp/relations",
          fixedSubtype: "causal-claim",
          typeAssessments: "maintainer",
          tokenAssessments: "user",
        },
      ],
      resourceViews: [
        { id: "ltp.model.view", resourceTypes: ["ltp.model"], component: LtpModelView },
        { id: "ltp.entity.view", resourceTypes: ["ltp.entity"], component: LtpEntityView },
        { id: "ltp.claim.view", resourceTypes: ["ltp.claim"], component: LtpClaimView },
        { id: "ltp.relation.view", resourceTypes: ["ltp.relation"], component: LtpRelationView },
        { id: "ltp.prediction.view", resourceTypes: ["ltp.prediction"], component: PredictionInspector },
      ],
      inspectors: [
        { id: "ltp.entity.lifecycle", resourceTypes: ["ltp.entity"], component: LifecycleInspector },
        { id: "ltp.claim.lifecycle", resourceTypes: ["ltp.claim"], component: LifecycleInspector },
        { id: "ltp.relation.lifecycle", resourceTypes: ["ltp.relation"], component: LifecycleInspector },
      ],
      commands: [{ id: "ltp.open", title: "LTP: open the overview" }],
    },
  },

  activate(context) {
    const source = manifestSource({
      id: "ltp:dashboard",
      ownerSkill: "ltp",
      load: async () => {
        const response = await fetch("/api/ltp/artifacts.json", { cache: "no-store" });
        if (!response.ok) throw new Error(`LTP artifact bundle not found (${response.status})`);
        return response.json();
      },
      mapping: ltpMapping,
    });
    const unregisterSource = context.resources.registerSource(source);

    const unregisterCapability = context.capabilities.register("ltp.model.v1", {
      getModel: (domain: string) => context.resources.list({ type: "ltp.model", domain }),
    });

    const unregisterCommand = context.commands.register("ltp.open", () => {
      context.navigation.navigate("/ltp");
    });

    return {
      deactivate() {
        unregisterCommand();
        unregisterCapability();
        unregisterSource();
      },
    };
  },
};
