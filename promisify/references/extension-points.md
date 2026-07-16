# Extension points

Version 1 deliberately leaves several semantics as explicit policies rather than pretending they are universal.

## Promise relations

Potential future relations:

- `refines`
- `supersedes`
- `conflictsWith`
- `dependsOn`
- `excepts`

Version 1 does not infer any of these from matching names or domain placement.

## Host type projection

Agency Engineering plugins may declare host-owned entity or relation types as
Promisify subdomains. A declaration needs a stable host resource type, a domain
prefix, a subtype discriminator when applicable, and separate type/token
assessment permissions. The host remains authoritative for object identity and
meaning. The projection only supplies inherited promise context.

The agency UI SDK carries this declaration as a `promiseTypes` contribution.
Persisting those declarations into `.norms/`, authoring assessments, and syncing
them through a shared runtime remain planned; the prototype shell must not claim
those operations are already available.

## Exceptions

Inheritance currently has no implicit opt-out. A future exception record should identify authority, scope, justification, and the promise being excepted. Until such a record type is specified, represent exceptions as separate promises or documented assessment applicability decisions rather than silently suppressing inheritance.

## Subject aggregation

Subject-level assessments may be aggregated by policies such as:

- universal: any broken subject breaks the promise;
- threshold: kept proportion must meet a declared threshold;
- existential: at least one kept subject satisfies the promise;
- weighted subject importance.

The policy must be explicit before subject assessments contribute to promise-level trust.

## Weighted trust

Future views may assign weights by promise address, tag, authority, or severity. Weights belong to the view or a referenced policy, not to objective truth.

## Trust transitivity

Version 1 does not infer trust between domains, actors, repositories, or assessors. A high score in a parent or child domain does not automatically determine another domain's score.

## Assessor trust

A future observer policy may assign credibility to assessors. This is separate from confidence reported by the assessor and separate from promise trust.

## Temporal decay

Version 1 uses snapshots and explicit selection. It does not decay old assessments automatically. A future policy may define staleness windows.

## Cryptographic provenance

Assessment signatures, content hashes, and transparency logs can be added without changing the core ontology. They prove origin or integrity, not correctness.

## External evidence

MCP tools or remote services may supply evidence, but assessment records should preserve stable references and avoid claiming remote data is timeless.
