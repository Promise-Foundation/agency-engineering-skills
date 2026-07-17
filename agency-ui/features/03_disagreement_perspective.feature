# Realizes HYP-DYN-HISTORY / the disagreement recommendation via CAP-DYNAMIC-DASHBOARD.
# Disagreement is owned by promisify (assessor != observer, preserved conflicting
# assessments). This feature asserts the dashboard SURFACES that observer-relative
# view for an LTP claim; it does not re-implement trust. @evidence_capability.
#
# Depends on closing the promisify-relations gap: promisify emits no relations today,
# so the view correlates assessments to the claim by subject + domain (see ROADMAP
# "Workstream C, promisify seam").

@phase:dynamic @should @perspective @promisify @ltp
@hyp_dyn_history @cap_dynamic_dashboard @evidence_capability
Feature: Represent disagreement about a causal claim instead of a false consensus
  As a reviewer who knows stakeholders read the same claim differently
  I want observer-relative positions preserved, not collapsed to one verdict
  So that minority hypotheses survive and the displayed status is honest about who holds it

  Background:
    Given a causal relationship that promisify assessments disagree about:
      | assessor    | position            | reservation             |
      | operations  | agrees              |                         |
      | sales       | disputes            | additional cause: season |
      | finance     | accepts provisionally |                       |
    And I open that relationship in the dynamic dashboard

  Scenario: Switching the observer view changes the displayed consensus
    When I select the "human-only" observer view
    Then the displayed status reflects only the accepted assessors and that view's conflict policy
    When I select the "all-assessors" observer view
    Then the displayed status for the same relationship changes accordingly
    And the view names which conflict policy produced the status

  Scenario: Disagreement is shown, not merged away
    Then I see the relationship marked as disputed
    And I see the per-assessor positions, not a single averaged verdict
    And selecting it reveals each assessor's reservation and evidence

  Scenario: A minority hypothesis is retained after a working consensus is chosen
    Given a working consensus has selected one explanation
    Then the competing minority explanation remains visible and marked retained
    And it can be revived without being recreated from scratch
