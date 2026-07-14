# Example behave feature showing correct tagging.
#
# Tag order (top to bottom): domain labels, requirement strength, hypothesis
# link, capability link, evidence role, controls. Every @hyp_* / @cap_* tag must
# be registered in the portfolio or publication fails. There is NEVER a
# @hypothesis_supported / @validated tag — scientific status is computed.
#
# What these tags mean here:
#   @application @scoring   domain labels (no derivation authority)
#   @must                   binding requirement
#   @hyp_ex_1               associates with HYP-EX-1 (rollup only, never a conclusion)
#   @cap_example            this scenario's outcome sets CAP-EXAMPLE's status
#   @evidence_mechanism     passing may raise HYP-EX-1 maturity to `mechanism`;
#                           it does NOT touch HYP-EX-1's conclusion
#   @synthetic_fixture      the data is synthetic — a maturity ceiling, not evidence

@application @scoring @must @hyp_ex_1 @cap_example @evidence_mechanism @synthetic_fixture
Feature: Score a response deterministically on the synthetic corpus
  As a benchmark developer
  I want the scorer to produce the same result for the same input
  So that the scoring mechanism is a sound, inspectable foundation

  Scenario: Identical inputs produce identical scores
    Given a synthetic packet and a fixed response
    When the development scorer evaluates the response twice
    Then both evaluations return byte-identical scores

  Scenario: A well-anchored finding earns dependency-independence credit
    Given a synthetic packet with a supported finding
    When the development scorer evaluates the response
    Then the finding receives dependency-independence credit

  # A capability may still be "specified" rather than "implemented": mark
  # not-yet-built scenarios @wip so they are skipped and register as specified —
  # a promise on the record, never a passing claim.
  @wip
  Scenario: Score multi-part responses with partial support
    Given a synthetic packet with a partially supported response
    When the development scorer evaluates the response
    Then each part is credited independently
