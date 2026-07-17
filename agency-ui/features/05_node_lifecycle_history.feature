# Realizes the node-lifecycle recommendation via CAP-LEARNING-HISTORY.
# A lifecycle is a sequence of events, not one mutable status field: two nodes that
# both read "disputed" now can have entirely different histories, and that difference
# is the value. @evidence_capability.

@phase:dynamic @should @lifecycle @ltp
@hyp_dyn_history @cap_learning_history @evidence_capability
Feature: Show a node's lifecycle as a sequence, not a single current badge
  As a reviewer deciding how much to trust a claim
  I want to see how it reached its current status
  So that a scalar "disputed" does not erase the reasoning behind it

  Background:
    Given two claims that both currently read "disputed":
      | claim  | history                                                             |
      | CLM-A  | proposed, then disputed on first review, never corroborated          |
      | CLM-B  | proposed, corroborated, supported for months, disputed yesterday     |
    And I open each claim in the dynamic dashboard

  Scenario: The two nodes expose visibly different lifecycles
    When I open the lifecycle of CLM-A
    Then I see it was never corroborated
    When I open the lifecycle of CLM-B
    Then I see it was corroborated and supported before being disputed
    And the two lifecycles are visibly different despite the identical current badge

  Scenario: The current badge is derived from the lifecycle, not authored
    When I open the lifecycle of CLM-B
    Then the current badge equals the most recent lifecycle state
    And each state names who moved it there and on what date
