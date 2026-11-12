# AI in development

Design: [docs/09](../09-ia-en-el-desarrollo.md).

## Instruction files

- [AGENTS.md](../../AGENTS.md): short; only what the AI cannot infer from the code (how to run `just check`, what not to touch without asking) and links to these standards.
- [CLAUDE.md](../../CLAUDE.md): imports `@AGENTS.md` and adds only what is specific to Claude Code.
- `.claude/rules/*.md`: rules per zone with a `paths:` list, which only link to this standards document. [backend.md](../../.claude/rules/backend.md) covers `backend/**` and [frontend.md](../../.claude/rules/frontend.md) covers `frontend/**`.
- No rule is duplicated: this standards document is the single source and is linked.

## Claude Code permissions

In [.claude/settings.json](../../.claude/settings.json). Precedence: deny, then ask, then allow. They apply the rules of no history rewriting, no deletion and no dependency changes without permission.

- Allow: `just` recipes except `just setup` and `just update-tools`; `uv run --locked`, `uv sync --locked --all-packages` (a partial `uv sync` would remove part of the shared `.venv`, so it asks); `pnpm install --frozen-lockfile`, `pnpm exec`, `pnpm run`; read-only git (`status`, `diff`, `log`, `show`, branch listing); `git add`, `git commit`, `git switch` and branch creation; and only `git remote get-url origin`; and the read tools of the `github` MCP server ([GitHub access](#github-access)). `just check` installs nothing: `uv run --locked` and `mise exec` use what `just setup` installed from `uv.lock` and `mise.lock`.
- Ask: `just setup`, `just update-tools`, `pnpm dlx`, `create`, `add`, `remove`, `update`; `uvx`, `uv add`, `uv remove`, `uv lock --upgrade`, `uv pip`, `uv tool`; `git push`, `rebase`, `commit --amend`, `reset`, `branch -d` and `-D`, `clean`, `git rm`; `rm`; `curl` and `wget`; the `github` MCP server's write tools; web tools.
- Deny: `git push --force` (also `-f` and `--force-with-lease`), `gh pr merge`, any push to `main`, and reading the use installation folder (`~/Library/Application Support/ivlia`) and the secret folders listed in the file; `security` (the Keychain), and `Edit` on what Claude Code runs outside the sandbox and on its MCP configuration (the list is in [GitHub access](#github-access)).
- Allow, ask and deny rules match the command text and can be bypassed. The real guards are the GitHub ruleset on `main` ([repository.md](repository.md#github)) and the sandbox.

## Bash sandbox

Enabled in the same file (`sandbox`):

- Bash writes only inside the project and the temporary directory, and reaches only `github.com` and `api.github.com`. Reading the use installation folder and the secret folders is denied.
- `autoAllowBashIfSandboxed: false`: a command runs without asking only if it matches the allow list; everything else asks.
- `allowUnsandboxedCommands: false`: Claude cannot retry a command outside the sandbox.
- `excludedCommands`: only `just setup` runs outside the sandbox, and it still asks.
- Verified on 2026-11-09: after `just setup`, `just check` and the pre-commit hook pass inside the sandbox. Exception since 2026-11-11: `end-of-file-fixer` opens each file for writing even when it changes nothing, so inside the sandbox it fails on `.claude/hooks/*.sh`, which the sandbox protects. Commits that touch `.claude/hooks/` are made by the user, who also copies those files in; skipping the hook is not the normal workflow.
- Consequences:
  - `git push` needs the SSH agent and `gh` needs `~/.config/gh`, both outside the sandbox: the user runs them with `!` (for example `git push`, `gh pr create`, `gh pr checks`).
  - Commit signing needs the SSH agent too, so commits in this repository are not signed (`commit.gpgsign false` in `.git/config`). Commits on `main` are created and signed by GitHub at squash merge.
- The sandbox does not cover the Read, Edit, Write and web tools, nor hooks; the permission rules are the only guard for them.

## GitHub access

Claude reads and acts on the repository's pull requests, runs, issues and alerts through GitHub's remote MCP server, which runs at GitHub: on the Mac, GitHub access adds only the `headersHelper` outside the sandbox, which follows the [Hooks](#hooks) rule, and the permission rules match tool names, not command text ([decision map](../decisions/README.md)).

- Server: `https://api.githubcopilot.com/mcp/`, added by the user in Claude Code's user scope (`~/.claude.json`, out of Claude's reach), never in a versioned `.mcp.json`, which Claude could edit. No Copilot subscription was needed (checked on 2026-11-12).
- Credential: a fine-grained personal access token named `ivlia-dev-mcp`, "Only select repositories" with this repository, expiring after 90 days, in the macOS Keychain (service `github-mcp-token`). [github-mcp-headers.sh](../../.claude/bin/github-mcp-headers.sh), installed by the user as `~/.local/bin/github-mcp-headers`, is the server's `headersHelper`: Claude Code runs it outside the sandbox when connecting and sends the headers it prints. It follows the [Hooks](#hooks) rule: `/bin/bash`, `/usr/bin/security` and `PATH=/usr/bin:/bin`. The token is in no file and never in Claude's context, and inside the sandbox `security` does not see the user's Keychain (checked on 2026-11-12). Code that runs outside the sandbox could still read it: hooks run only files Claude cannot write ([Hooks](#hooks)), but the commands the user runs with `!`, the user's own commits (pre-commit), `just setup` and VS Code's extensions run project code ([docs/10](../10-plan-y-pendientes.md)).
- Token permissions: read-only for now: Metadata, Contents, Pull requests, Issues, Actions, Commit statuses, Dependabot alerts and Code scanning alerts. Check runs are read without Checks, since the repository is public. The server is used at `/mcp/readonly`, so the user makes every write ([docs/10](../10-plan-y-pendientes.md)). When docs/10 is resolved, Pull requests, Contents (merging needs it), Actions (re-run and cancel) and Issues get write access.
- Toolsets (header `X-MCP-Toolsets`): `context`, `issues`, `pull_requests`, `actions`, `dependabot`, `code_security`. Not `repos`, which writes files and branches and can delete repositories. Lockdown (`X-MCP-Lockdown`) hides content from users without push access, against injected instructions in a public repository; GitHub states it is a filter, not a security boundary.
- Permissions: read tools (`get_*`, `list_*`, `search_*`, `pull_request_read`, `issue_read`, `actions_get`, `actions_list`) are allowed; write tools (pull requests, issues, comments, reviews, merging, `actions_run_trigger`) ask. `actions_run_trigger` can also start workflows and delete run logs; Claude uses it only to re-run or cancel a run. Claude cannot edit what Claude Code runs outside the sandbox or its MCP configuration: `Edit` is denied on `~/.local/bin/`, `~/.local/share/uv/`, `~/.claude.json`, `.mcp.json`, `.claude/settings.json`, `.claude/settings.local.json` and `.claude/hooks/` (an `Edit` rule also covers writes; Claude Code warns that a `Write` rule never matches).
- Claude merges a PR only when the user asks, with `merge_pull_request` and the squash method; the ruleset on `main` refuses it until the required checks pass.
- Claude does not push: the user runs `git push`. Dismissing a Dependabot alert has no MCP tool, so the user does it.
- The [`pr` skill](../../.claude/skills/pr/SKILL.md) is the procedure.

Setup, once per machine (by the user, in a terminal, from the repository root):

1. In GitHub, create the `release` environment, limited to `main`, with the release key ([release.md](release.md#credential)). Once the branch that adds `environment: release` is on `main`, delete the repository-level copy of the key; until then, `main`'s release workflow still reads it.
2. Create the token (Settings, Developer settings, Fine-grained tokens) with the permissions above.
3. `security add-generic-password -s github-mcp-token -a github-mcp -w`, and paste the token at its prompt, never into a file or an editor.
4. Read `.claude/bin/github-mcp-headers.sh`, then `mkdir -p ~/.local/bin` and `install -m 755 .claude/bin/github-mcp-headers.sh ~/.local/bin/github-mcp-headers`. Install it again, after reading the change, whenever it changes.
5. `claude mcp add-json --scope user github "{\"type\":\"http\",\"url\":\"https://api.githubcopilot.com/mcp/\",\"headersHelper\":\"$HOME/.local/bin/github-mcp-headers\"}"`, then restart Claude Code.

When the token expires, create a new one, replace it with `security add-generic-password -U -s github-mcp-token -a github-mcp -w`, and reconnect the server from `/mcp`.

## Hooks

- PreToolUse on Bash: `researcher-bash-guard.py` limits the read-only Bash of the `researcher` agent. Its test (`.claude/hooks/researcher-bash-guard.test.sh`) runs in `just check`.
- Hooks run outside the Bash sandbox, with the user's permissions, and so does the `headersHelper` ([GitHub access](#github-access)). Rule: what Claude Code runs outside the sandbox runs only files with an absolute path that Claude cannot write, apart from the hook's own script in `.claude/hooks/`, which the sandbox and the `Edit` rules protect. Nothing from `.venv`, `node_modules` or the `PATH`, which starts with `node_modules/.bin` (`_.path` in `mise.toml`).
- The guard is standard-library Python. Claude Code starts it in the hook's exec form, without a shell of its own: `command` is `/bin/sh`, by absolute path, and `args` is `-c` with `exec "$HOME/.local/bin/python3.14" -I "$CLAUDE_PROJECT_DIR/.claude/hooks/researcher-bash-guard.py"`. `/bin/sh` only expands the two variables, so no program is looked up in the `PATH`. `~/.local/bin/python3.14` is the uv-managed Python of `.python-version`, which the user installs with `uv python install 3.14`. The sandbox keeps Claude from writing in `~/.local/`, and `Edit` is denied on `~/.local/bin/` and `~/.local/share/uv/`. When `.python-version` changes its minor version, the hook's path changes with it. If the interpreter is missing, the hook fails and `onFailure: "block"` blocks every Bash command.
- The test runs the guard with the root `.venv`'s Python, the same version, because CI has no `~/.local/bin/python3.14`.
- No hook runs after edits: it would run the linters from `.venv` and `node_modules` outside the sandbox. pre-commit reports problems at commit, inside the sandbox; to check earlier, Claude runs `uv run --locked pre-commit run --files <files>`.

## Validar

Procedure in the skill [validar](../../.claude/skills/validar/SKILL.md) (Spanish until `.claude/` is translated), run before each step and slice.

- The `researcher` agent, with the Sonnet model, reads current official docs and versions (network use confirmed by the user) and compares them with the design, the plan and the repository.
- The report (confirmed, changed, risks, sources with how much was read) is saved in `.dev/validar-step-N.md` (gitignored) and shown to the user before work starts. Its summary goes in the PR description.
- Versions are checked against the 7-day cooldown ([README](README.md#versions-policy)).

## Reviewer

The [reviewer](../../.claude/agents/reviewer.md) agent (Opus, tools Read, Grep and Glob only, no network, clean context) reviews each branch before the user. After `just check` is green, `just review-diff` (or `just review-diff <parent-branch>` for a stacked PR) writes the diff and file list to `.dev/review/`; the reviewer reads them and reports findings by severity. The findings and how they were handled go in the PR.

## Other skills

- [research](../../.claude/skills/research/SKILL.md) (Spanish until `.claude/` is translated): queries the project's configured knowledge sources through `researcher` agents and synthesizes what they return.
- [pr](../../.claude/skills/pr/SKILL.md): pull requests through the `github` MCP server: create, update a stacked branch after a squash merge, checks and merge ([GitHub access](#github-access)).
- [review-file](../../.claude/skills/review-file/SKILL.md): explains one development tool or configuration file in junior-level terms and reviews it against the [Toolchain rules](repository.md#toolchain-rules).

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
