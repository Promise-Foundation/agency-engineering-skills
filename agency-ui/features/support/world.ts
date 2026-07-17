// Playwright-backed Cucumber World for the dynamic dashboard, mirroring the
// reference project's world.ts. Steps drive the shell through its PUBLIC SURFACE
// only (getByTestId / getByRole) -- never internal modules -- so a feature proves
// observable behaviour, not implementation shape.
//
// Determinism: like the reference app's `x-e2e-fixture` header, the shell must, in
// e2e mode, load a named fixture ResourceSource instead of live/generated data, so
// the timeline/attention/disagreement fixtures are reproducible and offline. That
// injection point is the one shell change Workstream E requires (see ROADMAP,
// "Workstream E, shell wiring"): a fixture manifestSource selected by this header.
import { setWorldConstructor, World, type IWorldOptions } from "@cucumber/cucumber";
import { chromium, type Browser, type BrowserContext, type Page } from "playwright";

export let sharedBrowser: Browser | undefined;

export async function launchSharedBrowser(): Promise<void> {
  sharedBrowser = await chromium.launch({ headless: process.env.HEADED !== "1" });
}

export async function closeSharedBrowser(): Promise<void> {
  await sharedBrowser?.close();
  sharedBrowser = undefined;
}

export class ShellWorld extends World {
  context: BrowserContext | undefined;
  page: Page | undefined;
  // Deterministic fixture the shell loads in e2e mode. Set per-scenario in hooks.
  fixtureName = "history-baseline";
  memory: Record<string, unknown> = {};

  constructor(options: IWorldOptions) {
    super(options);
  }

  async openDashboard(): Promise<Page> {
    if (!sharedBrowser) throw new Error("Playwright browser has not been launched");
    this.context ??= await sharedBrowser.newContext({
      baseURL: process.env.BASE_URL ?? "http://127.0.0.1:5197",
      extraHTTPHeaders: { "x-e2e-fixture": this.fixtureName },
    });
    this.page ??= await this.context.newPage();
    await this.page.goto("/ltp?domain=%2Fdynamic", { waitUntil: "domcontentloaded" });
    // Contract: the shell root marks itself hydrated so steps do not race the app.
    await this.page.locator('[data-testid="agency-shell"]').waitFor({ state: "attached" });
    return this.page;
  }

  requirePage(): Page {
    if (!this.page) throw new Error("The dashboard has not been opened in this scenario");
    return this.page;
  }

  async close(): Promise<void> {
    await this.context?.close();
    this.context = undefined;
    this.page = undefined;
    this.memory = {};
  }
}

setWorldConstructor(ShellWorld);
