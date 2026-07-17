# Engine contract for CAP-PREDICTION-EVALUATION (HYP-DYN-PREDICTION).
# @evidence_mechanism @synthetic_fixture -- a bounded, deterministic evaluator on
# a synthetic prediction/observation. Passing MAY raise HYP-DYN-PREDICTION maturity
# to `mechanism`; it NEVER sets the causal claim's conclusion. This is the
# generalisation of hypothesize's capability-evaluation loop to causal outcomes.
#
# Seams: add temporal fields to PredictedEffect (models.py:249-258, round-trip as
# strings via store.py:27-48); a PredictionEvaluation record (mirror the
# PredictedEffect wiring); PRED-OVERDUE/OBS-STALE codes in diagnostics.py CATALOG
# (:32-109), emitted by a validator registered in validators/__init__.py:28-39.
# The evaluator takes an EXPLICIT as-of date -- never wall-clock -- to stay
# deterministic under source_hash/golden tests.

@ltp @prediction @must
@hyp_dyn_prediction @cap_prediction_evaluation @evidence_mechanism @synthetic_fixture
Feature: Evaluate a predicted effect against an observation deterministically
  As the engine reconciling a Future Reality Tree with what happened
  I want predicted vs observed classified as a pure function of an explicit clock
  So that "did reality behave as predicted" is a tracked state, not authored prose

  Scenario: Classify an under-target observation as inconclusive or contradicted
    Given a predicted effect with baseline 20, expected magnitude -40 percent, and expected lag 6 weeks
    And an observation of -10 percent recorded after 6 weeks
    When the evaluator runs as of the observation date
    Then the evaluation result is "contradicted" or "inconclusive"
    And it is not "supported"

  Scenario: Distinguish "not yet due" from "contradicted"
    Given a predicted effect whose expected lag has not elapsed as of the evaluation date
    And no observation yet
    When the evaluator runs
    Then the result is "not_yet_due"
    And it is not "contradicted"

  Scenario: Identical inputs produce byte-identical evaluations
    Given a fixed prediction, a fixed observation, and a fixed as-of date
    When the evaluator runs twice
    Then both runs produce byte-identical evaluation records

  Scenario: Recording an observation never changes logical status
    Given a causal claim with a CLR-derived logical status
    When an observation is recorded and the prediction is evaluated
    Then the claim's clr.*.result values are unchanged
    And only the empirical/prediction fields move

  Scenario: A passing mechanism scenario never sets the conclusion
    Given this feature passes on the synthetic fixture
    Then HYP-DYN-PREDICTION evidence maturity may reach "mechanism"
    And HYP-DYN-PREDICTION conclusion stays "not_tested"
