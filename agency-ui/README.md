# agency-ui

A prototype domain-oriented shell that hosts agency-engineering skills as
**plugins**, with seams for mutable data demonstrated by a ZPD stand-in.

The shell owns *where and how* work is presented, including the active domain. A
plugin owns *what its concepts mean*. Shared contracts own *how skills refer to
each other's resources and capabilities*. No plugin imports another.

```
apps/web            the shell (nav, workspace, inspector, command palette, dashboard)
packages/
  agency-skill-sdk  the contract: AgencySkillPlugin + the ResourceSource seam + conformance kit
  agency-core       the runtime: PluginHost, FederatedResourceService, static + live sources
  ui-kit            shared React primitives
skills/
  promisify-plugin  the optional shared domain hierarchy and promise view
  ltp-plugin        domain-addressed, read-only LTP artifacts
  hypothesize-plugin domain-addressed, read-only research artifacts
apps/web/src/demo   a live, writable, domain-scoped ZPD stand-in
```

## The one idea

Nothing talks to "a file" or "a database" — everything reads and writes through a
`ResourceSource`. Read-only vs. mutable is a *declared capability of the source*
(`determinism: static | live`, `readable/watchable/writable`), not a different
code path. A `static` source (LTP, hypothesize) is reproducible and never
writable; a `live` source (ZPD) is watchable and writable. **Hosting mutable data
later is one new source implementation — zero change to the shell, the other
plugins, or the resource shape.** The conformance kit enforces the invariant that
makes this safe: `static ⇒ !writable`.

When Promisify is installed, it publishes the discovered hierarchy as neutral
`agency.domain` resources. The shell keeps one URL-backed active domain above
ordinary resource selection, so opening a claim in the inspector never loses
the domain being worked on. Skill navigation is orthogonal: choosing LTP,
Hypothesize, ZPD, or Promises passes that same domain reference to the selected
plugin view.

Plugin dependencies use three strengths: `requires` blocks activation,
`recommendedDependencies` preserves standalone operation, and
`optionalDependencies` enables an integration silently when present. ZPD
requires Promisify; LTP and Hypothesize recommend it.

LTP declares `promiseTypes` contributions for its host-owned entity and causal
claim types. These declarations specify the future Promisify subdomain and
whether type and token assessments are user-facing. The prototype does not yet
persist those declarations into `.norms/` or write assessments; LTP remains the
owner of every entity, relation, and logical status.

## Develop

```bash
npm install
npm run content:build      # validate Promisify and publish the shared domain explorer
npm run typecheck          # tsc across the whole workspace (strict)
npm test                   # vitest: runtime + seam + conformance
npm run build              # build the shell app
npm run dev                # vite dev server (http://127.0.0.1:5178)
```

The dev server reads domain-addressed artifact bundles from
`apps/web/public/api/`. `content:build` validates the repository's normative
model and regenerates Promisify's domain explorer. LTP and Hypothesize publish
their own bundles through their own generators or adapters. A promise is never
converted into an LTP necessary condition or a hypothesis by this build.

## Serving real skill content

The shell renders whatever the engines *previously generated*; it never
re-derives anything in the browser. Build the current repository content before
starting the UI:

```bash
npm run content:build
npm run dev
```

Each skill owns its source model and publishes a domain-addressed artifact under
`apps/web/public/api/`. A skill with no artifact for the active domain displays
a clear not-generated state. LTP, Hypothesize, and ZPD do not infer their object
models from promises.

## Maturity boundary

The shell currently demonstrates plugin isolation, shared domain selection,
static read-only sources, a writable in-memory source, and typed cross-skill
references. It does not yet provide an immutable event history, durable scoped
permissions, challenge/adjudication, interruption, replay, or rollback. Those
are specified Agency Engineering runtime requirements, not shipped shell
capabilities.

## Adding a skill

1. Create `skills/<name>-plugin` exporting an `AgencySkillPlugin`.
2. In `activate()`, register a `ResourceSource` (a `manifestSource` for a static
   skill, or a live source for a mutable one) and any capabilities/commands.
3. Declare `contributions` (routes, dashboard cards, resource views, inspectors,
   commands) in the manifest.
4. Add it to `apps/web/src/plugins.ts`. The shell needs no other change.
