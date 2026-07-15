import type { AgencySkillPlugin } from "@agency/skill-sdk";
import { manifestSource } from "@agency/core";
import { ltpMapping } from "./mapping";
import { LtpClaimView, LtpEntityView, LtpHealthCard, LtpModelView, LtpOverview } from "./views";

/** LTP as read-only plugin #1: a static source over its generated dashboard model. */
export const ltpPlugin: AgencySkillPlugin = {
  manifest: {
    id: "ltp",
    name: "LTP",
    version: "0.1.0",
    description: "Reconstruct a repository's logic as one validated Theory-of-Constraints model.",
    provides: ["ltp.model.v1"],
    contributions: {
      navigation: [{ id: "ltp.nav", label: "LTP", to: "/ltp", order: 10 }],
      routes: [{ id: "ltp.overview", path: "/ltp", title: "LTP", component: LtpOverview }],
      dashboardCards: [{ id: "ltp.health", title: "LTP model health", component: LtpHealthCard, order: 10 }],
      resourceTypes: [
        { type: "ltp.model", label: "LTP model" },
        { type: "ltp.entity", label: "LTP entity" },
        { type: "ltp.claim", label: "Causal claim" },
      ],
      resourceViews: [
        { id: "ltp.model.view", resourceTypes: ["ltp.model"], component: LtpModelView },
        { id: "ltp.entity.view", resourceTypes: ["ltp.entity"], component: LtpEntityView },
        { id: "ltp.claim.view", resourceTypes: ["ltp.claim"], component: LtpClaimView },
      ],
      commands: [{ id: "ltp.open", title: "LTP: open the overview" }],
    },
  },

  activate(context) {
    const source = manifestSource({
      id: "ltp:dashboard",
      ownerSkill: "ltp",
      load: async () => {
        const response = await fetch("/api/ltp/dashboard-model.json", { cache: "no-store" });
        if (!response.ok) throw new Error(`LTP manifest not found (${response.status})`);
        return response.json();
      },
      mapping: ltpMapping,
    });
    const unregisterSource = context.resources.registerSource(source);

    const unregisterCapability = context.capabilities.register("ltp.model.v1", {
      getModel: () => context.resources.get({ type: "ltp.model", id: "model" }),
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
