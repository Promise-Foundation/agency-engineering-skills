# Agent workflows

## Workflow A: initialize a repository

1. Inspect existing architecture, policy, security, testing, and contribution documents.
2. Create `.norms/repository.yaml`, `promises/`, `assessments/`, and `views/`.
3. Create a default trust view with an explicit observer and conservative initial assessor filter.
4. Encode only user-requested or repository-grounded promises.
5. Validate all files.
6. Report inherited scope for each broad promise.

## Workflow B: turn natural language into a promise

Input:

```text
A Class OUGHT to be defined with Pydantic.
```

Agent procedure:

1. Ask or infer from repository context which classes and domain are intended; do not make a root promise unless universal scope is clear.
2. Choose a precise statement, for example: "Python classes classified as domain models OUGHT to inherit from `pydantic.BaseModel`."
3. Define an assessable selector and criterion.
4. Create the promise without a status.
5. Validate address, domain placement, and schema.

## Workflow C: assess a target domain

1. Resolve the target domain's effective promises.
2. Fix the current revision.
3. For each promise, inspect criteria and evidence requirements.
4. Run deterministic repository tools before relying on prose judgment.
5. Emit one domain-level assessment or clearly scoped subject-level assessments.
6. Keep conflicts and uncertainty visible.
7. Do not calculate trust until the assessment set and view are known.

## Workflow D: compute trust

1. Load the view.
2. Resolve effective promises.
3. Select and resolve assessments.
4. Compute score and coverage.
5. Write a report only when requested; otherwise return the same fields in the agent response.
6. Identify promises excluded from scoring and why.

## Workflow E: repair

1. Start from broken assessments accepted by the chosen view.
2. Map each violation to implementation evidence.
3. Propose the smallest implementation change that can satisfy the promise without degrading unrelated behavior.
4. Run native tests and targeted assessment checks.
5. Create new post-change assessment records.
6. Recompute the same trust view.
7. Show before/after score, coverage, changed promises, and remaining disputes.

## Workflow F: change a norm

Changing what OUGHT to be true is not a repair. When the user intentionally changes a promise:

1. Identify whether the existing promise should be edited, versioned, or replaced.
2. Preserve history through version control and source rationale.
3. Do not retroactively relabel old assessments; they remain claims about the old snapshot and declaration.
4. Reassess current implementation against the new declaration.

## Agent report language

Prefer:

```text
Under observer team/architecture's default view at commit abc123,
8 of 10 scorable effective promises are kept. Trust is 0.80 with
83% coverage. Two promises are unknown and one is not applicable.
```

Avoid:

```text
The domain is 80% trustworthy.
```

The latter hides observer, policy, time, coverage, and disagreement.
