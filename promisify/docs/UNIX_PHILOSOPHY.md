## A Small, Composable Normative Tool

Promisify follows the Unix philosophy: do one thing well, then compose with other tools to solve larger problems.

Its job is not to plan tasks, execute code, enforce permissions, determine institutional authority, maintain general agent memory, or decide what an application should do next.

Its job is narrower:

> **Represent promises and attributable assessments of those promises in a stable, machine-readable form.**

A promise records what ought to be true. An assessment records what a particular assessor observed about that promise, using particular evidence, at a particular time or revision. Promisify preserves the distinction between the two.

Other tools can then consume this information for their own purposes:

```text
promises + assessments | learner model       → learning progress
promises + assessments | coding harness      → planning constraints
promises + assessments | review system       → findings and warnings
promises + assessments | governance policy   → approval decision
promises + assessments | reporting tool      → trust or compliance view
```

The downstream meaning is deliberately left to the consumer.

A learner-development system may interpret an assisted assessment as evidence that a capability lies within the learner’s zone of proximal development. A deployment system may interpret a broken security promise as a release blocker. A coding agent may use an applicable promise as an acceptance criterion. These systems need not be built into Promisify, and they need not agree on how the same assessments should affect their decisions.

This separation gives the tool a clear boundary.

### Promisify should own

* the representation of promises;
* stable identities for promises;
* the domains in which promises apply;
* the representation of assessments;
* assessor, evidence, time, and revision provenance;
* uncertainty and conflicting assessments;
* deterministic projections under an explicit observer policy;
* validation and interchange of these records.

### Promisify should not own

* general task planning;
* code execution;
* authorization and permissions;
* institutional policy enforcement;
* factual verification of arbitrary documentation;
* general episodic or semantic memory;
* educational intervention selection;
* deployment decisions;
* application-specific interpretations of trust.

Those capabilities belong in separate tools that compose with it.

The value of this design is not that the tool makes every agent decision. Its value is that it gives otherwise independent components a shared normative language.

A planner can identify the promises relevant to a task. An executor can attempt to satisfy them. Tests, agents, and humans can assess them. A domain-specific consumer can interpret the resulting assessments. Each component remains independently understandable, replaceable, and testable.

Like a Unix utility, the tool becomes powerful through composition:

```text
declare expectations
    | resolve applicability
    | collect assessments
    | apply a consumer-specific interpretation
```

The core design standard is therefore not feature completeness. It is protocol quality:

* Is the distinction between a promise and an assessment unambiguous?
* Are records stable and machine-readable?
* Is provenance preserved?
* Can disagreement and uncertainty be represented without information loss?
* Can unrelated tools consume the output without depending on internal implementation details?
* Can domain-specific behavior be added without expanding the core tool’s responsibility?

Promisify succeeds when it performs this one job predictably enough that other systems can build richer workflows around it.
