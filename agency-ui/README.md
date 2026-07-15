# agency-ui

A read-only shell that hosts agency-engineering skills as **plugins**, with the
seams for mutable data (ZPD) baked in from day one.

The shell owns *where and how* work is presented. A plugin owns *what its
concepts mean*. Shared contracts own *how skills refer to each other's resources
and capabilities*. No plugin imports another.

```
apps/web            the shell (nav, workspace, inspector, command palette, dashboard)
packages/
  agency-skill-sdk  the contract: AgencySkillPlugin + the ResourceSource seam + conformance kit
  agency-core       the runtime: PluginHost, FederatedResourceService, static + live sources
  ui-kit            shared React primitives
skills/
  ltp-plugin        LTP as read-only plugin #1 (static source over dashboard-model.json)
  hypothesize-plugin plugin #2 (static source over research-status.json)
apps/web/src/demo   a live, writable ZPD stand-in (proves mutable data hosts cleanly)
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

## Develop

```bash
npm install
npm run typecheck          # tsc across the whole workspace (strict)
npm test                   # vitest: runtime + seam + conformance
npm run build              # build the shell app
npm run dev                # vite dev server (http://127.0.0.1:5178)
```

The dev server reads two generated manifests from `apps/web/public/api/` — LTP's
`dashboard-model.json` and hypothesize's `research-status.json` — exactly the
files those skills' engines already produce.

## Adding a skill

1. Create `skills/<name>-plugin` exporting an `AgencySkillPlugin`.
2. In `activate()`, register a `ResourceSource` (a `manifestSource` for a static
   skill, or a live source for a mutable one) and any capabilities/commands.
3. Declare `contributions` (routes, dashboard cards, resource views, inspectors,
   commands) in the manifest.
4. Add it to `apps/web/src/plugins.ts`. The shell needs no other change.
