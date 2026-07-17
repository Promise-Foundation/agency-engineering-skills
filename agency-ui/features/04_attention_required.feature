# Realizes HYP-DYN-CURRENCY via CAP-DYNAMIC-DASHBOARD (docs/dynamic-ltp/portfolio.toml).
# This is the UI face of the enforcement reframe: "attention" is the set of
# unresolved learning obligations the engine derives -- the same set whose overdue
# members make `ltp check` red (CAP-LEARNING-OBLIGATION-GATE). @evidence_capability.

@phase:dynamic @must @attention @ltp
@hyp_dyn_currency @cap_dynamic_dashboard @evidence_capability
Feature: Show what needs attention next, computed from learning obligations
  As an analyst who should not have to inspect the whole tree
  I want the model's unresolved, time-sensitive obligations surfaced and ranked
  So that "you are here / what to do next" is derived, not manually curated

  Background:
    Given a model evaluated as of "2026-03-15" that carries several learning obligations
    And I open the attention-required view in the dynamic dashboard

  Scenario: Obligations are listed by kind with a concrete next action
    Then I see obligations grouped by kind:
      | kind                                  |
      | prediction overdue for evaluation     |
      | observation stale past its expected lag |
      | revision not yet reviewed             |
      | intervention completed but not verified |
      | high-impact causal link with weak evidence |
    And each item links to the exact claim or record it concerns
    And each item states the smallest next action that would resolve it

  Scenario: Resolving an obligation clears it without touching logical status
    When I mark the overdue prediction as evaluated with a recorded observation
    Then that item leaves the queue
    And the causal claim's CLR-derived logical status is unchanged

  Scenario: An empty queue asserts currency, not merely consistency
    Given a model with no unresolved overdue obligations as of the same date
    Then the view states the model has no overdue learning obligations
    And it distinguishes that from "the model is internally consistent"
