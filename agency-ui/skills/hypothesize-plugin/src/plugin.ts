import type { AgencySkillPlugin } from "@agency/skill-sdk";
import { manifestSource } from "@agency/core";
import "./hypothesize.css";
import { hypothesizeMapping } from "./mapping";
import { HypothesisCard, HypothesisTable, HypothesisView } from "./views";

/** hypothesize as plugin #2: proves the abstractions generalize beyond LTP, and
 * completes the cross-skill link (an LTP claim VERIFIED_BY one of these). */
export const hypothesizePlugin: AgencySkillPlugin = {
  manifest: {
    id: "hypothesize",
    name: "Hypothesize",
    version: "0.1.0",
    description: "Track an honest empirical status for each hypothesis, apart from any logic.",
    recommendedDependencies: [
      {
        capability: "norms.read.v1",
        reason: "Reuse Promisify's normative domain context without making it epistemic evidence.",
      },
    ],
    provides: ["hypothesis.read.v1"],
    contributions: {
      navigation: [{ id: "hyp.nav", label: "Hypotheses", to: "/hypotheses", order: 20 }],
      routes: [{ id: "hyp.index", path: "/hypotheses", title: "Hypotheses", component: HypothesisTable }],
      dashboardCards: [{ id: "hyp.card", title: "Hypotheses", component: HypothesisCard, order: 20 }],
      resourceTypes: [{ type: "hypothesis", label: "Hypothesis" }],
      resourceViews: [{ id: "hyp.view", resourceTypes: ["hypothesis"], component: HypothesisView }],
      commands: [{ id: "hypothesize.open", title: "Hypotheses: open the list" }],
    },
  },

  activate(context) {
    const source = manifestSource({
      id: "hypothesize:research-status",
      ownerSkill: "hypothesize",
      load: async () => {
        const response = await fetch("/api/hypothesize/artifacts.json", { cache: "no-store" });
        if (!response.ok) throw new Error(`hypothesize artifact bundle not found (${response.status})`);
        return response.json();
      },
      mapping: hypothesizeMapping,
    });
    const unregisterSource = context.resources.registerSource(source);
    const unregisterCapability = context.capabilities.register("hypothesis.read.v1", {
      list: (domain: string) => context.resources.list({ type: "hypothesis", domain }),
    });
    const unregisterCommand = context.commands.register("hypothesize.open", () => {
      context.navigation.navigate("/hypotheses");
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
