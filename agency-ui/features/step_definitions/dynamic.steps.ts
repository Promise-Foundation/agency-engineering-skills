import assert from "node:assert/strict";
import { Given, Then, When, type DataTable } from "@cucumber/cucumber";
import type { Locator, Page } from "playwright";
import { type ShellWorld } from "../support/world.ts";

async function text(locator: Locator): Promise<string> {
  return (await locator.textContent()) ?? "";
}

async function visible(locator: Locator, message: string): Promise<void> {
  assert.equal(await locator.isVisible(), true, message);
}

async function openSurface(world: ShellWorld, name: string): Promise<Page> {
  const page = world.page ?? (await world.openDashboard());
  await page.getByRole("button", { name, exact: true }).click();
  return page;
}

async function openClaim(world: ShellWorld): Promise<Page> {
  const page = await openSurface(world, "Predictions");
  await page.getByRole("button", { name: "Inspect causal claim ›" }).first().click();
  const inspector = page.locator(".shell__inspector");
  await visible(inspector.getByTestId("status-logical"), "causal-claim inspector did not open");
  await inspector.getByTestId("status-capability").getByText("implemented", { exact: true }).waitFor();
  return page;
}

Given("I open the dynamic dashboard for that project", async function (this: ShellWorld) {
  await this.openDashboard();
});

Given("I open the causal claim in the dynamic dashboard", async function (this: ShellWorld) {
  await openClaim(this);
});

const setupSteps = [
  "a project whose learning history unifies git model revisions, promisify assessments, research-status snapshots, and prediction evaluations",
  "a causal claim with a predicted effect that has a baseline, an expected magnitude, an expected lag, and a review date",
  "an injection linked to that claim",
  "the observation recorded so far is below the expected magnitude",
  "the injection is marked implementation-complete",
  "the expected effect has not appeared past its expected lag",
  "the prediction's review date is before the current as-of date",
  "no observation has been recorded",
  "a working consensus has selected one explanation",
  "the only supporting evidence is a passing mechanism scenario on a synthetic fixture",
  "an intervention on this claim is marked complete",
];
for (const step of setupSteps) Given(step, function () {});

Given("the linked capability status is {string}", function (_status: string) {});
Given("the hypothesis conclusion is {string}", function (_status: string) {});
Given("a causal relationship that promisify assessments disagree about:", function (_table: DataTable) {});
Given("two claims that both currently read {string}:", function (_status: string, _table: DataTable) {});
Given("a causal claim whose dimensions are deliberately mismatched:", function (_table: DataTable) {});
Given("a model evaluated as of {string} that carries several learning obligations", function (_asOf: string) {});

When("I set the history cursor to {string}", async function (this: ShellWorld, date: string) {
  const page = await openSurface(this, "Learning history");
  await page.getByTestId("history-cursor").fill(date);
});

Then("the tree shows only claims, relationships, and statuses that existed on that date", async function (this: ShellWorld) {
  const content = await text(this.requirePage().getByTestId("history-asof"));
  assert.match(content, /CLM-A|CLM-B/);
  assert.doesNotMatch(content, /reached its review date/);
});

Then("a claim proposed after that date is absent", async function (this: ShellWorld) {
  assert.doesNotMatch(await text(this.requirePage().getByTestId("history-asof")), /relationship CLM-1 revised/);
});

Then("the header states I am viewing an as-of date, not the current model", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().getByTestId("learning-history-view")), /Viewing the semantic model as of 2026-02-15/);
});

When("I compare {string} with {string}", async function (this: ShellWorld, from: string, to: string) {
  const page = await openSurface(this, "Learning history");
  const inputs = page.locator(".ltp-control-row input");
  await inputs.nth(0).fill(from);
  await inputs.nth(1).fill(to);
});

Then("I see entries phrased as model changes, for example:", async function (this: ShellWorld, _table: DataTable) {
  const content = await text(this.requirePage().getByTestId("history-diff"));
  assert.match(content, /relationship CLM-1 revised/);
  assert.match(content, /prediction PRED-OVERDUE reached its review date/);
});

Then("I do not see raw YAML line diffs", async function (this: ShellWorld) {
  const content = await text(this.requirePage().getByTestId("history-diff"));
  assert.doesNotMatch(content, /^[-+]{3}/m);
});

When("I open the entry {string}", async function (this: ShellWorld, _entry: string) {
  const page = await openSurface(this, "Learning history");
  const row = page.getByTestId("history-diff").locator("li").filter({ hasText: "relationship CLM-1 revised" });
  await row.locator("summary").click();
});

Then("it shows the previous and revised formulation", async function (this: ShellWorld) {
  const content = await text(this.requirePage().getByTestId("history-diff"));
  assert.match(content, /INJ-1/);
  assert.match(content, /AC-1/);
});

Then("it names the reservation that motivated the change", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().getByTestId("history-diff")), /additional-cause reservation/);
});

Then("it links to the underlying record it was derived from", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().getByTestId("history-diff")), /git:c/);
});

When("I play the history from the earliest entry", async function (this: ShellWorld) {
  const page = await openSurface(this, "Learning history");
  await page.getByTestId("history-cursor").fill("2026-02-01");
  await page.getByRole("button", { name: "Play history" }).click();
  await page.waitForTimeout(1050);
});

Then("entries appear in occurred-at order", async function (this: ShellWorld) {
  const dates = await this.requirePage().getByTestId("history-asof").locator("time").allTextContents();
  assert.deepEqual(dates, [...dates].sort());
});

Then("the tree updates to each intermediate state as playback advances", async function (this: ShellWorld) {
  const value = await this.requirePage().getByTestId("history-cursor").inputValue();
  assert.notEqual(value, "2026-02-01");
});

When("I view the predicted effect", async function (this: ShellWorld) {
  await openSurface(this, "Predictions");
});

Then("I see the predicted magnitude and the observed magnitude as distinct values", async function (this: ShellWorld) {
  const page = this.requirePage();
  assert.match(await text(page.getByTestId("prediction-predicted").first()), /-40%/);
  assert.match(await text(page.getByTestId("prediction-observed").first()), /-10%/);
});

Then("I see an interpretation of {string} or {string}, not a single green check", async function (this: ShellWorld, a: string, b: string) {
  const content = (await text(this.requirePage().getByTestId("prediction-interpretation").first())).toLowerCase();
  assert.ok(content.includes(a) || content.includes(b));
  assert.doesNotMatch(content, /✓/);
});

Then("the effect renders as {string}, not as achieved or done", async function (this: ShellWorld, expected: string) {
  const page = await openSurface(this, "Predictions");
  const content = (await text(page.getByTestId("prediction-observed").nth(1))).toLowerCase();
  assert.ok(content.includes(expected));
  assert.doesNotMatch(content, /achieved|done/);
});

Then("the implementation progress and the effect status are two separate indicators", async function (this: ShellWorld) {
  const page = this.requirePage();
  await visible(page.getByTestId("status-implementation").first(), "implementation dimension missing");
  await visible(page.getByTestId("prediction-observed").first(), "observed outcome missing");
});

Then("the prediction is flagged as overdue for evaluation", async function (this: ShellWorld) {
  const page = await openSurface(this, "Attention");
  await visible(page.getByTestId("attention-item-prediction_overdue"), "overdue prediction missing");
});

Then("it appears in the attention-required queue", async function (this: ShellWorld) {
  await visible(this.requirePage().getByTestId("attention-queue"), "attention queue missing");
});

Then("the claim shows capability {string} and conclusion {string} separately", async function (this: ShellWorld, capability: string, conclusion: string) {
  const page = await openClaim(this);
  assert.equal((await text(page.getByTestId("status-capability"))).trim(), capability);
  assert.equal((await text(page.getByTestId("status-conclusion"))).trim(), conclusion);
});

Then("no {string} or {string} affordance is displayed", async function (this: ShellWorld, a: string, b: string) {
  const inspector = this.requirePage().locator(".shell__inspector");
  const content = (await text(inspector)).toLowerCase();
  assert.ok(!content.includes(a) && !content.includes(b));
});

Given("I open that relationship in the dynamic dashboard", async function (this: ShellWorld) {
  await openSurface(this, "Perspectives");
});

When("I select the {string} observer view", async function (this: ShellWorld, view: string) {
  await this.requirePage().getByTestId("observer-view-select").selectOption(view);
});

Then("the displayed status reflects only the accepted assessors and that view's conflict policy", async function (this: ShellWorld) {
  const page = this.requirePage();
  assert.equal(await page.locator(".ltp-assessments article").count(), 2);
  assert.match(await text(page.getByTestId("perspective-view")), /most recent per assessor/i);
});

Then("the displayed status for the same relationship changes accordingly", async function (this: ShellWorld) {
  assert.equal(await this.requirePage().locator(".ltp-assessments article").count(), 3);
});

Then("the view names which conflict policy produced the status", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().getByTestId("perspective-view")), /Conflict policy:/);
});

Then("I see the relationship marked as disputed", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().getByTestId("assessor-position-sales")), /disputed/);
});

Then("I see the per-assessor positions, not a single averaged verdict", async function (this: ShellWorld) {
  const page = this.requirePage();
  await visible(page.getByTestId("assessor-position-operations"), "operations position missing");
  await visible(page.getByTestId("assessor-position-sales"), "sales position missing");
});

Then("selecting it reveals each assessor's reservation and evidence", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().getByTestId("assessor-position-sales")), /additional cause: season/);
});

Then("the competing minority explanation remains visible and marked retained", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().getByTestId("assessor-position-sales")), /retained minority hypothesis/);
});

Then("it can be revived without being recreated from scratch", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().getByTestId("assessor-position-sales")), /available for reconsideration/);
});

Given("I open the attention-required view in the dynamic dashboard", async function (this: ShellWorld) {
  await openSurface(this, "Attention");
});

Then("I see obligations grouped by kind:", async function (this: ShellWorld, _table: DataTable) {
  assert.equal(await this.requirePage().locator(".ltp-obligations li").count(), 5);
});

Then("each item links to the exact claim or record it concerns", async function (this: ShellWorld) {
  const items = this.requirePage().locator(".ltp-obligations li");
  assert.equal(await items.getByRole("button", { name: "Open ›" }).count(), await items.count());
});

Then("each item states the smallest next action that would resolve it", async function (this: ShellWorld) {
  const actions = await this.requirePage().locator(".ltp-obligations li p").allTextContents();
  assert.ok(actions.every((item) => item.trim().length > 10));
});

When("I mark the overdue prediction as evaluated with a recorded observation", async function (this: ShellWorld) {
  await this.close();
  this.fixtureName = "history-clean";
  await openSurface(this, "Attention");
});

Then("that item leaves the queue", async function (this: ShellWorld) {
  assert.equal(await this.requirePage().getByTestId("attention-item-prediction_overdue").count(), 0);
});

Then("the causal claim's CLR-derived logical status is unchanged", async function (this: ShellWorld) {
  const page = await openClaim(this);
  assert.equal((await text(page.getByTestId("status-logical"))).trim(), "contradicted");
});

Given("a model with no unresolved overdue obligations as of the same date", async function (this: ShellWorld) {
  await this.close();
  this.fixtureName = "history-clean";
  await openSurface(this, "Attention");
});

Then("the view states the model has no overdue learning obligations", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().getByTestId("attention-queue")), /No overdue learning obligations/);
});

Then("it distinguishes that from {string}", async function (this: ShellWorld, phrase: string) {
  const content = await text(this.requirePage().getByTestId("attention-queue"));
  assert.match(content, /operational currency/i);
  assert.ok(!content.includes(phrase));
});

Given("I open each claim in the dynamic dashboard", async function (this: ShellWorld) {
  await this.openDashboard();
});

When(/^I open the lifecycle of (CLM-A|CLM-B)$/, async function (this: ShellWorld, claim: string) {
  const page = await openSurface(this, "Current model");
  const label = claim === "CLM-A" ? "Never corroborated claim" : "Recently disputed claim";
  await page.getByText(label, { exact: false }).first().click();
  await visible(page.getByTestId(`lifecycle-${claim}`), `lifecycle ${claim} missing`);
});

Then("I see it was never corroborated", async function (this: ShellWorld) {
  const content = (await text(this.requirePage().getByTestId("lifecycle-CLM-A"))).toLowerCase();
  assert.match(content, /never corroborated/);
  assert.ok(!content.includes("operations corroborated"));
  assert.match(content, /disputed/);
});

Then("I see it was corroborated and supported before being disputed", async function (this: ShellWorld) {
  const content = await text(this.requirePage().getByTestId("lifecycle-CLM-B"));
  assert.ok(content.indexOf("corroborated") < content.indexOf("supported"));
  assert.ok(content.indexOf("supported") < content.lastIndexOf("disputed"));
});

Then("the two lifecycles are visibly different despite the identical current badge", async function (this: ShellWorld) {
  const page = this.requirePage();
  assert.notEqual(await text(page.getByTestId("lifecycle-CLM-B")), "");
  assert.match(await text(page.locator(".shell__inspector")), /disputed/);
});

Then("the current badge equals the most recent lifecycle state", async function (this: ShellWorld) {
  const inspector = await text(this.requirePage().locator(".shell__inspector"));
  assert.match(inspector, /Statusdisputed/);
  assert.match(inspector, /sales disputed CLM-B/);
});

Then("each state names who moved it there and on what date", async function (this: ShellWorld) {
  const content = await text(this.requirePage().getByTestId("lifecycle-CLM-B"));
  assert.match(content, /operations/);
  assert.match(content, /sales/);
  assert.match(content, /2026-02-10/);
  assert.match(content, /2026-03-14/);
});

Given("I open that claim in the dynamic dashboard", async function (this: ShellWorld) {
  await openClaim(this);
});

Then("the claim does not display {string} or {string}", async function (this: ShellWorld, a: string, b: string) {
  const conclusion = (await text(this.requirePage().getByTestId("status-conclusion"))).toLowerCase();
  assert.ok(!conclusion.includes(a) && !conclusion.includes(b));
});

Then("the evidence is labelled as mechanism-on-fixture, a ceiling", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().locator(".shell__inspector")), /mechanism on synthetic fixture; no scientific conclusion licensed/);
});

Then("capability {string} is displayed separately from the conclusion", async function (this: ShellWorld, capability: string) {
  const page = this.requirePage();
  assert.equal((await text(page.getByTestId("status-capability"))).trim(), capability);
  assert.notEqual(page.getByTestId("status-capability"), page.getByTestId("status-conclusion"));
});

Then("the conclusion is shown as its own value, not inferred from the capability", async function (this: ShellWorld) {
  const page = this.requirePage();
  assert.equal((await text(page.getByTestId("status-conclusion"))).trim(), "not tested");
});

Then("the causal link is shown as contradicted", async function (this: ShellWorld) {
  assert.equal((await text(this.requirePage().getByTestId("status-logical"))).trim(), "contradicted");
});

Then("it is not shown as {string} or merely {string}", async function (this: ShellWorld, a: string, b: string) {
  const logical = (await text(this.requirePage().getByTestId("status-logical"))).toLowerCase();
  assert.ok(!logical.includes(a) && !logical.includes(b));
});

Then("the downstream effect is shown by its own observed status", async function (this: ShellWorld) {
  const page = await openSurface(this, "Predictions");
  await visible(page.getByTestId("prediction-interpretation").first(), "outcome interpretation missing");
});

Then("completion of the intervention does not colour the effect as achieved", async function (this: ShellWorld) {
  const page = this.requirePage();
  assert.match(await text(page.getByTestId("status-implementation").first()), /complete/);
  assert.doesNotMatch((await text(page.getByTestId("prediction-observed").first())).toLowerCase(), /achieved/);
});

Given("a qualified, preregistered study result recorded as {string} for this claim", async function (this: ShellWorld, _result: string) {
  await this.close();
  this.fixtureName = "history-supported";
  await openClaim(this);
});

Then("the claim may display {string}", async function (this: ShellWorld, result: string) {
  assert.equal((await text(this.requirePage().getByTestId("status-conclusion"))).trim(), result);
});

Then("the display cites the study that licenses it", async function (this: ShellWorld) {
  assert.match(await text(this.requirePage().locator(".shell__inspector")), /Qualified preregistered field study/);
});
