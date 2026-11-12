# AI in development

Design: [docs/09](../09-ia-en-el-desarrollo.md).

## Instruction files

- [AGENTS.md](../../AGENTS.md): short; only what the AI cannot infer from the code (how to run `just check`, what not to touch without asking) and links to these standards.
- [CLAUDE.md](../../CLAUDE.md): imports `@AGENTS.md` and adds only what is specific to Claude Code.
- `.claude/rules/*.md`: rules per zone with a `paths:` list, which only link to this standards document. [backend.md](../../.claude/rules/backend.md) covers `backend/**` and [frontend.md](../../.claude/rules/frontend.md) covers `frontend/**`.
- No rule is duplicated: this standards document is the single source and is linked.

## Claude Code permissions

In [.claude/settings.json](../../.claude/settings.json). Precedence: deny, then ask, then allow. They apply the rules of no history rewriting, no deletion and no dependency changes without permission.

- Allow: `just` recipes except `just setup` and `just update-tools`; `uv run --locked`, `uv sync --locked --all-packages` (a partial `uv sync` would remove part of the shared `.venv`, so it asks); `pnpm install --frozen-lockfile`, `pnpm exec`, `pnpm run`; read-only git (`status`, `diff`, `log`, `show`, branch listing); `git add`, `git commit`, `git switch` and branch creation; and only `gh pr view`, `gh pr diff`, `gh pr checks`, `gh run view`, `gh issue view`; and the read tools of the `github` MCP server ([GitHub access](#github-access)). `just check` installs nothing: `uv run --locked` and `mise exec` use what `just setup` installed from `uv.lock` and `mise.lock`.
- Ask: `just setup`, `just update-tools`, `pnpm dlx`, `create`, `add`, `remove`, `update`; `uvx`, `uv add`, `uv remove`, `uv lock --upgrade`, `uv pip`, `uv tool`; `git push`, `rebase`, `commit --amend`, `reset`, `branch -d` and `-D`, `clean`, `git rm`; `rm`; `curl` and `wget`; every other `gh` command; the `github` MCP server's write tools; web tools.
- Deny: `git push --force` (also `-f` and `--force-with-lease`), `gh pr merge`, any push to `main`, and reading the use installation folder (`~/Library/Application Support/ivlia`) and the secret folders listed in the file; `security` (the Keychain), and `Edit` and `Write` on `~/.local/bin/` and `~/.claude.json`, which hold what Claude Code runs and its MCP configuration.
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

Claude reads and acts on the repository's pull requests, runs, issues and alerts through GitHub's remote MCP server, which runs at GitHub: nothing runs on the Mac outside the sandbox, and the permission rules match tool names, not command text. A first design ran `gh` outside the sandbox through a wrapper; four review rounds kept finding ways to run code outside it (the script's path, the working directory, `PATH`, git hooks and settings), so it was dropped (2026-11-12).

- Server: `https://api.githubcopilot.com/mcp/`, added by the user in Claude Code's user scope (`~/.claude.json`, out of Claude's reach), never in a versioned `.mcp.json`, which Claude could edit. No Copilot subscription was needed (checked on 2026-11-12).
- Credential: a fine-grained personal access token, "Only select repositories" with this repository, expiring after 90 days, in the macOS Keychain (service `github-mcp-token`). [github-mcp-headers.sh](../../.claude/bin/github-mcp-headers.sh), installed by the user as `~/.local/bin/github-mcp-headers`, is the server's `headersHelper`: Claude Code runs it when connecting and sends the headers it prints. The token is in no file and never in Claude's context; inside the sandbox `security` does not see the user's Keychain (checked on 2026-11-12).
- Token permissions: Metadata read; Pull requests, Contents (merging needs it), Actions (re-run and cancel) and Issues read and write; Commit statuses, Checks, Dependabot alerts and Code scanning alerts read.
- Toolsets (header `X-MCP-Toolsets`): `context`, `issues`, `pull_requests`, `actions`, `dependabot`, `code_security`. Not `repos`, which writes files and branches and can delete repositories. Lockdown (`X-MCP-Lockdown`) hides content from users without push access, against injected instructions in a public repository; GitHub states it is a filter, not a security boundary.
- Permissions: read tools (`get_*`, `list_*`, `search_*`, `pull_request_read`, `issue_read`, `actions_get`, `actions_list`) are allowed; write tools (pull requests, issues, comments, reviews, merging, `actions_run_trigger`) ask.
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

- PreToolUse on Bash: `researcher-bash-guard.py` limits the read-only Bash of the `researcher` agent; its test (`.claude/hooks/researcher-bash-guard.test.sh`) runs in `just check`.
- PostToolUse on `Edit` and `Write`: `lint-after-edit.py` formats and lints each file Claude edits with pre-commit's file tools (same order and ignore files), so problems are reported while writing ([repository.md](repository.md)). Through `mise exec`, from the root, with the path relative to it:
  - Text files that no formatter owns: `end-of-file-fixer` and `trailing-whitespace-fixer` (their exit code 1 with a `Fixing <file>` message means they fixed the file; with anything on stderr, such as a traceback, it is an error).
  - GitHub Actions files: zizmor (`--offline`), and actionlint for workflows.
  - Shell scripts: shellcheck.
  - Markdown: `markdownlint-cli2 --fix`.

  File types come from identify (`uv run --locked identify-cli`), the library pre-commit uses for `types`, so a file is a shell script, YAML or Markdown exactly when it is for pre-commit (for example, a shebang counts only in an executable file).
  - Python in `backend/` and `.claude/hooks/`: `ruff check --fix`, then `ruff format` (`uv run --locked`).
  - Any file: Prettier with `--ignore-unknown`.
  - `frontend/**/*.ts(x)`: `eslint --fix`.

  gitleaks and pre-commit-hooks' commit checks (large files, case and merge conflicts) are not in the hook: they check the commit, not one file. Generated code is skipped by the tools' ignore files. Errors the tools cannot fix go back to Claude (exit code 2), so it fixes them in its next step. Files outside the repository are ignored. Its test (`.claude/hooks/lint-after-edit.test.sh`) runs in `just check`; it writes scratch folders in `backend/`, `frontend/src/` and the root, the last two neither hidden nor gitignored, because TypeScript, Prettier and markdownlint skip those, and two workflows in `.github/workflows/` itself, where zizmor and actionlint look; all are removed on exit. The first version was checked in a live session on 2026-11-10, and the current one on 2026-11-11 (markdownlint, shellcheck and zizmor each reported an error back to Claude).
- Both hooks are standard-library Python, run through `.claude/hooks/python.sh` with the project's Python (the root `.venv`, as in `just check` and CI), in isolated mode (`-I`). Without the `.venv`, the wrapper exits 2 and asks to run `just setup`, so neither hook fails without a reason; the researcher's guard also blocks on any failure (`onFailure: "block"`). Both tests run the hooks through it. Hooks run outside the Bash sandbox.

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
