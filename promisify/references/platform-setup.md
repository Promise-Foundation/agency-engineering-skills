# Platform setup

## Open Agent Skills package

The portable unit is this directory, whose required entrypoint is `SKILL.md`. Supporting documentation is under `references/`, deterministic helpers under `scripts/`, and templates and schemas under `assets/`.

## Codex

Repository installation:

```text
<repo>/.agents/skills/normative-promises/SKILL.md
```

Codex can select the skill implicitly from its description or explicitly through the skill picker or mention mechanism supported by the client.

Use `AGENTS.md` for small, always-loaded repository guidance. The skill itself is better for this multi-step, reference-heavy workflow because its body loads only when selected.

## Claude Code

Repository installation:

```text
<repo>/.claude/skills/normative-promises/SKILL.md
```

Claude Code can select the skill when relevant or invoke it as `/normative-promises`.

Claude Code reads `CLAUDE.md` rather than `AGENTS.md`. To share root guidance, create:

```markdown
@AGENTS.md
```

or use the provided snippets.

## One canonical copy

In a repository supporting both clients, keep the canonical skill under `.agents/skills/normative-promises` and symlink `.claude/skills/normative-promises` to it, or copy the same directory to both locations.

## Hosted skill upload

The downloadable zip contains one top-level `normative-promises/` directory, matching hosted skill bundle expectations.

## Verification prompts

After installation, test discovery with:

```text
List the promises effective in /biology/botany and explain their provenance.
```

Test behavior with:

```text
Encode the rule that Python domain models under /software/python/models OUGHT to inherit from pydantic.BaseModel. Do not assess it yet.
```

The agent should create a promise only and must not add a kept or broken field.
