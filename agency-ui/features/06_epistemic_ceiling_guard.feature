# Realizes HYP-DYN-UI-CEILING via CAP-EPISTEMIC-CEILING-UI (docs/dynamic-ltp/portfolio.toml).
# The flagship guard, modelled on the reference project's 13_feedback_quality_guard:
# just as that app refuses to display perfect LTP scores with no evidence, this
# dashboard refuses to let a lower-authority green signal read as a higher-authority
# conclusion. This is the visual analog of the @evidence_* tag ceilings.
# Satisfies REQ-DYN-CEILINGS-HELD (blocking). @evidence_capability.

@phase:dynamic @must @ceiling @ltp @hypothesize
@hyp_dyn_ui_ceiling @cap_epistemic_ceiling_ui @evidence_capability
Feature: Never let a lower-authority signal display as a higher-authority conclusion
  As a reader who glances at a status badge and trusts it
  I want the display to keep capability, logic, empirical, and outcome distinct
  So that a completed action can never masquerade as a validated hypothesis

  Background:
    Given a causal claim whose dimensions are deliberately mismatched:
      | dimension          | value        |
      | capability status  | implemented  |
      | logical (CLR)      | contradicted |
      | empirical status   | falsified    |
      | predicted effect   | absent       |
    And I open that claim in the dynamic dashboard

  Scenario: A mechanism result never renders as a scientific conclusion
    Given the only supporting evidence is a passing mechanism scenario on a synthetic fixture
    Then the claim does not display "supported" or "validated"
    And the evidence is labelled as mechanism-on-fixture, a ceiling

  Scenario: A completed capability never renders as the hypothesis validated
    Then capability "implemented" is displayed separately from the conclusion
    And the conclusion is shown as its own value, not inferred from the capability

  Scenario: A contradicted link renders as contradicted, not in progress
    Then the causal link is shown as contradicted
    And it is not shown as "in progress" or merely "pending more work"

  Scenario: A completed intervention does not render its effect as achieved
    Given an intervention on this claim is marked complete
    Then the downstream effect is shown by its own observed status
    And completion of the intervention does not colour the effect as achieved

  Scenario: The one path that DOES license "supported"
    Given a qualified, preregistered study result recorded as "supported" for this claim
    Then the claim may display "supported"
    And the display cites the study that licenses it
