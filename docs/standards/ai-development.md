# AI in development

Design: [docs/09](../09-ia-en-el-desarrollo.md).

## Instruction files

- [AGENTS.md](../../AGENTS.md): short; only what the AI cannot infer from the code (how to run `just check`, what not to touch without asking) and links to these standards.
- [CLAUDE.md](../../CLAUDE.md): imports `@AGENTS.md` and adds only what is specific to Claude Code.
- `.claude/rules/*.md`: rules per zone with a `paths:` list, which only link to this standards document. [backend.md](../../.claude/rules/backend.md) covers `backend/**` and [frontend.md](../../.claude/rules/frontend.md) covers `frontend/**`.
- No rule is duplicated: this standards document is the single source and is linked.

## Claude Code permissions

In [.claude/settings.json](../../.claude/settings.json). Precedence: deny, then ask, then allow. They apply the rules of no history rewriting, no deletion and no dependency changes without permission.

- Allow: `just` recipes except `just setup` and `just update-tools`; `uv run --locked`, `uv sync --locked --all-packages` (a partial `uv sync` would remove part of the shared `.venv`, so it asks); `pnpm install --frozen-lockfile`, `pnpm exec`, `pnpm run`; read-only git (`status`, `diff`, `log`, `show`, branch listing); `git add`, `git commit`, `git switch` and branch creation; and only the read-only `~/.local/bin/gh-repo` commands: `pr view`, `pr diff`, `pr checks`, `pr list`, `pr status`, `run list`, `run view`, `issue view`, `issue list`, `repo view` ([GitHub access](#github-access)). `just check` installs nothing: `uv run --locked` and `mise exec` use what `just setup` installed from `uv.lock` and `mise.lock`.
- Ask: `just setup`, `just update-tools`, `pnpm dlx`, `create`, `add`, `remove`, `update`; `uvx`, `uv add`, `uv remove`, `uv lock --upgrade`, `uv pip`, `uv tool`; `git push`, `rebase`, `commit --amend`, `reset`, `branch -d` and `-D`, `clean`, `git rm`; `rm`; `curl` and `wget`; every `~/.local/bin/gh-repo` subcommand that writes (pull requests, runs, issues, and all of `api`); web tools.
- Deny: `git push --force` (also `-f` and `--force-with-lease`), any push to `main`, the other destructive pushes and `git push` options of [GitHub access](#github-access), `security`, `Edit` and `Write` on `~/.local/bin/`, `.git/hooks` and `.git/config` (deny rules for `Edit` also bind the sandbox: one on all of `.git/` blocked commits, seen on 2026-11-12), and reading the use installation folder (`~/Library/Application Support/ivlia`) and the secret folders listed in the file.
- Allow, ask and deny rules match the command text and can be bypassed. The real guards are the GitHub ruleset on `main` ([repository.md](repository.md#github)) and the sandbox.

## Bash sandbox

Enabled in the same file (`sandbox`):

- Bash writes only inside the project and the temporary directory, and reaches only `github.com` and `api.github.com`. Reading the use installation folder and the secret folders is denied.
- `autoAllowBashIfSandboxed: false`: a command runs without asking only if it matches the allow list; everything else asks.
- `allowUnsandboxedCommands: false`: Claude cannot retry a command outside the sandbox.
- `excludedCommands`: `just setup`, `~/.local/bin/gh-repo` and `git push origin` (also with `-u`) run outside the sandbox, and still go through the permission rules. An excluded command runs with the user's full access ([GitHub access](#github-access)).
- Verified on 2026-11-09: after `just setup`, `just check` and the pre-commit hook pass inside the sandbox. Exception since 2026-11-11: `end-of-file-fixer` opens each file for writing even when it changes nothing, so inside the sandbox it fails on `.claude/hooks/*.sh`, which the sandbox protects. Commits that touch `.claude/hooks/` are made by the user, who also copies those files in; skipping the hook is not the normal workflow.
- Consequences:
  - Inside the sandbox, `gh` cannot verify TLS on macOS (Claude Code's sandboxing docs list it among the Go tools that fail) nor read the user's Keychain, which is why `gh` and `git push` run outside it. `git fetch` stays inside: the repository is public.
  - Commit signing needs the SSH agent, so commits in this repository are not signed (`commit.gpgsign false` in `.git/config`). Commits on `main` are created and signed by GitHub at squash merge.
- The sandbox does not cover the Read, Edit, Write and web tools, nor hooks; the permission rules are the only guard for them.

## GitHub access

Claude works on the repository's pull requests, runs and issues with its own token, limited to this repository. Nothing in the repository names the repository: a fork uses its own token the same way.

- The scripts live in [.claude/bin/](../../.claude/bin/) and the user installs them in `~/.local/bin`, where Claude cannot write (the sandbox, and deny rules for `Edit` and `Write`). The permission rules and `excludedCommands` match the text `~/.local/bin/gh-repo`: a copy elsewhere, or a `gh-repo` found earlier in `PATH` (the project's `.venv/bin` comes first), does not match, so it stays inside the sandbox and asks.
- `gh-repo` runs `gh` with `GH_TOKEN` from the macOS Keychain (service `gh-repo-token`, account `OWNER/REPO` of `origin`, read by `github-repo.sh`), `GH_REPO` set to that repository, and an empty `gh` configuration (no aliases, extensions or user settings). It accepts only the subcommands it lists; anything else, such as `auth`, `alias`, `config`, `extension`, `pr checkout` or `run download`, is refused before `gh` runs. In `pr merge` and `pr update-branch` it also refuses `--rebase`, `--delete-branch` and `-d`, which rewrite history or delete branches.
- `git push` goes over HTTPS with `git-credential-gh-repo` as the only credential helper for github.com, set by its absolute path, so a push uses the same token. Run by Claude directly, the helper stays inside the sandbox, where the user's Keychain is not visible (checked on 2026-11-12: `security` sees only the system keychain there).
- The token is a fine-grained personal access token, "Only select repositories" with this repository, expiring after 90 days. Repository permissions: Metadata read; Contents, Pull requests, Actions, Workflows, Issues and Dependabot alerts read and write; Commit statuses, Checks and Code scanning alerts read. Workflows write is needed to push changes to `.github/workflows/`; the release key is out of reach of branch runs ([release.md](release.md#credential)).
- Claude merges only when the user asks, with `gh-repo pr merge --auto --squash`: GitHub merges once the required checks pass ([repository.md](repository.md#github)).
- `git push` runs outside the sandbox only as `git push origin` (also with `-u`). Denied: `--receive-pack` and `--exec` (they run a local program), force pushes in any form (`--force`, `+branch`), deletions (`--delete`, `-d`, `:branch`) and pushes to `main`. The sandbox and deny rules keep Claude out of `.git/hooks` and `.git/config`, whose hooks and settings (such as `core.hooksPath`) a push would run. `security` is denied.
- The [`pr` skill](../../.claude/skills/pr/SKILL.md) is the procedure: create, update a stacked branch after a squash merge, checks and merge.
- Accepted risk: `gh-repo` and `git push` run with the user's full access, so a command could send a local file to GitHub (for example `gh-repo api -F field=@file`). Every write asks, `api` included, and the token reaches only this repository. Not verified: whether Claude Code checks an output redirection on an excluded command; the `pr` skill never chains or redirects them.

Setup, once per clone (by the user, in a terminal, from the repository root):

1. In GitHub: create the `release` environment, limited to `main`, with the release key ([release.md](release.md#credential)), and turn on "Allow auto-merge" (Settings, General). Once the branch that adds `environment: release` is on `main`, delete the repository-level copy of the key; until then, `main`'s release workflow still reads it.
2. Read the scripts in `.claude/bin/`, then install them: `install -m 755 .claude/bin/gh-repo.sh ~/.local/bin/gh-repo`, `install -m 755 .claude/bin/git-credential-gh-repo.sh ~/.local/bin/git-credential-gh-repo` and `install -m 644 .claude/bin/github-repo.sh ~/.local/bin/github-repo.sh`. Install them again, after reading the change, whenever they change.
3. Create the token (Settings, Developer settings, Fine-grained tokens) with the permissions above.
4. `security add-generic-password -s gh-repo-token -a OWNER/REPO -w`, and paste the token at its prompt, never into a file or an editor.
5. `git remote set-url origin https://github.com/OWNER/REPO.git`.
6. `git config --replace-all credential.https://github.com.helper ''` and `git config --add credential.https://github.com.helper "$HOME/.local/bin/git-credential-gh-repo"`. The empty value drops helpers set globally, such as `osxkeychain`.
7. Check: `~/.local/bin/gh-repo pr list` and `git push --dry-run origin HEAD`.

When the token expires, create a new one and replace it with `security add-generic-password -U -s gh-repo-token -a OWNER/REPO -w`.

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
- [pr](../../.claude/skills/pr/SKILL.md): pull requests through `gh-repo`: create, update a stacked branch after a squash merge, checks and merge ([GitHub access](#github-access)).
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
