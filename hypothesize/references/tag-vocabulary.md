# Tag vocabulary

The controlled vocabulary for acceptance features/tests. `hypothesize` reads these tags from the acceptance report to derive capability status and evidence maturity, and to enforce traceability. Tags are the interface between the tests and the registry — use them exactly as defined here. Under behave they are Gherkin `@tags`; under pytest they are the adapter's equivalent markers.

## Contents
- [Domain / architecture tags](#domain--architecture-tags)
- [Requirement strength](#requirement-strength)
- [Traceability links](#traceability-links)
- [Evidence-role tags](#evidence-role-tags)
- [Control tags](#control-tags)
- [Forbidden tags](#forbidden-tags)
- [Worked example](#worked-example)

## Domain / architecture tags

Freeform labels that name the area a scenario lives in — e.g. `@application`, `@scoring`, `@governance`, `@adjudication`. They organize and filter the suite and carry no derivation authority. Use whatever vocabulary fits the project; keep it consistent.

## Requirement strength

Normative weight, mirroring RFC 2119.

| Tag | Meaning |
| --- | --- |
| `@must` | A binding requirement; failure is a blocking defect. |
| `@should` | A strong recommendation; deviations need justification. |
| `@may` | Optional / permitted behavior. |

Strength informs how a failure is reported and how requirement gates in the registry are evaluated. It does not by itself change a capability status.

## Traceability links

These bind a scenario to a registered object. **Every link tag used in the suite must resolve to a registered entry in the portfolio, or publication fails.**

| Tag | Maps to | Registry family |
| --- | --- | --- |
| `@hyp_<id>` (e.g. `@hyp_ub_1`) | `HYP-*` | `hypotheses` (via each entry's `tag`) |
| `@cap_*` (e.g. `@cap_clean_control_scoring`) | `CAP-*` | `capabilities` (via each entry's `tag`) |

A scenario may carry both a `@hyp_*` and a `@cap_*` tag: it proves a capability *and* is associated with the hypothesis that capability informs. The capability's scenarios decide its capability status; the hypothesis association feeds the hypothesis's `capability_status` rollup — never its conclusion.

## Evidence-role tags

The most consequential tags: they declare **what kind of claim a passing scenario licenses**. This is where the capability/evidence/conclusion separation is enforced at the test level. Exactly one evidence role is intended per feature.

### `@evidence_capability`
The scenario proves a **behavior exists** on the implementation. It confirms capability status and nothing more — **no maturity bump, no conclusion**. Use this for the ordinary "the software does X" scenarios, including the scenario that proves the project can *publish its own research status*.

> Licenses: "this behavior works." Does not license any empirical claim.

### `@evidence_mechanism`
The scenario proves a **bounded mechanism** behaves as designed on fixtures — e.g. a scoring function or a verification step runs deterministically on a synthetic corpus. This may raise the linked hypothesis's evidence maturity to `mechanism` (the highest rung reachable without a study result). It is **not** a comparative result and does **not** test the hypothesis's outcome.

> Licenses: "the mechanism relevant to H works." Does not license "H is supported."

### `@evidence_scientific_contract`
The scenario tests a **scientific workflow**, not an outcome — for example, that a qualified+preregistered result *would* control the conclusion, that an unqualified artifact *would* be quarantined, or that an unregistered hypothesis reference *would* fail validation. It exercises the *rules of evidence*, so it affects only capability status (the workflow exists). It **never** moves maturity or a conclusion, and passing it says nothing about any real hypothesis's truth.

> Licenses: "the evidence machinery behaves correctly." Never asserts a scientific result.

The distinction that matters: `@evidence_mechanism` says a domain mechanism works; `@evidence_scientific_contract` says the *status-derivation* mechanism works. Neither can make a hypothesis `supported` — only an admitted qualified, preregistered study result does that.

## Control tags

Mark the epistemic role of a fixture or scenario.

| Tag | Meaning |
| --- | --- |
| `@clean_control` | A case that should **not** trigger a defect finding; guards against over-suspicion / false positives. |
| `@negative_control` | A case that should produce a null/negative result; guards against spurious signal. |
| `@adversarial` | A deliberately hostile input probing robustness. |
| `@synthetic_fixture` | The data is synthetic, not real-world — a maturity ceiling, not real evidence. |
| `@independence_required` | The scenario's validity depends on independent (e.g. third-party, non-author) artifacts. |
| `@wip` | Specified-but-unbuilt. The scenario is skipped and registers the capability as **specified** — a promise on the record, not a passing claim. |

## Forbidden tags

There is **never** a `@hypothesis_supported`, `@validated`, `@supported`, or equivalent tag. Scientific status is **computed** from qualified, preregistered study results — it is never *asserted* in feature text. A tag that claims a scientific outcome would let a test promote a hypothesis, which is precisely the category error the model forbids. If you find such a tag in a suite, treat it as a defect to repair, not a signal to honor.

## Worked example

```gherkin
@application @scoring @must
@hyp_ub_2
@cap_clean_control_scoring
@evidence_mechanism
@clean_control @synthetic_fixture
Feature: Preserve clean-case specificity in development scoring
  As a benchmark developer
  I want unsupported suspicion penalized on clean controls
  So that the scoring mechanism does not reward indiscriminate skepticism

  Scenario: Penalize an unanchored fatal allegation on a clean control
    Given a synthetic clean-control packet
    And a response that alleges unsupported fatal circularity
    When the provisional development scorer evaluates the response
    Then unsupported suspicion reduces dependency independence
```

How the engine reads this feature:

- `@application`, `@scoring` — domain labels (no authority).
- `@must` — a binding requirement.
- `@cap_clean_control_scoring` — must resolve to a `CAP-*`; its scenarios' outcomes set that capability's status.
- `@hyp_ub_2` — must resolve to `HYP-2`; associates the capability with that hypothesis.
- `@evidence_mechanism` — a passing scenario may raise `HYP-2` maturity to `mechanism`; it does **not** touch `HYP-2`'s conclusion.
- `@clean_control`, `@synthetic_fixture` — this is a synthetic false-positive guard, so it is a mechanism ceiling, not empirical validation.

Net effect if the scenario passes: the capability is `implemented`, `HYP-2` maturity may reach `mechanism`, and `HYP-2`'s conclusion stays `not_tested`. Exactly as intended.
