The MVP should be a **thin vertical slice** that proves one claim:

> Given a real task and a demonstrated blocker, the skill can teach the smallest useful capability, return the learner to the task, and update an evidence-based estimate of what they can now do.

It should not try to become a complete learning management system.

## Agency Engineering dependency and ontology

ZPD has a hard dependency on Promisify. Unlike LTP and Hypothesize, it must not run
without a validated promise domain model because its learner estimates assess capacity
promises effective in that domain.

A ZPD capacity promise states what a learner or role can be expected to do under stated
conditions. This is not necessarily a hypothesis and does not require an LTP model. The
domain describes the capability **type** and inherits promises hierarchically; the learner,
attempt, or work product is the assessed **token**. ZPD assessments may be graded,
uncertain, and subjective. They must retain assessor, evidence, conditions, and revision
rather than collapsing into a kept/broken fact on the promise.

The current document specifies an MVP; the live UI demo is not a shipped ZPD skill or a
complete learning-assessment implementation.

# MVP user flow

```text
User invokes /teach with a real job
        ↓
Skill establishes definition of done
        ↓
Skill inspects or requests a small attempt
        ↓
Skill diagnoses one blocker
        ↓
Skill maps blocker to one domain promise
        ↓
Skill decides: teach, assess, or proceed
        ↓
User completes a short lesson or diagnostic
        ↓
User applies learning to the original job
        ↓
Skill evaluates the result
        ↓
Skill records evidence and suggests one next action
```

# 1. One active job

The MVP needs a single `NOW.md`.

```md
# Current Job

## Outcome

Represent one uncertain chatbot claim as a Graphist structure.

## Definition of Done

The representation contains:
- one claim;
- one source;
- one scope;
- one conflict;
- one status transition.

## Current Attempt

Claim and source nodes exist.

## Current Blocker

I cannot determine whether two references denote the same entity.

## Time Available

30 minutes.

## Next Action

Diagnose the identity relation.
```

The skill should enforce:

```text
one active job
one current blocker
one immediate learning intervention
```

No project portfolio is needed in the MVP.

# 2. A minimal domain registry

The MVP needs a small domain model, probably YAML.

```text
domains/
├── graphist.yaml
├── existential-graphs.yaml
├── rag.yaml
└── python.yaml
```

Each domain only needs:

* nested capability names;
* level promises;
* prerequisite hints;
* critical assessment criteria;
* one or two task templates;
* trusted resources.

Example:

```yaml
name: Existential Graphs

subdomains:
  alpha-cuts:
    levels:
      1:
        promise:
          - recognize cuts
          - identify positive and negative regions

      2:
        promise:
          - translate simple negations into Alpha graphs
          - apply basic erasure and insertion rules
          - explain why a transformation is legal

        critical:
          - correctly determine polarity

        assessments:
          - type: translation
          - type: error-diagnosis

  beta-identity:
    prerequisites:
      - alpha-cuts: 2

    levels:
      1:
        promise:
          - recognize a line of identity
          - explain what it connects

      2:
        promise:
          - represent identity across predicates
          - distinguish false merges from false splits
```

The registry does not need to cover every conceivable topic. It needs only enough domains to test the workflow.

# 3. Assessable promises

Every level must make a small, observable promise.

Bad:

> Understand Beta graphs.

Good:

> Given a novel relational statement, the learner can represent its identity structure and identify one false merge without notes and with at most one hint.

A promise record needs:

```yaml
promise:
  can:
    - represent identity across two predicates
    - detect a false identity merge
    - explain the role of scope

conditions:
  notes: false
  hints_allowed: 1
  novelty: near-transfer

critical:
  - no false identity merge
```

The MVP should avoid elaborate competency frameworks. Three types of evidence are enough:

* recognition;
* independent application;
* transfer to the current job.

# 4. A simple ZPD estimate

The MVP does not need a psychometrically sophisticated learner model.

For each subdomain, track:

```yaml
independent_level: 1
assisted_level: 2
confidence: medium
```

And store the evidence supporting it.

The teaching decision can be simple:

```text
Required level ≤ independent level
    → proceed directly

Required level = assisted level
    → teach or scaffold

Required level > assisted level
    → reduce task or teach a smaller prerequisite
```

A useful six-state performance scale would be:

```text
0 — not encountered
1 — recognized with explanation
2 — reproduced from example
3 — applied independently in familiar case
4 — transferred to a new case
5 — critiqued or designed with it
```

The MVP does not need to expose a numerical score unless it adds real value.

# 5. Attempt-first diagnosis

Before teaching, the skill needs one small diagnostic attempt.

Examples:

* “Draw the identity relation as you currently understand it.”
* “Explain why these two records might refer to the same person.”
* “Modify this function to preserve provenance.”
* “Choose which source supports the claim.”
* “Translate this sentence into an Alpha graph.”

The agent then classifies the blocker using a short taxonomy:

```text
missing vocabulary
missing fact
missing procedure
missing prerequisite
incorrect mental model
weak discrimination
working-memory overload
unclear goal
non-learning technical blocker
```

The MVP should record the diagnosis as provisional:

```md
Current diagnosis:

You understand identity conceptually, but you are treating
same spelling as sufficient evidence of same entity.
```

# 6. Three possible decisions

The skill must be able to choose among:

## Proceed

The learner already has enough demonstrated capability.

> Your records and current attempt show that you can do this. Apply it directly to the project.

## Assess

The learner may know it, but the evidence is old or weak.

> Complete this two-minute transfer task before we decide whether instruction is needed.

## Teach

A specific missing capability is blocking progress.

> Learn one method for distinguishing identity evidence from name similarity.

This decision is one of the MVP’s most important features. Otherwise `/teach` becomes a lesson generator rather than an adaptive teaching agent.

# 7. One short lesson format

The lesson can be a generated HTML file, but it should be minimal.

```text
lessons/
└── 0001-identity-is-not-name-similarity.html
```

Every lesson needs:

1. **Current job**
2. **Current blocker**
3. **One concept**
4. **One worked example**
5. **One learner attempt**
6. **Immediate feedback**
7. **Return to the real task**
8. **One primary resource**

A lesson might be:

```text
Job:
Resolve two conflicting user records.

Concept:
Same label does not establish same identity.

Worked example:
Two “Alex Kim” records with different account IDs.

Practice:
Decide whether three pairs should be merged, split,
or left unresolved.

Return:
Apply the checklist to the actual Graphist nodes.
```

The lesson should be completable in roughly 10–25 minutes.

# 8. Immediate application to the real job

This must be mandatory.

The user should not finish after passing a quiz. They must perform the blocked action:

```text
lesson:
distinguish false merge from unresolved identity

application:
repair the actual Graphist diagram
```

For coding work, the skill should inspect the relevant project and run available checks:

* tests;
* type checking;
* linting;
* graph invariants;
* rendered output.

The MVP should separately report:

```text
Task progress: successful
Learning evidence: moderate
```

A working result does not prove the learner produced it independently.

# 9. An append-only assessment record

The MVP needs an `assessments/` directory.

```yaml
id: 0003
date: 2026-07-15

domain: existential-graphs.beta-identity
level: 2

job:
  outcome: model a mistaken identity case

assessment:
  type: project-application
  novelty: near-transfer
  notes_used: true
  hints: 1

result:
  accuracy: pass
  critical_errors: []
  explanation: adequate

evidence:
  - represented two candidate identities
  - did not merge on name similarity alone
  - marked unresolved identity explicitly

updated_estimate:
  independent_level: 1
  assisted_level: 2
  confidence: medium
```

Append-only matters because the system should be able to explain why its current estimate changed.

# 10. A minimal learning record

After meaningful progress, create one short learning record.

```md
# 0003-identity-requires-a-witness.md

## Job

Model conflicting memories in Graphist.

## Blocker

I treated matching names as proof of identity.

## Capability Gained

I can distinguish:
- confirmed identity;
- likely identity;
- unresolved identity;
- false merge.

## Evidence

I repaired the project graph with one hint.

## Remaining Limitation

I have not yet handled identity across changing time scopes.

## Likely Next Blocker

Temporal identity and supersession.
```

This should record changed capability, not summarize the entire lesson.

# 11. Minimal merit calculation

The MVP can avoid a complex 0–100 score.

Use a small status vocabulary:

```text
unassessed
introduced
developing
demonstrated
retained
```

With confidence:

```text
low
medium
high
```

Example:

```yaml
beta-identity:
  level_1:
    status: demonstrated
    confidence: high

  level_2:
    status: developing
    confidence: medium
```

Later versions can introduce weighted merit using accuracy, independence, transfer, retention, and explanation. The MVP only needs enough granularity to choose the next action.

# 12. Minimal resource management

The MVP needs `RESOURCES.md`, but only as a curated registry.

Each entry should say:

* domain;
* level;
* resource type;
* why it is trusted;
* which blocker it addresses.

```md
## Peirce on Beta Graphs

- Domain: Existential Graphs / Beta
- Level: 1–2
- Type: Primary source
- Use for: Lines of identity and quantification
- Notes: Read only the section needed for the current exercise
```

No comprehensive reading roadmap is needed.

# 13. Basic workspace

```text
teaching-workspace/
├── MISSION.md
├── NOW.md
├── NOTES.md
├── RESOURCES.md
├── DOMAIN-MAP.yaml
├── REVIEW-QUEUE.md
│
├── domains/
│   ├── graphist.yaml
│   ├── existential-graphs.yaml
│   ├── rag.yaml
│   └── python.yaml
│
├── assessments/
│   └── 0001-beta-identity.yaml
│
├── learning-records/
│   └── 0001-identity-requires-a-witness.md
│
├── lessons/
│   └── 0001-identity-is-not-name-similarity.html
│
├── reference/
│   └── identity-resolution-checklist.html
│
└── assets/
    └── lesson.css
```

`REVIEW-QUEUE.md` can remain very simple:

```md
- 2026-07-18: Diagnose a new false identity merge without notes.
```

Only useful, already-applied capabilities enter review.

# 14. Commands or modes

The MVP could expose a few explicit modes:

```text
/teach start
/teach continue
/teach assess <domain>
/teach status
/teach explain-decision
```

## `/teach start`

Creates or clarifies the active job.

## `/teach continue`

Reads the workspace and resumes from the current blocker.

## `/teach assess`

Runs a short assessment for one promise.

## `/teach status`

Shows:

* active job;
* current blocker;
* relevant domain;
* current capability estimate;
* next action.

## `/teach explain-decision`

Answers:

* Why are you teaching this?
* Why this difficulty?
* Which assessment supports the level estimate?
* Why is this prerequisite relevant now?

Natural-language invocation should still work; commands merely make the workflow inspectable.

# 15. MVP acceptance test

The MVP succeeds if it can complete this scenario:

### Initial request

> I am building a Graphist representation of Plato’s wax tablet, but I do not know how to represent whether the perceived person and remembered person are the same.

### Expected behavior

1. Create or update `NOW.md`.
2. Ask the learner to draw or describe their current attempt.
3. Diagnose identity representation as the blocker.
4. Locate the relevant Beta-graph or Graphist identity promise.
5. Estimate the learner’s local ZPD.
6. Teach one small lesson on identity versus name similarity.
7. Ask the learner to repair the actual graph.
8. Evaluate the repair.
9. Record the assessment.
10. Update the learning record.
11. Return one next action—not a curriculum.

That is a complete vertical slice.

# Explicit non-goals

The MVP should not include:

* a complete ontology of every learning domain;
* automated curriculum generation;
* social or community features;
* elaborate gamification;
* universal numerical merit scores;
* automatic mastery certification;
* comprehensive spaced-repetition scheduling;
* multi-user classrooms;
* predictive analytics;
* full Graphist integration;
* automatic extraction of every possible prerequisite;
* long-term schedules;
* badges or leaderboards.

# MVP product statement

> **The MVP helps one learner advance one meaningful task by diagnosing one learning blocker, teaching or assessing one domain promise at the right level, verifying immediate application, and preserving evidence for the next session.**

Everything in the MVP should support that sentence.
