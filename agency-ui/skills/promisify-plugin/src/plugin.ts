import { DOMAIN_RESOURCE_TYPE, type AgencySkillPlugin } from "@agency/skill-sdk";
import { manifestSource } from "@agency/core";
import "./promisify.css";
import { promisifyMapping } from "./mapping";
import { PromiseView, PromisesCard } from "./views";
import { PromisesWorkspace } from "./workspace";

/** Promisify as a read-only explorer: one lens over `.norms/`
 * data and a safe composer for the agent. It reads the JSON emitted by
 * `norms.py explorer`; every action button composes an agent instruction rather
 * than writing policy from the browser. */
export const promisifyPlugin: AgencySkillPlugin = {
  manifest: {
    id: "promisify",
    name: "Promises",
    version: "0.1.0",
    description: "What is expected in this domain, and why does this observer believe it is being kept?",
    provides: ["norms.read.v1"],
    contributions: {
      navigation: [{ id: "promisify.nav", label: "Promises", to: "/promises", order: 40 }],
      routes: [{ id: "promisify.workspace", path: "/promises", title: "Promises", component: PromisesWorkspace }],
      dashboardCards: [{ id: "promisify.card", title: "Normative promises", component: PromisesCard, order: 40 }],
      resourceTypes: [
        { type: DOMAIN_RESOURCE_TYPE, label: "Domain" },
        { type: "norms.model", label: "Norms model" },
        { type: "norms.promise", label: "Promise" },
      ],
      resourceViews: [{ id: "promisify.promise.view", resourceTypes: ["norms.promise"], component: PromiseView }],
      commands: [{ id: "promisify.open", title: "Promises: open the explorer" }],
    },
  },

  activate(context) {
    const source = manifestSource({
      id: "promisify:explorer",
      ownerSkill: "promisify",
      load: async () => {
        const response = await fetch("/api/promisify/explorer.json", { cache: "no-store" });
        if (!response.ok) throw new Error(`promisify explorer not found (${response.status})`);
        return response.json();
      },
      mapping: promisifyMapping,
    });
    const unregisterSource = context.resources.registerSource(source);
    const unregisterCapability = context.capabilities.register("norms.read.v1", {
      model: () => context.resources.get({ type: "norms.model", id: "model" }),
    });
    const unregisterCommand = context.commands.register("promisify.open", () => {
      context.navigation.navigate("/promises");
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
