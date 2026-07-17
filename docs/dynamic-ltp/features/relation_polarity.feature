# Engine contract for CAP-RELATION-POLARITY (HYP-DYN-POLARITY).
# Executable contract mirrored by ltp/tests/test_dynamic.py and test_migrate.py.
# @evidence_capability -- the software does X, including
# rejecting a mis-encoding; it makes no empirical claim.
#
# Seams (see docs/dynamic-ltp/ROADMAP.md, from the LTP seam map):
#   mirror ObstacleResolution (models.py:264-268 and its ~13 touch-points)
#   replace FRT-006's causal-reachability check (reality.py:167-184)
#   render "neutralizes"/"trimmed by" instead of hard-coded "causes"
#   (mermaid.py:98,105; dashboard.py:53,56; markdown.py:142-158)
#   migrate CLM-6 like the overcome_by->obstacle_resolutions map (migrate.py:204-208)

@ltp @ontology @must
@hyp_dyn_polarity @cap_relation_polarity @evidence_capability
Feature: Type causal polarity so prevention is not encoded as causation
  As an analyst modelling a trimming injection that neutralises a negative branch
  I want the relationship typed by its real polarity
  So that the model does not have to say "causes" and apologise in a comment

  Scenario: A trimming injection neutralises a negative branch as a first-class relation
    Given a trimming injection TRIM-1 and a negative branch NBR-1
    When TRIM-1 is recorded as neutralising NBR-1
    Then the relationship carries polarity "neutralizes"
    And no free-text comment is needed to deny forward causation
    And the model validates without a sufficiency claim from TRIM-1 to NBR-1

  Scenario: Renderers label the relationship by its polarity, not "causes"
    Given TRIM-1 neutralises NBR-1
    When the future-reality view is rendered
    Then the edge is labelled "neutralizes" or "trimmed by"
    And it is not labelled "causes"

  Scenario: Encoding a prevention as a sufficiency claim is rejected
    Given a relationship whose real polarity is prevention
    When it is authored as a plain sufficiency causal_claim
    Then `ltp validate` reports a coded error naming the polarity mismatch
    And the error names the correct typed relation to use instead

  Scenario: Migration rewrites the existing apology into a typed relation
    Given the self-model's CLM-6 sufficiency claim from TRIM-1 to NBR-1
    When `ltp migrate` runs
    Then CLM-6 becomes a typed neutralises relationship
    And the record ids are preserved
    And the apology comment is no longer required
