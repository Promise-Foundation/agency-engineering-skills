# Domain resolution and inheritance

## Normalized paths

Valid domain paths:

```text
/
/biology
/biology/botany
/software/python/models
```

Invalid paths:

```text
biology/botany       # not absolute
/biology/            # trailing slash
/biology//botany     # empty segment
/biology/../botany   # traversal segment
```

Segments use lowercase letters, numbers, `_`, or `-`, and begin with a lowercase letter or number.

## Ancestors

The ancestors of `/biology/botany/bryology`, including itself, are:

```text
/
/biology
/biology/botany
/biology/botany/bryology
```

## Applicability rule

A promise declared at domain `P` is effective at domain `D` exactly when:

```text
P == D
or
D begins with P + "/"
```

The root domain `/` is an ancestor of every domain.

Do not use raw string prefix matching without a segment boundary: `/bio` is not an ancestor of `/biology`.

## Effective set

For target domain `D`:

```text
effective(D) = union of promises declared at every ancestor of D, including D
```

Resolution walks root to leaf to preserve provenance and deterministic display order.

## Canonical identity

A promise inherited into a child retains its declaration address.

```text
Declared:  /biology/botany/_relates_to_plants
Effective: /biology/botany/bryology
Identity:  /biology/botany/_relates_to_plants
```

Never synthesize `/biology/botany/bryology/_relates_to_plants` unless a distinct promise was declared there.

## Local-name collisions

Version 1 uses accumulation, not implicit shadowing.

These are distinct promises:

```text
/biology/_preserves_life
/biology/botany/_preserves_life
```

Both are effective in `/biology/botany` and descendants. Similar local names do not imply replacement, refinement, or contradiction.

Future versions may add explicit relations such as `refines`, `supersedes`, or `excepts`, but agents must not infer these relations from names alone.

## Domain placement test

Before declaring a promise at domain `D`, ask:

1. Should the rule apply to `D` itself?
2. Should it apply to every current child?
3. Should it automatically apply to every future child?
4. Is there a narrower domain that expresses the intended scope?

Choose the highest domain for which all answers are yes.

## File mapping

A promise file path mirrors its declaring domain beneath `.norms/promises/`:

```text
Address: /biology/botany/_relates_to_plants
File:    .norms/promises/biology/botany/_relates_to_plants.yaml
```

Root promises live directly under `.norms/promises/`:

```text
Address: /_repository_is_reproducible
File:    .norms/promises/_repository_is_reproducible.yaml
```

The validator checks that metadata and file placement agree.
