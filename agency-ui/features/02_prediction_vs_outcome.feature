# Realizes HYP-DYN-PREDICTION via CAP-PREDICTION-EVALUATION (docs/dynamic-ltp/portfolio.toml).
# Evidence ceiling: @evidence_capability -- passing proves the UI distinguishes
# predicted from observed from validated; it never asserts a hypothesis is supported.
# The deep guard against a green signal reading as a conclusion is 06_epistemic_ceiling_guard.

@phase:dynamic @must @prediction @ltp @hypothesize
@hyp_dyn_prediction @cap_prediction_evaluation @evidence_capability
Feature: Show a causal effect as a testable prediction, not a desired box
  As an analyst tracking whether an intervention worked
  I want predicted effect, observed effect, and interpretation shown separately
  So that "action completed" is never read as "effect occurred" or "hypothesis validated"

  Background:
    Given a causal claim with a predicted effect that has a baseline, an expected magnitude, an expected lag, and a review date
    And an injection linked to that claim
    And I open the causal claim in the dynamic dashboard

  Scenario: Predicted and observed are shown side by side with an interpretation
    Given the observation recorded so far is below the expected magnitude
    When I view the predicted effect
    Then I see the predicted magnitude and the observed magnitude as distinct values
    And I see an interpretation of "inconclusive" or "contradicted", not a single green check

  Scenario: A completed intervention with an absent effect is not shown as done
    Given the injection is marked implementation-complete
    And the expected effect has not appeared past its expected lag
    Then the effect renders as "effect absent", not as achieved or done
    And the implementation progress and the effect status are two separate indicators

  Scenario: A prediction past its review date is flagged overdue
    Given the prediction's review date is before the current as-of date
    And no observation has been recorded
    Then the prediction is flagged as overdue for evaluation
    And it appears in the attention-required queue

  Scenario: Implementation-complete does not display as hypothesis-supported
    Given the linked capability status is "implemented"
    And the hypothesis conclusion is "not_tested"
    Then the claim shows capability "implemented" and conclusion "not tested" separately
    And no "validated" or "supported" affordance is displayed
