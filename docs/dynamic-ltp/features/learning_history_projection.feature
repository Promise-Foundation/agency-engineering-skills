# Engine contract for CAP-LEARNING-HISTORY (HYP-DYN-HISTORY).
# @evidence_capability -- the projection behaves; it makes no empirical claim.
# The refined architecture: UNIFY existing records into a read-model, do NOT build
# a parallel generic event store.
#
# Record sources (from Agent seam map + hypothesize extraction):
#   git revisions of ltp/ltp-model.yaml (structural change + author + date)
#   promisify .norms/assessments/ (already append-only; repairs as superseding records)
#   research/generated/research-status.json snapshots (regenerated, source_hash'd)
#   prediction evaluations (CAP-PREDICTION-EVALUATION output)
# The projection is deterministic and hashable like every other generated artifact.

@ltp @history @should
@hyp_dyn_history @cap_learning_history @evidence_capability
Feature: Project one navigable learning history from records that already exist
  As the engine answering "how did this model come to be?"
  I want a single ordered history unified from existing sources, not a new event log
  So that timeline, diff, and attention views need no parallel write path

  Scenario: Unify existing sources into one ordered history
    Given git revisions of the ltp model, promisify assessments, research-status snapshots, and prediction evaluations for a project
    When the learning-history projection is built
    Then the entries are ordered by occurred-at
    And each entry references the underlying record it derives from
    And no source record is copied into a new authoritative log

  Scenario: Reconstruct the model state as of a date
    Given a learning history spanning several dates
    When the projection is asked for the state as of a past date
    Then it returns the claims, relationships, and statuses that existed then

  Scenario: Produce a semantic diff between two dates
    When the projection diffs two dates
    Then it emits changes as model events, for example "relationship revised: cause insufficiency"
    And it does not emit raw text diffs

  Scenario: The projection is deterministic and hashable
    Given identical source records
    When the projection is built twice
    Then both builds are byte-identical
    And the build carries a source_hash like other generated artifacts
