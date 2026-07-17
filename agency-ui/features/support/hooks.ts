import { After, AfterAll, Before, BeforeAll, setDefaultTimeout } from "@cucumber/cucumber";
import { closeSharedBrowser, launchSharedBrowser, type ShellWorld } from "./world.ts";

setDefaultTimeout(30_000);

BeforeAll(async function () {
  await launchSharedBrowser();
});

// Default deterministic fixture; individual scenarios/features may override by
// setting this.fixtureName before opening the dashboard.
Before(function (this: ShellWorld) {
  this.fixtureName = "history-baseline";
});

After(async function (this: ShellWorld) {
  await this.close();
});

AfterAll(async function () {
  await closeSharedBrowser();
});
