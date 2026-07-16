# Hypothesize

**Make uncertainty explicit.**

Hypothesize identifies the hypotheses operating within a body of work and records what the available evidence currently warrants.

The target might be:

* a scientific research program;
* a theory or manuscript;
* a strategic plan;
* a policy proposal;
* a product concept;
* a technical project;
* an attempt to address a complex social problem.

Wherever people are acting under uncertainty, they rely on assertions that may be plausible, important, and consequential without yet being established.

Hypothesize makes those assertions inspectable.

## The basic interface

Given a body of work, Hypothesize helps answer:

```text
What might be true?

Why is it worth considering?

What would follow if it were true?

What evidence bears on it?

What would count against it?

What does the evidence currently justify?

What remains unresolved?
```

Its output is a structured hypothesis portfolio: a machine-readable account of the conjectures, evidence, conclusions, and open questions that shape the work.

## A hypothesis is not a finding

A hypothesis is a possible reading of a situation.

It may explain an observation, motivate a project, organize a research program, or justify an experiment. It can be highly plausible and still be wrong.

Hypothesize therefore treats a hypothesis in the **interrogative mood**:

> Could this be so?

The hypothesis directs inquiry without asserting its own truth.

Its first value is not that it deserves belief. Its value is that it suggests consequences that can be investigated.

```text
conjecture
→ expected consequences
→ probe or observation
→ evidence
→ revised standing
```

This prevents a common collapse:

```text
The idea is coherent
therefore
the idea is true

The project implements the idea
therefore
the idea works

The test passed
therefore
the proposed explanation is correct

Some evidence exists
therefore
the conclusion is supported
```

Each transition requires its own justification.

## What Hypothesize records

A hypothesis record can include:

```yaml
id: HYP-001

statement: >
  Intervention X reduces systemic risk under conditions C.

rationale:
  - observation or anomaly the hypothesis addresses
  - reasons it is considered plausible

consequences:
  - what should be observable if the hypothesis is correct

falsifiers:
  - observations that would count against it

evidence:
  - studies
  - measurements
  - tests
  - analyses
  - documented observations

status: not_tested

limitations:
  - unresolved assumptions
  - missing evidence
  - scope restrictions
```

The precise schema may vary by domain. The distinctions should not.

## Evidentiary status

Hypothesize separates the existence of evidence from the conclusion the evidence supports.

A project may have:

* a study design but no result;
* a mechanism demonstration but no outcome evidence;
* an internal pilot but no comparison;
* a comparative result that failed preregistered criteria;
* a strong result with limited external validity;
* conflicting studies;
* no relevant evidence at all.

These states should not be compressed into “promising” or “validated.”

A minimal conclusion vocabulary is:

| Status         | Meaning                                                                          |
| -------------- | -------------------------------------------------------------------------------- |
| `not_tested`   | No admitted outcome evidence currently answers the hypothesis.                   |
| `supported`    | Qualified evidence favors the hypothesis under stated conditions.                |
| `falsified`    | Qualified evidence counts against the hypothesis under stated conditions.        |
| `inconclusive` | Relevant evidence exists but does not justify a positive or negative conclusion. |

The status applies to a particular proposition under particular conditions. It is not a permanent declaration of truth.

## Example: a civilizational strategy

Suppose a project presents a plan to help humanity respond to a global metacrisis.

The document may contain assertions such as:

```text
Improving collective sensemaking will reduce coordination failure.

A new governance institution will remain legitimate at global scale.

The proposed intervention can spread faster than the risks it addresses.

Participants will change their behavior when given better information.

The project can avoid reproducing the power structures it criticizes.
```

These assertions may be embedded in vision statements, causal diagrams, implementation plans, and moral arguments. They may not be labeled as hypotheses.

Hypothesize can make them explicit and distinguish:

* the project’s central hypotheses;
* assumptions required by those hypotheses;
* expected observable consequences;
* available supporting and contrary evidence;
* claims that remain untested;
* conclusions that exceed the current evidence;
* uncertainties on which the whole strategy depends.

The result is not a verdict on whether the project will save humanity.

It is a clearer account of what would have to be true for the plan to work and how much is currently known about those propositions.

## Example: a scientific research program

A research program may contain many related hypotheses:

```text
Mechanism M produces effect E.

The effect generalizes across population P.

Measurement Y is a valid proxy for construct X.

The observed result is not explained by alternative A.

The intervention remains effective outside laboratory conditions.
```

Hypothesize can connect each proposition to:

* registered studies;
* datasets;
* experimental conditions;
* expected outcomes;
* falsifiers;
* replications;
* limitations;
* current conclusions.

This makes it possible to see whether the program has accumulated many results around one narrow proposition while leaving its most important assumptions largely untested.

## Capabilities are not conclusions

When the target includes software, an instrument, or an operational process, Hypothesize can also record what it demonstrably does.

This remains separate from whether the surrounding hypothesis is supported.

```text
Capability:
The system can generate a structured intervention plan.

Hypothesis:
Using the plan improves real-world coordination.

Evidence:
The capability passes its acceptance tests.

Conclusion:
The effect hypothesis remains not tested.
```

Implementation evidence can establish that a capability exists.

It cannot, by itself, establish that the capability is useful, valid, effective, or causally responsible for an observed result.

## Evidence must retain its conditions

Evidence is meaningful only with its provenance and scope.

A useful record identifies, where applicable:

* what was observed;
* how it was measured;
* under which conditions;
* against which version or object;
* who produced or assessed it;
* whether the procedure was preregistered;
* whether the result was qualified to affect the conclusion;
* what limitations remain.

A favorable result from one setting should not silently become evidence for another.

A result about one revision, population, workload, environment, or interpretation remains tied to that context unless an explicit inference justifies transfer.

## Inquiry must be able to lose

A hypothesis is meaningful only when some conceivable result could weaken, revise, or displace it.

Hypothesize therefore favors conjectures with explicit consequences and defeat conditions.

```text
A useful hypothesis petitions for an investigation.

A useful investigation can produce an unwelcome answer.

A useful evidence process can register that answer.

A useful research program can change in response.
```

When every result can be interpreted as confirmation, the problem is not that the hypothesis has unusually strong support. The problem is that it has ceased to function as a hypothesis.

## What Hypothesize does not do

Hypothesize does not decide:

* what ought to be done;
* who has authority to make a decision;
* whether an action is permitted;
* whether a project should receive funding;
* whether a system should be deployed;
* how much practical reliance a result should authorize;
* whether evidence was produced honestly merely because it was registered.

It makes the epistemic structure visible so that researchers, agents, institutions, and other tools can make those decisions without confusing conjecture, implementation, evidence, and conclusion.

## Composition

Hypothesize produces structured records that can be consumed by other systems.

```text
documents, observations, tests, and studies
                    |
                    v
              Hypothesize
                    |
                    v
hypotheses, evidence, status, and open questions
                    |
       +------------+------------+
       |            |            |
       v            v            v
 research tools   agents     decision systems
```

A commitment system may record who agreed to conduct a study.

An assessment system may determine whether the registered procedure was followed.

A policy system may decide whether the resulting evidence is sufficient for action.

Hypothesize retains the narrower question:

> What empirical standing does this proposition currently have?

## Current workflow

A project maintains a portfolio of hypotheses, evidence, capabilities, studies, and limitations.

Hypothesize derives a deterministic research-status publication from those sources.

```bash
hypothesize sync
```

Recompute the current status and update configured outputs.

```bash
hypothesize check
```

Recompute the status without writing files and fail when published outputs are stale.

```bash
hypothesize doctor
```

Diagnose missing traceability, invalid evidence, conflicting records, and publication problems.

```bash
hypothesize adopt
```

Inspect an existing project and report how it can be represented without silently changing its current published conclusions.

## Design principle

Hypothesize does not turn uncertainty into certainty.

It turns implicit uncertainty into an explicit, revisable structure:

```text
possible
→ investigable
→ tested
→ supported, falsified, or unresolved
```

The tool succeeds when a reader can see not only what a body of work claims, but what kind of claim each assertion is, what evidence bears on it, and how far that evidence permits the inquiry to go.
