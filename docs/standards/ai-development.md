# AI in development

Design: [docs/09](../09-ia-en-el-desarrollo.md).

## Instruction files

- [AGENTS.md](../../AGENTS.md): short; only what the AI cannot infer from the code (how to run `just check`, what not to touch without asking) and links to these standards.
- [CLAUDE.md](../../CLAUDE.md): imports `@AGENTS.md` and adds only what is specific to Claude Code.
- `.claude/rules/*.md`: rules per zone (backend, frontend) with a `paths:` list; added from step 2.
- No rule is duplicated: this standards document is the single source and is linked.

## Claude Code permissions

In [.claude/settings.json](../../.claude/settings.json). Precedence: deny, then ask, then allow. They apply the rules of no history rewriting, no deletion and no dependency changes without permission.

- Allow: `just` recipes except `just setup` and `just update-tools`; `uv run --locked`, `uv sync --locked`; `pnpm install --frozen-lockfile`, `pnpm exec`, `pnpm run`; read-only git (`status`, `diff`, `log`, `show`, branch listing); `git add`, `git commit`, `git switch` and branch creation; and only `gh pr view`, `gh pr diff`, `gh pr checks`, `gh run view`, `gh issue view`. Pinned downloads that `just check` makes (pre-commit environments) count as installs from a lockfile.
- Ask: `just setup`, `just update-tools`, `pnpm dlx`, `create`, `add`, `remove`, `update`; `uvx`, `uv add`, `uv remove`, `uv lock --upgrade`, `uv pip`, `uv tool`; `git push`, `rebase`, `commit --amend`, `reset`, `branch -d` and `-D`, `clean`, `rm`; `rm`; `curl` and `wget`; every other `gh` command; web tools.
- Deny: `git push --force` (also `-f` and `--force-with-lease`), `gh pr merge`, any push to `main`, and reading the use installation folder (`~/Library/Application Support/ivlia`) and the secret folders listed in the file.
- Allow, ask and deny rules match the command text and can be bypassed. The real guards are the GitHub ruleset on `main` ([repository.md](repository.md#github)) and the sandbox.

## Bash sandbox

Enabled in the same file. Bash can write only inside the project and reach only the allowed network domains. It does not cover the Read, Edit, Write and web tools, nor hooks, so the permission rules stay the guard for those. `just setup` installs tools, dependencies, pre-commit environments and browsers; it asks and runs outside the sandbox with the user's approval. Every other recipe runs inside it.

## Hooks

- PreToolUse on Bash: `researcher-bash-guard.py` limits the read-only Bash of the `researcher` agent; its test (`.claude/hooks/researcher-bash-guard.test.sh`) runs in `just check`.
- From step 2: a PostToolUse hook runs the fast checks (formatter and linter) after each edit.

## Validar

Procedure in the skill [validar](../../.claude/skills/validar/SKILL.md) (Spanish until `.claude/` is translated), run before each step and slice.

- The `researcher` agent, with the Sonnet model, reads current official docs and versions (network use confirmed by the user) and compares them with the design, the plan and the repository.
- The report (confirmed, changed, risks, sources with how much was read) is saved in `.dev/validar-step-N.md` (gitignored) and shown to the user before work starts. Its summary goes in the PR description.
- Versions are checked against the 7-day cooldown ([README](README.md#versions-policy)).

## Reviewer

The [reviewer](../../.claude/agents/reviewer.md) agent (Opus, tools Read, Grep and Glob only, no network, clean context) reviews each branch before the user. After `just check` is green, `just review-diff` writes the diff and file list to `.dev/review/`; the reviewer reads them and reports findings by severity. The findings and how they were handled go in the PR.

## OpenSpec

- Run with `pnpm exec openspec` (version in [package.json](../../package.json)). Telemetry is off (`OPENSPEC_TELEMETRY=0`, `DO_NOT_TRACK=1` in the justfile).
- Initialized with `pnpm exec openspec init --tools claude`. Generated: `.claude/skills/openspec-*/` and `.claude/commands/opsx/`; after an upgrade, run `openspec update`. Edited by people: [openspec/config.yaml](../../openspec/config.yaml) and `openspec/specs/`.
- `just check` runs `openspec validate --all --strict`.
- Phase 0 is built without the OpenSpec cycle; the cycle is used from slice 2.

## AI per task

Provisional, from [docs/09](../09-ia-en-el-desarrollo.md) ("IA por tarea"): proposing, specifying and designing, the most capable model; implementing specified tasks, a faster model (Sonnet); independent review, a subagent with clean context (Opus); research, read-only subagents (Sonnet, Haiku for mechanical searches).

## Rules for the AI

- Quality tools guide it: it runs the checks through `just`, reads the errors and fixes them before the user reviews.
- It does not finish a task while a check fails, and does not disable or relax a rule to make it pass.
- It does not edit generated files by hand.
