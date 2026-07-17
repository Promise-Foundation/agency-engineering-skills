# Realizes HYP-DYN-HISTORY via CAP-LEARNING-HISTORY (docs/dynamic-ltp/portfolio.toml).
# Evidence ceiling: @evidence_capability -- passing proves the timeline UI works,
# NOT that any modelled prediction is supported. Executable against the real shell.
#
# Dual-idiom tags:
#   @phase:dynamic @must   -> Cucumber browser gate
#   @hyp_* @cap_* @evidence_* -> hypothesize traceability + inferential ceiling

@phase:dynamic @must @history @ltp
@hyp_dyn_history @cap_learning_history @evidence_capability
Feature: Navigate the learning history of a causal model
  As an analyst returning to a model I have not seen in weeks
  I want to move through how the model changed, not just read its current state
  So that the tree shows the reasoning that produced it, not a static snapshot

  Background:
    Given a project whose learning history unifies git model revisions, promisify assessments, research-status snapshots, and prediction evaluations
    And I open the dynamic dashboard for that project

  Scenario: View the model as it stood on a past date
    When I set the history cursor to "2026-02-15"
    Then the tree shows only claims, relationships, and statuses that existed on that date
    And a claim proposed after that date is absent
    And the header states I am viewing an as-of date, not the current model

  Scenario: See a semantic diff between two dates, not a text diff
    When I compare "2026-02-15" with "2026-03-15"
    Then I see entries phrased as model changes, for example:
      | change                                                        |
      | claim CLM-12 added                                            |
      | relationship REL-4 revised: cause insufficiency, premise added |
      | stakeholder position on REL-4 changed: sales disputes         |
      | prediction PRED-3 reached its review date                     |
    And I do not see raw YAML line diffs

  Scenario: Every history entry names what changed and why
    When I open the entry "relationship REL-4 revised"
    Then it shows the previous and revised formulation
    And it names the reservation that motivated the change
    And it links to the underlying record it was derived from

  Scenario: Play back the evolution in order
    When I play the history from the earliest entry
    Then entries appear in occurred-at order
    And the tree updates to each intermediate state as playback advances
