# Ontology

## Purpose

This ontology represents normative expectations inside a repository while preserving the distinction between what ought to be true and what any observer believes is true.

## Primitive: domain

A domain is a hierarchical namespace for a promise-bearing type or scope. It is
roughly analogous to an agent in Promise Theory, while adding ancestry so that
promises can be inherited by more specific types and contexts.

Examples:

```text
/
/biology
/biology/botany
/biology/botany/bryology
/software/python/models
```

A domain path is absolute, slash-delimited, normalized, and nestable. Domain hierarchy is defined by path ancestry, not by tags or file placement alone.

A domain may denote a methodology-level type, a host tool's entity or relation
type, a capability family, or a repository scope. A domain is not normally the
concrete instance being judged.

## Primitive: subject

A subject is a token: the particular entity, relation, learner, artifact, or
revision being assessed against promises effective in a domain. For example:

```text
domain:  /skills/ltp/entities/necessary-condition
subject: ltp://projects/metacrisis/entities/NC-17
```

The `necessary_condition` type and the `NC-17` token remain owned by LTP.
Promisify supplies inherited promises and attributable assessments about them;
it does not re-represent the host object or claim its logical status.

## Primitive: promise

A promise is a normative declaration.

It contains:

- a declaring domain;
- a local name;
- a statement of what OUGHT to be true;
- scope and criteria sufficient to make assessment possible;
- optional provenance, source, or authority.

A promise's canonical address is:

```text
{declaring-domain}/{local-name}
```

For the root domain, avoid a double slash:

```text
/_repository_is_reproducible
```

Example:

```text
/biology/botany/_relates_to_plants
```

The local name begins with `_` to distinguish normative declarations from domain segments.

A promise does not contain:

- current status;
- a kept or broken flag;
- a trust score;
- a mutable compliance field;
- a privileged objective truth claim.

Promises may describe normative obligations, general capacities, quality
expectations, or meta-level rules about a method. They may be as granular as the
consumer needs. They are more general than LTP necessary conditions and
hypotheses: not every assessable capacity is an empirical proposition, and not
every promise warrants a causal model.

## Primitive: assessment

An assessment is an assessor's claim about a promise as effective in a domain at a particular observation point.

It contains:

- the canonical promise address;
- the effective domain being judged;
- the assessor identity;
- observation time and repository revision when relevant;
- a verdict;
- evidence and rationale;
- optional confidence and subject scope.

An assessment does not mutate the promise. Multiple assessments may coexist and disagree.

Both type-level and token-level assessments are permitted. Early user-facing
interfaces should normally emphasize token assessment; type-level judgments are
often maintainer or framework-level claims until suitable policy and evidence
are available. Verdicts may represent nuanced, subjective judgment. A binary
kept/broken view is only the smallest profile, not the ontology's limit.

## Derived concept: effective promise

A promise declared at domain `P` is effective in target domain `D` when `P` is equal to `D` or an ancestor of `D`.

The effective promise retains its original canonical address. It may be represented contextually as:

```yaml
promise: /biology/botany/_relates_to_plants
declaredAt: /biology/botany
effectiveAt: /biology/botany/bryology
inherited: true
```

## Derived concept: trust view

A trust view specifies how an observer selects and interprets assessments for a target domain.

It declares:

- observer identity;
- target domain;
- snapshot or revision;
- accepted assessors or filters;
- assessment selection rules;
- disagreement resolution policy;
- scoring unit and weighting policy.

The observer need not be an assessor. An assessor makes a claim; an observer decides which claims contribute to a score.

## Derived concept: trust report

A trust report is generated output from a trust view and a set of promise and assessment records.

It is not a source of truth. It records:

- score;
- coverage;
- counts;
- observer and snapshot;
- policies used;
- selected inputs;
- unresolved disputes.

## Core invariants

1. Promise identity is canonical and stable.
2. Inheritance never rewrites identity.
3. Promise status is never stored on the promise.
4. Assessments are attributable claims, not universal facts.
5. New observations create new assessment records.
6. Trust is calculated, not declared.
7. Every trust result is observer- and policy-relative.
8. Missing evidence is not equivalent to a broken promise.
9. Disagreement is data and must not be silently erased.
10. Broad promises have broad inherited consequences and require deliberate placement.
11. Host-owned types and tokens retain their identity and domain semantics.
12. Type projection creates assessment context, not a duplicate object model.

## Vocabulary

| Term | Meaning |
|---|---|
| Declaring domain | Namespace where the promise originates. |
| Local name | Promise name beginning with `_`. |
| Canonical address | Declaring domain plus local name. |
| Target domain | Domain currently being inspected, assessed, or scored. |
| Subject | Concrete token being assessed in an effective domain. |
| Effective promise | A promise applicable to a target domain through declaration or inheritance. |
| Assessor | Actor or system that makes an assessment claim. |
| Observer | Actor or policy owner whose trust view selects assessment claims. |
| Snapshot | Time or repository revision to which assessments and trust refer. |
| Coverage | Proportion of relevant promises with scorable resolved verdicts. |
