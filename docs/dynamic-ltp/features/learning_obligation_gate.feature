# Engine contract for CAP-LEARNING-OBLIGATION-GATE (HYP-DYN-CURRENCY).
# @evidence_scientific_contract -- this scenario tests the STATUS/GATE machinery
# (does publication correctly refuse an operationally-obsolete model), not any
# hypothesis outcome. It affects only capability status and asserts nothing about
# whether any modelled effect is real.
#
# Seams: a new ERROR-severity code in diagnostics.py CATALOG (:32-109), emitted by
# a validator registered in validators/__init__.py:28-39, flows through
# report.errors (:47-48) and blocks cmd_sync (cli.py:139-146) and cmd_check
# (cli.py:165). `--as-of` supplies the EXPLICIT date used by the caller/CI,
# keeping validate() a pure function.

@ltp @governance @must
@hyp_dyn_currency @cap_learning_obligation_gate @evidence_scientific_contract
Feature: Fail publication when the model carries an overdue learning obligation
  As CI defending a model's currency with reality, not just its internal consistency
  I want an overdue, unresolved obligation to block publication
  So that "publishable" means "no outstanding debt with reality", not "the files match"

  Scenario: An overdue prediction blocks an otherwise valid model
    Given a model with zero structural or logical errors
    And a prediction whose review date is before the evaluation as-of date, with no observation
    When `ltp check` runs as of that date
    Then it exits non-zero
    And it reports a distinct coded diagnostic for the overdue learning obligation

  Scenario: The same model with no overdue obligations publishes
    Given the same model evaluated as of a date before that review date
    When `ltp check` runs
    Then it exits zero
    And it reports no learning-obligation diagnostic

  Scenario: Obligations are relative to an explicit date, not wall-clock
    Given a model with a prediction due on a fixed date
    When the obligation check runs twice with the same explicit as-of date
    Then both runs produce identical diagnostics
    And the check never reads the system clock

  Scenario: Waiving an obligation clears the gate without touching logical status
    Given an overdue obligation that is explicitly waived with a reason
    When `ltp check` runs
    Then the learning-obligation diagnostic is cleared
    And the underlying claim's CLR-derived logical status is unchanged
