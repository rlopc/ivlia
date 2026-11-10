# Phase 0 implementation plan

> **Archived on 2026-11-10.** Phase 0 is done: every step's done criteria and the Phase 0 done criteria were verified, and release v0.1.0 is published. This plan is no longer maintained; the current state of the project is in the standards document ([docs/standards/](../standards/README.md)) and the decision map ([docs/decisions/](../decisions/README.md)).

Status: archived. Drafted 2026-11-09. Updated 2026-11-09 with the user's answers to all open questions and with an independent review: its routine fixes and the user's decisions on its findings; then with the routine fixes of a second independent review. The design changes of 2026-11-09 are already applied to `docs/`.

## About this plan

### Purpose

This plan is the step-by-step guide to build Phase 0: the full development environment, with every piece of the architecture in its minimal working version and no real functionality. Scope and done criteria come from [docs/01](../01-vision-y-alcance.md) ("Alcance por fases") and [docs/10](../10-plan-y-pendientes.md) (slice 1). The way of working comes from [docs/09](../09-ia-en-el-desarrollo.md) ("Modo de trabajo de la fase 0").

The plan does not repeat the design. Each step links to the design sections that explain the "why". Items marked "(decision 2026-11-09)" are user decisions taken on that date; they are final and override any "candidate" in the design. Until each step moves them to the standards document or the decision map, this plan is where they are recorded.

### How to read it

- Steps run in order: 1 Repository and `just`, 2 Backend, 3 CLI, 4 Frontend, 5 CI, 6 Release (decision 2026-11-09). A small final PR archives the plan (see "Final PR: archive this plan").
- Each step has: goal, Validar scope, tasks, user-only actions, done criteria, what goes into the standards document, and open questions.
- Tasks are checkboxes: `[ ]` todo, `[x]` done. Each step also has a status line: `todo`, `in progress` or `done`.
- "User only" marks actions that Claude cannot or must not do.
- "(assumed)" marks a routine choice made by this plan. The user can change it at review without further discussion.
- An open question blocks only the tasks that depend on it. Raise it with the user before starting those tasks. Never resolve it silently.
- When a Validar item has several possible outcomes, the plan says what happens with each. Claude tells the user which outcome happened before acting on it.

### How it is maintained and how it ends

- The plan is temporary. In each step's PR, that step's content is rewritten into the standards document: current state, detailed, no history, linking to config files instead of copying their values. The plan only keeps the ticked checklist.
- The standards document is `docs/standards/`, with nine files (decision 2026-11-09):
  - `README.md`: index, plus what is common to all areas: Git and PRs, the documentation rule, the versions policy and the cooldown.
  - `repository.md`: tool versions, `just`, pre-commit, formatting and Markdown checks, repository files, licence, ruleset.
  - `ai-development.md`: Claude Code permissions, hooks and rules; Validar; OpenSpec.
  - `security.md`: the threat model, linking to where each measure lives.
  - `backend.md`: the Python package, including the CLI.
  - `api.md`: the contract and its export, OpenAPI, SSE, token, cookie session, Host and Origin checks.
  - `frontend.md`, `ci.md`, `release.md`.
- Decisions that need it go to `docs/decisions/` (from step 2): `README.md` is the decision map, `adr/` holds the ADRs.
- When Phase 0 ends (see "Phase 0 done criteria"), the final PR marks this plan as archived. After that it is not maintained.

### How to continue if interrupted

1. Find the first step whose status is not `done`, then its first unticked task.
2. Check the local state: current branch, uncommitted changes, and whether that step's PR already exists.
3. Read the step's Validar report: `.dev/validar-step-N.md` before the PR exists, the PR description after (see the cross-cutting rules). If there is none, run the `validar` skill first.
4. Run `just check` (from step 1 on) to see what is broken before continuing.

## Cross-cutting rules

These apply to every step. They come from [docs/08](../08-ingenieria-y-calidad.md) ("Git", "Documentación en tres capas") and [docs/09](../09-ia-en-el-desarrollo.md) ("Modo de trabajo de la fase 0", "Guardarraíles", "Las herramientas de calidad guían a la IA").

1. Validar first. Before any task, Claude runs the `validar` skill (decision 2026-11-09; created in step 1, whose own Validar follows the same procedure by hand, assumed). The skill delegates the reading to the read-only `researcher` agent, which checks current official docs, versions and best practices for the step's tools and compares them with the design, this plan and the repo. It returns a short report: confirmed, changed, risks, and sources with how much of each was read. It needs network access, so the user confirms that first. The user sees the report before work starts. If it contradicts the design or this plan, stop and discuss. Until the PR exists, the report is saved in `.dev/validar-step-N.md` (gitignored, assumed); then its summary goes into the PR description (assumed).
2. One branch and one PR per step. Short-lived branch from `main`, named `<type>/<short-description>` (assumed), for example `chore/repo-setup`. The PR is squashed into `main`.
3. PR title: `<type>(<area>): <summary>`. Types: standard Conventional Commits. Areas: `backend`, `frontend`, `cli`, `docs`, `ci`, `repo`, `deps` (decision 2026-11-09: `deps` is for dependency updates). After the squash, the title is the commit message.
4. `just check` is green before opening the PR (from step 1). CI exists only from step 5; until then Claude runs `just check` locally and pastes the result in the PR.
5. The `reviewer` agent reviews the branch before the user (decision 2026-11-09): after `just check` is green and before the push is requested, `just review-diff` writes the diff against `main` and the list of changed files to `.dev/review/`, and the reviewer reads that file and any repository file it needs. Claude fixes or answers its findings first. The user reviews and merges every PR. Claude never merges and never pushes to `main`.
6. The same PR updates the standards document, and from step 2 the decision map and ADRs when a decision needs them. It also updates `AGENTS.md` "Current state" and ticks this plan's tasks.
7. The user confirms before: any push, any network use, adding or upgrading dependencies, deleting files, and anything that touches secrets. Installing from a lockfile needs no confirmation.
8. Claude does not disable or relax a check to make it pass.
9. Generated files are never edited by hand; they are regenerated with their command.
10. Before using a version, Validar re-confirms it. The versions in this plan were checked on 2026-11-09.

## Step 1: Repository and `just`

Status: done. PR title: `chore(repo): <summary>`.

### 1.1 Goal

Create the git repository, the tool versions, the `just` entry point, the pre-commit checks, the repository files, the Claude Code configuration (with the `validar` skill and the `reviewer` agent), OpenSpec, and the first version of the standards document with the threat model. After this step `just check` runs every repository-level check. Design: [docs/08](../08-ingenieria-y-calidad.md) ("Herramientas por parte", "Necesidades con herramienta provisional", "Git"), [docs/09](../09-ia-en-el-desarrollo.md) ("Instrucciones para la IA", "Guardarraíles"), [docs/06](../06-datos-y-seguridad.md) ("Seguridad"), [docs/01](../01-vision-y-alcance.md) ("Datos del proyecto").

### 1.2 Validar scope

- Host prerequisites: mise, git and gh are installed.
- Versions: just 1.59.0, mise and its settings (`idiomatic_version_file_enable_tools`), Node 26 LTS (v26.13.0), pnpm 12.18.0, uv 0.13.7, lychee 0.24.2, pre-commit 4.7.0, pre-commit-uv 4.4.2, Prettier 3.9, OpenSpec 1.16.1.
- mise pipx backend for pre-commit (decision 2026-11-09): that it installs with uv, and the syntax to add `pre-commit-uv` as an extra package. Supported: pre-commit comes from `mise.toml`. Not supported: `just setup` installs it with `uv tool install`, pinned in the justfile. The user is told the outcome.
- Hook revisions: gitleaks v8.30.1, actionlint v1.7.12, zizmor v1.32.0, shellcheck-py, markdownlint-cli2 0.24.0. `mirrors-prettier` is archived: confirm the `repo: local` Prettier hook pattern.
- The 7-day cooldown in pnpm (`minimumReleaseAge: 10080`), uv (`exclude-newer = "7 days"`) and Dependabot (`cooldown`). [docs/08](../08-ingenieria-y-calidad.md) says this value is confirmed here.
- mise lockfile (`mise.lock`, checksums for tool downloads): stable or experimental in the current mise version. Stable: enable it and commit `mise.lock`. Experimental: do not enable it; revisit when it is stable (decision 2026-11-09).
- Whether mise reads the pnpm version from `packageManager`. Yes: keep pnpm pinned only there. No: pin pnpm in `mise.toml` too and keep `packageManager` in sync (assumed). The user is told the outcome.
- How to run gitleaks on the initial commit before the repository tooling exists: a pinned binary through mise (assumed), and the right subcommand (`gitleaks git` on the commit or `gitleaks dir` on the working tree).
- lychee `--offline --include-fragments` on the existing Spanish docs (accented heading anchors).
- What `openspec init` writes (does it touch `AGENTS.md` or `CLAUDE.md`, which files under `.claude/`), which of its files are generated and which are edited by the user, the command to validate specs, `openspec update` after an upgrade, and whether it has telemetry to turn off.
- Claude Code permission rule syntax for `permissions.allow`, `ask` and `deny`, and their precedence.
- Claude Code sandbox for Bash (decision 2026-11-09): settings syntax, and whether it covers writes only inside the project, network only to allowed domains, and the commands that `just` runs. If it cannot cover part of that, the permission rules stay the only guard for that part, the gap is recorded in `security.md`, and the user is told (assumed).
- Claude Code skill and subagent file format (frontmatter, `model`, `tools`), for the `validar` skill and the `reviewer` agent; and the `paths:` frontmatter of `.claude/rules/*.md`.
- After `just setup`, `just check` writes nothing outside the repository (decision 2026-11-09). If a tool does, add a sandbox write exception for that folder only, record it in `security.md`, and tell the user.
- Whether the markdownlint-cli2 pre-commit hook honours `ignores` from `.markdownlint-cli2.jsonc` when it receives file names; if not, add an `exclude:` to the hook.
- GitHub rulesets: squash-only, linear history, no bypass, 0 approvals; private vulnerability reporting.
- GitHub secret scanning with push protection: free on public repositories, and whether it can be enabled before the first push. Free: the user enables it (1.4). Not free: it is not enabled, gitleaks stays the only scan, and [docs/06](../06-datos-y-seguridad.md) ("Seguridad") is discussed with the user (decision 2026-11-09).
- `prek`: still below 1.0? (decision 2026-11-09: use pre-commit; revisit prek at 1.0).

### 1.3 Tasks

Order of the first tasks (assumed): initial commit, gitleaks scan, the user creates the repository and pushes, the user creates the ruleset and enables secret scanning (before the push if GitHub allows it; 1.4), then the step 1 branch is created and the remaining tasks follow.

- [x] `git init -b main` locally. Add `.dev/` to the existing `.gitignore` first, so the Validar report is never committed (assumed). Initial commit with the existing files: `docs/`, `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.gitignore`, `.markdownlint.jsonc`. The step 1 PR then shows only the new files (decision 2026-11-09).
- [x] Scan the initial commit with gitleaks before the push, with the subcommand found in Validar, for example `mise exec gitleaks@8.30.1 -- gitleaks git --redact` (assumed). It downloads gitleaks: user confirms.
- [x] After the user-only actions of 1.4 up to the ruleset: create the branch `chore/repo-setup` (assumed) from `main`.
- [x] Extend `.gitignore` with: `.venv/`, `node_modules/`, `dist/`, `__pycache__/`, coverage outputs, Playwright reports. Keep `.dev/`, the dev installation folder (decision 2026-11-09), `*.local.*` and `.DS_Store`.
- [x] `mise.toml`: `[tools]` with exact versions of `node`, `uv`, `just`, `lychee` (short names), and pre-commit 4.7.0 with pre-commit-uv 4.4.2 through the pipx backend, which uses uv (decision 2026-11-09; syntax and fallback per Validar); `[settings] idiomatic_version_file_enable_tools = ["pnpm"]`; the lockfile setting per Validar. pnpm is pinned only in `packageManager` (decision 2026-11-09), unless Validar finds that mise does not read it. No corepack (decision 2026-11-09). Python is not in mise: uv reads `.python-version` (step 2).
- [x] Root pnpm workspace (decision 2026-11-09): `package.json` with `"private": true`, `"packageManager": "pnpm@12.18.0"`, `"license": "AGPL-3.0-or-later"`, and Prettier and OpenSpec as exact dev dependencies; `pnpm-workspace.yaml` with `minimumReleaseAge: 10080` (`frontend/` is added to it in step 4); one root `pnpm-lock.yaml` from `pnpm install` (user confirms adding Prettier and OpenSpec).
- [x] `justfile` with, at least (names assumed):
  - `setup`: `mise install` (which also installs pre-commit), `pre-commit install`, `pnpm install --frozen-lockfile`. Fallback if mise cannot add the extra package: `uv tool install pre-commit==4.7.0 --with pre-commit-uv==4.4.2`, pinned in the justfile (decision 2026-11-09).
  - `check`: runs every local check and fails on the first error. In this step: `pre-commit run --all-files`, the `.claude` hook tests, `lychee --offline --include-fragments` on all Markdown, OpenSpec validation.
  - `fix`: runs the formatters and auto-fixes.
  - `review-diff`: writes `git diff main...HEAD` and the list of changed files to `.dev/review/` for the `reviewer` agent (decision 2026-11-09).
- [x] `.pre-commit-config.yaml` with: gitleaks, actionlint, zizmor, shellcheck (shellcheck-py), markdownlint-cli2 with `--fix` (uses the existing `.markdownlint.jsonc`), and Prettier as a `repo: local` hook that runs pnpm's Prettier. Revisions pinned. Set `minimum_pre_commit_version`. Rule (decision 2026-11-09): a tool that has a lockfile runs as a `repo: local` hook with the locked version. So ruff becomes a local hook with `uv run --locked ruff`, added in step 2, when `backend/` and its `uv.lock` exist (assumed).
- [x] Prettier config (`.prettierrc.json`, `.prettierignore`). Prettier excludes Markdown; markdownlint owns Markdown (decision 2026-11-09).
- [x] Generated files are not reformatted (rule 9; assumed): `.prettierignore` lists the lockfiles (`pnpm-lock.yaml`, `uv.lock`, `mise.lock` if any) and OpenSpec's generated files (in `openspec/` and `.claude/`, per Validar); `.markdownlint-cli2.jsonc` `ignores` lists OpenSpec's generated Markdown. Later steps add their own generated files.
- [x] Run `just check` and fix findings. In the existing Spanish docs, fix only formatting and broken links, never content.
- [x] `.claude/hooks/researcher-bash-guard.test.sh`: remove the trailing space on line 2; fix any shellcheck finding; build the test JSON with `python3` instead of `jq` (decision 2026-11-09). Add the test to `just check`.
- [x] `.claude/settings.json`: keep the PreToolUse researcher hook. Add `permissions` per [docs/09](../09-ia-en-el-desarrollo.md) ("Guardarraíles") and the sandbox (decision 2026-11-09):
  - These rules apply the user's rules: no history rewriting, no deletion and no dependency changes without permission. Ask and deny win over allow (precedence per Validar).
  - allow: `just` recipes except `just setup` and `just update-tools`; `uv run --locked`, `uv sync --locked`; `pnpm install --frozen-lockfile`, `pnpm exec`, `pnpm run`; read-only git (`status`, `diff`, `log`, `show`, branch listing); `git add`, `git commit`, `git switch` and branch creation; and only these `gh` commands: `pr view`, `pr diff`, `pr checks`, `run view`, `issue view`. The pinned downloads that `just check` makes (for example pre-commit hook environments) count as installs from a lockfile.
  - ask: `just setup`, `just update-tools`, `pnpm dlx`, `pnpm create`, `pnpm add`, `pnpm remove`, `pnpm update`, `uvx`, `uv add`, `uv remove`, `uv lock --upgrade`, `uv pip`, `uv tool`, `git push`, `git rebase`, `git commit --amend`, `git reset`, `git branch -d` and `-D`, `git clean`, `git rm`, `rm`, network commands (`curl`, `wget`), every other `gh` command, web tools.
  - deny: `git push --force` (also `-f` and `--force-with-lease`), `gh pr merge`, any push to `main`, and reading the use installation folder (`~/Library/Application Support/ivlia`) and secret folders (list assumed, shown to the user).
  - Sandbox for Bash, per Validar: writes only inside the project; network only to allowed domains (list assumed, shown to the user). Installing happens only in `just setup`, which asks and runs outside the sandbox with the user's approval (tools from mise, dependencies from lockfiles, pre-commit environments, Playwright browsers); every other recipe runs inside the sandbox (decision 2026-11-09).
  - The push-to-main deny matches command text and can be bypassed; the ruleset (1.4) is the real guard.
- [x] `.claude/skills/validar/SKILL.md`, in Spanish until `.claude/` is translated (decision 2026-11-09). Input: the step and its tools. Checks: versions, official docs, differences with the design, this plan and the repo. Output: confirmed, changed, risks, and sources with how much of each was read. Saves the report in `.dev/validar-step-N.md`. Delegates the reading to the existing `researcher` agent and invokes it with model Sonnet, because `researcher.md` has no `model:` field and is not modified.
- [x] `.claude/agents/reviewer.md`, in Spanish until `.claude/` is translated (decision 2026-11-09): Opus, read-only tools, no network, clean context. Its tools are Read, Grep and Glob only; it gets the changes from the file written by `just review-diff` (decision 2026-11-09). It reviews each Phase 0 branch before the user, and does Verificar ([docs/09](../09-ia-en-el-desarrollo.md)) from slice 2.
- [x] OpenSpec (decision 2026-11-09): run it with `pnpm exec openspec`. Run `openspec init` for Claude Code. Its output (`openspec/`, its files under `.claude/`) is generated: commit it as is, and after each OpenSpec upgrade regenerate it with `openspec update`. If it edits `AGENTS.md` or `CLAUDE.md`, show the diff to the user before keeping it. Add spec validation to `just check`.
- [x] `LICENSE`: AGPL-3.0-or-later full text (decision 2026-11-09). Getting the official text needs network: user confirms.
- [x] `README.md` (English): what ivlia is, status (Phase 0), license, link to `docs/`, how to set up (`mise trust`, `mise install`, `just setup`, `just check`).
- [x] `SECURITY.md`: report vulnerabilities through GitHub private vulnerability reporting; supported versions: latest release only (assumed).
- [x] `CONTRIBUTING.md`, short: issues welcome, external PRs not accepted for now (decision 2026-11-09).
- [x] `.github/pull_request_template.md`: summary, Validar summary, and a docs checklist: specs updated if behaviour changed, standards document updated if tools or practices changed, ADR if the decision is hard to reverse, decision map updated, obsolete descriptions fixed. Source: [docs/08](../08-ingenieria-y-calidad.md) ("Documentación en tres capas") and [docs/09](../09-ia-en-el-desarrollo.md) ("Documentación").
- [x] `.github/ISSUE_TEMPLATE/`: bug report and feature request as issue forms, plus `config.yml` that points security reports to private reporting.
- [x] No CODEOWNERS, Code of Conduct or DCO until contributions open (decision 2026-11-09).
- [x] Standards document: the files listed in 1.6. `security.md` holds the threat model required by [docs/06](../06-datos-y-seguridad.md) ("Seguridad"): what it protects (user data by level, secrets, the action log), from whom (prompt injection in external content, malicious local web pages and DNS rebinding, compromised dependencies, leaks to logs or the repo), and how (data and instructions separation, approvals, sandbox, local-only API with token and Host/Origin checks, data levels, gitleaks and GitHub secret scanning, cooldowns, pinned actions), each measure linking to where it lives. The index in `README.md` names the files that do not exist yet without linking them, so the link check passes (assumed).
- [x] `AGENTS.md`: replace "Rules for Fase 0" with links to the standards document. Update "Current state" (repository and `just` exist; how to run `just check`; next step: backend). The rewrite keeps the link "Follow `docs/plan/phase-0.md`" until the final archive PR.

### 1.4 User-only actions

- [x] User only: create the public GitHub repository `ivlia` ([docs/01](../01-vision-y-alcance.md), "Datos del proyecto") and add the remote.
- [x] User only: enable secret scanning and push protection, if Validar confirms it is free (decision 2026-11-09). Before the first push if GitHub allows it, otherwise right after.
- [x] User only: push the initial commit to `main` after the gitleaks scan, then create the ruleset right after (decision 2026-11-09).
- [x] User only: repository settings: allow only squash merging; default squash message = PR title ([docs/08](../08-ingenieria-y-calidad.md), "Git").
- [x] User only: ruleset on `main`, no bypass: require PR with 0 approvals, squash only, linear history, block force pushes and deletion. Required status checks are added in step 5 (decision 2026-11-09).
- [x] User only: enable private vulnerability reporting.
- [x] User only: approve the push of the step 1 branch and merge the PR.

### 1.5 Done criteria

- `mise trust`, `mise install` and `just setup` work on a clean clone.
- `just check` exits 0.
- `pre-commit run --all-files` exits 0.
- The `.claude` hook test exits 0 without `jq` installed.
- `pnpm exec openspec` validation exits 0.
- GitHub shows the ruleset active on `main` with the rules listed in 1.4, and secret scanning with push protection on (if enabled per Validar).
- Claude Code asks before `git push`, `git commit --amend`, `just setup`, `pnpm add` and `gh` commands outside the read-only list, and refuses `git push --force`, `gh pr merge` and reading the use installation folder.
- A Bash command that writes outside the project, or reaches a domain outside the allowed list, is blocked by the sandbox (as far as Validar found it covers).
- The `validar` skill and the `reviewer` agent exist, and the reviewer reviewed the step 1 PR before the user.
- `AGENTS.md` no longer contains "Rules for Fase 0".

### 1.6 Standards document in this PR

Creates:

- `README.md`: index; Git and PR rules; the documentation rule; versions policy (links to `mise.toml`, `package.json`, `.pre-commit-config.yaml`) and the 7-day cooldown.
- `repository.md`: tool versions and the mise lockfile outcome, `just` recipes, pre-commit hooks and the rule "a tool with a lockfile runs as a local hook with the locked version", Prettier and markdownlint scope, link checks, repository files, licence, the ruleset.
- `ai-development.md`: Claude Code permissions, sandbox and hooks; the `validar` skill and the `reviewer` agent; OpenSpec usage (from slice 2) and its update. It notes that the push-to-main deny can be bypassed and the ruleset is the real guard.
- `security.md`: the threat model, with the same note on the push-to-main deny and the ruleset.

### 1.7 Open questions

None.

## Step 2: Backend

Status: done. PR title: `feat(backend): <summary>`.

### 2.1 Goal

Create the Python package `ivlia` in `backend/` with its layers and a hello-world flow: an SSE endpoint runs a use case, which runs a minimal LangGraph graph, which calls a hello-world adapter, and emits contract events. Include the three-layer configuration, secrets, the API token, the one-time link and cookie session, Host/Origin checks, the migration runner with the initial migration, structured logs and OpenTelemetry traces, the exported JSON Schema and the OpenAPI 3.2 document, the `ivlia-server` entry point, all quality checks, the PostToolUse hook for Python, the backend rules for Claude Code, the LangGraph ADR and the decision map. Design: [docs/02](../02-arquitectura-e-interfaces.md) ("Principios", "Estructura del repositorio (monorepo)", "Contrato único de la API", "Orquestación", "API"), [docs/07](../07-transversales.md) ("Configuración", "Observabilidad"), [docs/06](../06-datos-y-seguridad.md) ("Política de datos"), [docs/08](../08-ingenieria-y-calidad.md) ("Tipado", "Pruebas", "Entrega", "Documentación en tres capas"), [docs/10](../10-plan-y-pendientes.md) (slice 1).

### 2.2 Validar scope

- Python 3.14 (decision 2026-11-09: confirmed, LangGraph CI tests 3.14). If Validar or later work finds a blocker, fall back to 3.13 and tell the user.
- Versions: ruff 0.17.4, mypy 2.4.1 and the `pydantic.mypy` plugin, pytest 9.2.0, coverage 7.17.2, import-linter 2.16, FastAPI 0.162.2, pydantic 2.14.3, pydantic-settings 2.16.2, keyring 25.7.0, structlog 26.1.0, opentelemetry-sdk 1.45.2, langgraph 1.2.20, openapi-spec-validator (3.2 support), uvicorn, httpx for `TestClient`.
- `[tool.uv] exclude-newer = "7 days"` and `required-version` in uv 0.13.7.
- FastAPI native SSE (`fastapi.sse.EventSourceResponse`), the `itemSchema` it emits, and `openapi_version="3.2.0"`.
- pydantic discriminated union export (JSON Schema 2020-12, `oneOf` + `discriminator.mapping`).
- `PRAGMA user_version` inside a transaction with Python 3.14 `sqlite3` transaction control.
- import-linter: `include_external_packages = true`, layers and forbidden contracts, behaviour with modules that do not exist yet (`application/maintenance` stays empty until slice 2).
- coverage.py: one run, two reports with `--include`/`--omit` and `--fail-under`.
- ruff rule families: a curated list, each family with its reason. The list is shown to the user before it goes into `pyproject.toml` (decision 2026-11-09).
- MADR: the current minimal template, for ADR 0001.
- For step 3 (decision 2026-11-09): Typer 0.28.0, and httpx2 version, licence and SSE API (`EventSource`). Fits: use httpx2. Does not fit: httpx plus an own SSE reader. The user is told the outcome.
- uvicorn reload with an own entry point (`ivlia-server`).
- Whether a cookie with `Secure` on `http://localhost` is kept and sent by Chrome, Firefox and Safari (decision 2026-11-09). All three: add `Secure` to the session cookie. Not all: leave it out and record why in `api.md`. The user is told the outcome.
- Whether uv writes `direct_url.json` (PEP 610) with `dir_info` for the editable install of `backend/`, and `archive_info` for `uv tool install` from a wheel (decision 2026-11-09). Yes: the start guard uses it. No: Claude stops and discusses another detection with the user.
- Claude Code PostToolUse hook input format and how to return errors to Claude.

### 2.3 Tasks

- [x] Create a simple uv project (not a workspace) in `backend/` (decision 2026-11-09), src layout (assumed): `backend/pyproject.toml` (name `ivlia`, `version = "0.0.0"` (assumed), `requires-python = ">=3.14"`, `license = "AGPL-3.0-or-later"`, build backend `uv_build` until step 6 confirms it, assumed), `backend/.python-version` (`3.14`), `[tool.uv]` with `required-version` and `exclude-newer = "7 days"`, `backend/uv.lock`.
- [x] Add only the spike's dependencies; the user confirms first: fastapi; dev group: pytest, openapi-spec-validator (assumed).
- [x] Spike: OpenAPI 3.2 (decision 2026-11-09), before the rest of the step. A minimal FastAPI app with `openapi_version="3.2.0"` and one SSE endpoint. Replace the generated `itemSchema` with the contract union (`oneOf` + `discriminator`). Validate the document with openapi-spec-validator in a pytest test. If it works, the test stays as the OpenAPI test. If not, report to the user and propose the fallback: OpenAPI 3.1 whose SSE response refers to the exported JSON Schema. The user decides.
- [x] Add the rest of the dependencies; the user confirms the list again. Runtime: uvicorn, pydantic, pydantic-settings, keyring, structlog, opentelemetry-api, opentelemetry-sdk, langgraph. Dev group: ruff, mypy, coverage, import-linter, httpx (only for `TestClient`, decision 2026-11-09; Validar changed it to httpx2, with no classic httpx). No pytest-cov (decision 2026-11-09). No langgraph-checkpoint-sqlite yet: checkpoints arrive in slice 2 ([docs/10](../10-plan-y-pendientes.md)).
- [x] Package layout, layer first (decision 2026-11-09), in `backend/src/ivlia/`:
  - `domain/` with `agents`, `memory`, `knowledge`, `models`, `tools`, `data_policy`.
  - `application/` with `orchestration`, `maintenance` and the use cases.
  - `contract/`: the Pydantic event models.
  - `config/`: settings and secret lookup.
  - `adapters/`, `api/`, `cli/` (filled in step 3).
  - `bootstrap.py`: the composition root, the only module that imports adapters.
- [x] Domain: data levels 0-3 as a type ([docs/06](../06-datos-y-seguridad.md)); minimal agent state; only the LLM port, as a typed protocol (decision 2026-11-09). Every other port of the closed list is created in the slice that uses it.
- [x] Contract test base class (decision 2026-11-09): each port has a base test class; each adapter's test subclasses it.
- [x] Hello-world adapter behind the LLM port, with its contract test (decision 2026-11-09).
- [x] Contract: Pydantic event models as a discriminated union on `type`, with only `token`, `end` and `error` (decision 2026-11-09); each slice adds its own. `just contract` exports the JSON Schema to `backend/schemas/events.schema.json` and the OpenAPI document to `backend/schemas/openapi.json`, both outside `src/` and versioned (decision 2026-11-09). Both are generated: add `backend/schemas/` to `.prettierignore` (rule 9; assumed). A test in `just check` (and so in CI) fails if either export differs from its versioned file.
- [x] Orchestration: a minimal LangGraph graph in `application/orchestration` with one node that calls the LLM port. The application translates domain state to LangGraph state ([docs/02](../02-arquitectura-e-interfaces.md), "Orquestación"). No checkpointer yet.
- [x] Use case: the chat use case emits contract events (token, end; error on failure). The endpoint only serializes them.
- [x] Configuration in `ivlia.config` ([docs/07](../07-transversales.md), "Configuración"): defaults in code; user TOML via `TomlConfigSettingsSource`; environment variables. Validate everything at start; on error, do not start and say what fails. Installation identity (decision 2026-11-09):
  - `IVLIA_HOME` is the installation root; default `~/Library/Application Support/ivlia`.
  - `IVLIA_ENV=dev` marks the dev installation; in the repo, `IVLIA_HOME` is `.dev/` (gitignored).
  - `just` always sets both; mise also sets them on entering the repo (`[env]` in `mise.toml`, with `IVLIA_HOME = "{{config_root}}/.dev"` so it is absolute from any subfolder).
  - Start guard (decision 2026-11-09): ivlia detects a run from the repo through PEP 610. If its `direct_url.json` has `dir_info` (installed from a local folder, editable included) and `IVLIA_HOME` is not set, ivlia does not start and says why. Extended (decision 2026-11-10): with `dir_info`, `IVLIA_ENV=dev` is required too. A release install (`archive_info`) starts. Tests with fake distribution metadata (assumed).
- [x] Secrets in `ivlia.config`: order env, then keyring, then a file in `IVLIA_HOME` with mode `0600`; if keyring fails, fall back to the file (decision 2026-11-09). The keyring service name is configurable, default `ivlia` (decision 2026-11-09). The dev installation never uses keyring. The API token is generated at first start and stored this way; the env-first lookup reads it from `IVLIA_API_TOKEN` (assumed).
- [x] API (decision 2026-11-09): FastAPI app factory; routes under `/api` so the SPA can own the rest (assumed); `GET /api/health` (assumed) and `POST /api/chat` with body `{"message": "..."}`, which answers with SSE. Binds to `127.0.0.1` only. Port configurable, default 8765 in use and 8766 in dev. The token goes in `Authorization: Bearer <token>` and is compared with `secrets.compare_digest`. Host and Origin checks ([docs/02](../02-arquitectura-e-interfaces.md), "API"):
  - allowed `Host`: `127.0.0.1:<port>` and `localhost:<port>`;
  - allowed `Origin`: the same two, plus the Vite dev origin only in the dev installation. The dev origin is a setting, default `http://localhost:5173` (assumed), used by the allowlist and its tests. A request without `Origin` (the CLI) is not rejected for it (assumed);
  - missing or wrong token or session: 401; foreign `Host` or `Origin`: 403.
- [x] `/openapi.json` is served in both installations; `/docs` (Swagger UI, loaded from a CDN) only in the dev installation (decision 2026-11-09).
- [x] Web session ([docs/02](../02-arquitectura-e-interfaces.md), "API"; here because `ivlia web` in step 3 needs it, assumed; values decision 2026-11-09): an endpoint authenticated by token mints a one-time link (256 random bits, valid 60 s, single use); another exchanges it for the session cookie `ivlia_session` (`ivlia_session_dev` in the dev installation, decision 2026-11-10; `HttpOnly`, `SameSite=Strict`, `Path=/`, plus `Secure` per Validar) and redirects to the SPA root. The session lives 7 days, kept in server memory, so a restart ends it. One auth dependency accepts the token header or the cookie. Tests, with a fake clock (assumed):
  - 401: missing token, wrong token, missing or unknown cookie, session older than 7 days;
  - 403: wrong `Host`, wrong `Origin`, the Vite origin in the use installation;
  - the Vite origin is accepted in the dev installation;
  - link reuse fails; link used after 60 s fails; a valid cookie works;
  - the default port is 8765 in use and 8766 in dev.
- [x] Migrations (decision 2026-11-09): own runner; numbered SQL files per database; `PRAGMA user_version`; one transaction per migration; forward only. Phase 0 has only the memory database, with `0001` creating an `installation` table (id, creation date, version that created it). No knowledge database, no reindex and no checkpoints in Phase 0. Guard, since backup arrives in slice 2: pending migrations on an existing database, with no backup available, mean ivlia does not start and says why. Tests: empty database, already migrated, failing migration rolls back and startup fails with a clear message, existing database plus a fake `0002` refuses to start.
- [x] Logs (decision 2026-11-09): structlog, JSON to a file in `IVLIA_HOME`, with `trace_id` and `span_id` from the current span, and a processor that removes message content unless the explicit local debug mode is on. Level 3 data is never logged ([docs/07](../07-transversales.md), "Observabilidad"). Test that content does not reach the log file.
- [x] Traces (decision 2026-11-09): OpenTelemetry `TracerProvider` that always exports to a rotating JSON Lines file in `IVLIA_HOME` (rotation through `logging`); console export optional by configuration; no external exporter. One span per request and per use case.
- [x] `ivlia-server` entry point (decision 2026-11-09): `[project.scripts] ivlia-server = ...` runs uvicorn on the app built by `bootstrap.py`. launchd will use it later.
- [x] Quality config in `backend/pyproject.toml`:
  - ruff format and lint with the curated families confirmed in Validar (decision 2026-11-09).
  - mypy strict with `plugins = ["pydantic.mypy"]`. Type exceptions only in adapters and `application/orchestration`, as narrow as possible, each with a comment ([docs/08](../08-ingenieria-y-calidad.md), "Tipado").
  - import-linter with `include_external_packages = true` (decision 2026-11-09): layers `api | cli | adapters` → `application` → `contract` → `domain`; domain imports no framework; `config` imports no `api`, `adapters` or `application`; only `bootstrap` imports `adapters`; `langgraph` and `langsmith` only in `application/orchestration` (`langsmith`: decision 2026-11-10); `ivlia.cli` imports only `contract`, `config` and `application/maintenance` (decision 2026-11-09; enforced from step 3).
  - pytest config; coverage.py: one run, two reports: domain `--fail-under=100`, the rest `--fail-under=95` (decision 2026-11-09).
- [x] `justfile`: add `uv sync --locked` in `backend/` to `setup`. Add the backend checks to `check` (ruff, mypy, `lint-imports`, tests with coverage, contract export check), all through `uv run --locked`, so neither `just check` nor CI ever rewrites `uv.lock`. Add `just dev`: `ivlia-server` with reload (decision 2026-11-09).
- [x] `.pre-commit-config.yaml`: add ruff-check and ruff-format as `repo: local` hooks that run `uv run --locked ruff` in `backend/` (decision 2026-11-09; placed in this step, assumed).
- [x] PostToolUse hook ([docs/09](../09-ia-en-el-desarrollo.md), "Las herramientas de calidad guían a la IA"): a stdlib Python script in `.claude/hooks/` registered in `.claude/settings.json` for file edits. For `backend/**/*.py` it runs `ruff format` and `ruff check --fix` on that file and returns remaining errors to Claude. A test for it runs in `just check`.
- [x] `.claude/rules/backend.md` with `paths: backend/**`: only links to the standards document ([docs/09](../09-ia-en-el-desarrollo.md), "Instrucciones para la IA").
- [x] ADR `docs/decisions/adr/0001-langgraph-orchestration.md` (name assumed), MADR minimal (decision 2026-11-09): LangGraph as the orchestration framework, in the application layer, with no adapter copying its API ([docs/02](../02-arquitectura-e-interfaces.md), "Orquestación"). ADRs are immutable; a later one marks the old one "superseded by".
- [x] Decision map `docs/decisions/README.md` (decision 2026-11-09): columns decision, status (Final or Provisional), revisit when, link. Start it with the decisions of Phase 0 so far (for example: mypy vs ty, OpenAPI 3.2 vs fallback, httpx2, prek at 1.0, mise lockfile, Zod postponed).
- [x] Update the standards document and `AGENTS.md` "Current state".

### 2.4 User-only actions

- [x] User only: confirm the spike's dependencies before `uv add` (done), and then the rest of the list.
- [x] User only: confirm the ruff family list.
- [x] User only: decide keep or fallback after the OpenAPI 3.2 spike: keep OpenAPI 3.2 (decision 2026-11-10). FastAPI puts the typed union in `itemSchema` by itself; a test checks that the union's `$ref`s resolve, because openapi-spec-validator does not follow them inside `contentSchema`.
- [x] User only: approve the push and merge the PR.

### 2.5 Done criteria

- `just check` exits 0, including mypy strict, `lint-imports`, domain coverage 100 % and the rest 95 %.
- The OpenAPI test validates the generated document as 3.2 (or 3.1 if the fallback was chosen) and the SSE response lists the contract union.
- The contract export test passes for `events.schema.json` and `openapi.json`, and fails after a manual change to a model or a route without re-export.
- With `just dev` running on port 8766, an authenticated `POST /api/chat` streams the hello-world events and ends with the end event; a request without token gets 401; a request with a foreign `Host` or `Origin` gets 403; a reused or expired one-time link is rejected.
- `/docs` answers only in the dev installation; `/openapi.json` answers in both.
- Starting with an invalid TOML value fails with a message that names the value.
- Starting from the repo without `IVLIA_HOME` fails with a clear message.
- The log file has JSON lines with `trace_id` and no message content; the trace file has JSON lines.
- Editing a Python file triggers the PostToolUse hook.
- `docs/decisions/` contains ADR 0001 and the decision map.

### 2.6 Standards document in this PR

- Creates `backend.md`: layout and layers, import rules, typing rules, testing and coverage, contract tests, configuration and secrets, installation identity, migrations, logs and traces, `ivlia-server` and `just dev`.
- Creates `api.md`: contract and tolerant reader rule, contract and OpenAPI export, `/docs` and `/openapi.json`, SSE, ports, token, one-time link and cookie session (and the `Secure` outcome), Host and Origin checks, status codes. It records why requests without `Origin` (the CLI) are accepted: the token header and `SameSite=Strict` cover CSRF, and the Host check covers DNS rebinding.
- Extends `README.md` (ADR and decision map process), `ai-development.md` (PostToolUse hook, `.claude/rules/`) and `security.md` (links to the API, secrets and logs measures).

### 2.7 Open questions

None.

## Step 3: CLI

Status: done. PR title: `feat(cli): <summary>`.

### 3.1 Goal

Fill the `ivlia.cli` subpackage with `ivlia ask` and `ivlia web`, both through the API, using the Pydantic contract models and an HTTP/SSE client behind an own function. Design: [docs/02](../02-arquitectura-e-interfaces.md) ("CLI", "API", "Contrato único de la API").

### 3.2 Validar scope

- Re-check the step 2 findings on Typer 0.28.0 and httpx2 (version, SSE `EventSource` API, test transport). Fits: httpx2. Does not fit: httpx plus an own SSE reader (decision 2026-11-09). The user is told the outcome.
- Typer testing (`CliRunner`) and console script entry points with uv.
- Opening the browser from Python (`webbrowser`) and how to replace it in tests.

### 3.3 Tasks

- [x] Add Typer and httpx2 (or the fallback); the user confirms. httpx stays dev only (decision 2026-11-09).
- [x] `[project.scripts] ivlia = ...` in `backend/pyproject.toml`.
- [x] The CLI reads the API address and the token through `ivlia.config` (decision 2026-11-09).
- [x] An own client function that opens the SSE stream and yields contract events parsed with the Pydantic models. Only it imports httpx2. Unknown event types are ignored and logged (tolerant reader, decision 2026-11-09).
- [x] `ivlia ask "..."`: streams the answer to stdout; on an error event or connection failure, prints a clear message to stderr and exits non-zero.
- [x] `ivlia web`: asks the API for a one-time link (step 2) and opens the browser on it. Until step 4 the SPA root has no page (assumed).
- [x] import-linter: activate the rule that limits `ivlia.cli` to `contract`, `config` and `application/maintenance` (decision 2026-11-09).
- [x] Tests: CLI commands with `CliRunner` and a fake transport; unknown event type ignored; `ivlia web` with a fake browser opener, and the link it opens is accepted once by the API; one integration test against the real app; coverage thresholds as in step 2.
- [x] Update the standards document and `AGENTS.md` "Current state".

### 3.4 User-only actions

- [x] User only: confirm the dependencies, approve the push and merge the PR.

### 3.5 Done criteria

- `just check` exits 0.
- With `just dev` running, `uv run ivlia ask "hello"` prints the hello-world answer.
- With the server stopped, `ivlia ask` exits non-zero with a clear message.
- `ivlia web` opens the browser on a valid one-time link, and the browser gets the session cookie.
- `lint-imports` fails if `ivlia.cli` imports a module outside `contract`, `config` and `application/maintenance`.

### 3.6 Standards document in this PR

Extends `backend.md`: CLI structure, client function, tolerant reader, error and exit-code rules, CLI import rule, CLI tests.

### 3.7 Open questions

None.

## Step 4: Frontend

Status: done. PR title: `feat(frontend): <summary>`.

### 4.1 Goal

Create the SPA in `frontend/` with one chat page that streams the hello-world answer from the API, the generated contract types and validator, FastAPI serving the built SPA, all frontend checks, the PostToolUse hook for frontend files and the frontend rules for Claude Code. For manual use, `ivlia web` opens it. Design: [docs/02](../02-arquitectura-e-interfaces.md) ("Web", "API", "Contrato único de la API", "Principios"), [docs/08](../08-ingenieria-y-calidad.md) ("Herramientas por parte", "Pruebas").

### 4.2 Validar scope

- Versions: Node 26 LTS, pnpm 12.18.0, Vite 8.3, React 19.3, TypeScript 6.0 (typescript-eslint 8.72 supports below 6.1), Tailwind 4.3 with `@tailwindcss/vite`, shadcn CLI 4, @assistant-ui/react 0.15 (ExternalStoreRuntime), TanStack Query 5, React Router 8 (declarative mode), ESLint 10 flat config, typescript-eslint `strictTypeChecked`, eslint-plugin-react-hooks 7, eslint-plugin-boundaries 7, knip 6, Vitest 5.1 with coverage-v8 per-glob thresholds, React Testing Library 16, MSW 3, Playwright 1.65, @axe-core/playwright 4.14, json-schema-to-typescript 16, Ajv 8.20, eventsource-parser 4.
- Ajv: `ajv/dist/2020`, standalone code generation, and `discriminator: true` without `mapping` support.
- MSW 3 SSE in Node: the `sse` handler is browser-only; use an `http` handler returning a `ReadableStream`.
- eslint-plugin-boundaries: how to express the rules in 4.3, including the rule on who imports assistant-ui.
- Risk (decision 2026-11-09): Dependabot may not raise security alerts when `pnpm-lock.yaml` has two YAML documents (pnpm 12). Find out whether it applies and what to do.
- Cookie flow through the Vite proxy in dev: which origin `ivlia web` must open so the cookie reaches the SPA, and how Host and Origin checks treat proxied requests.
- The `Host` header behind the Vite proxy: with `changeOrigin: false` it is `localhost:5173`, which the Host allowlist rejects. Choose `changeOrigin: true` or adding the dev Host to the allowlist in the dev installation. The user is told the outcome.

### 4.3 Tasks

- [x] Scaffold `frontend/` (Vite, React, TypeScript strict) with `pnpm create vite@<exact version>`; it uses the network and adds dependencies, so the user confirms first. It is a package of the root pnpm workspace (add it to `pnpm-workspace.yaml`), with `"version": "0.0.0"` (assumed) and `"license": "AGPL-3.0-or-later"`.
- [x] Add only the spike's dependencies; the user confirms first: json-schema-to-typescript, Ajv (assumed).
- [x] Spike (decision 2026-11-09), before the rest of the step: from `backend/schemas/events.schema.json`, generate TS types with json-schema-to-typescript and a standalone Ajv validator with `ajv/dist/2020`, after removing `discriminator.mapping`. Prove that (1) the standalone validator accepts valid events and rejects invalid ones, and (2) TypeScript narrows the union by `type` in a `switch`. Report to the user before continuing.
- [x] Add the rest of the dependencies; the user confirms the list again. It includes Tailwind with `@tailwindcss/vite`, then `pnpm dlx shadcn@<exact version> init`, which uses the network and adds dependencies. `@assistant-ui/react` pinned to an exact version (decision 2026-11-09). No Zod in Phase 0 (decision 2026-11-09): it arrives with the first form, and then it is reviewed whether it is still needed next to Ajv.
- [x] Layout by feature (decision 2026-11-09), in `frontend/src/`:
  - `contract/`: generated types and validator.
  - `api/`: the only code that uses the network.
  - `shared/`: code used by more than one feature.
  - `features/chat/`: components, hooks, the assistant-ui adapter, and `model/` (pure logic).
  - `components/ui/`: shadcn components.
  - `app/`: entry, routes and providers.
  - An entities layer (as in Feature-Sliced Design) only if it appears.
- [x] Tailwind 4 with `@tailwindcss/vite`; shadcn components in `src/components/ui`. That folder is excluded from coverage and strict lint, but not from `tsc` and Prettier; a component that is modified moves out of `ui/` (decision 2026-11-09).
- [x] Contract generation (decision 2026-11-09): a `pnpm` script, which `just contract` runs after the JSON Schema export of step 2 (assumed), removes `discriminator.mapping` from a copy of the versioned JSON Schema and generates the types and the Ajv validator into `src/contract/`. Both outputs are versioned and marked as generated, and excluded from coverage, Prettier and ESLint, so the check is stable (assumed). A check mode regenerates into a temporary folder and fails on any difference; it runs in `just check`. Zod is not used for the contract.
- [x] SSE client in `src/api/`: `fetch` plus eventsource-parser; each event is validated with the Ajv validator and typed with the generated types. Unknown event types are ignored and logged (tolerant reader, decision 2026-11-09).
- [x] Chat UI: assistant-ui with ExternalStoreRuntime behind an own adapter module in `features/chat`, so it can be replaced (decision 2026-11-09). The assistant-ui spike for citations, approvals and delegation happens before slice 6, not here; the fallback is an own chat built with shadcn.
- [x] Routing and data: React Router in SPA declarative mode with the chat route and a not-found route; TanStack Query for the health status.
- [x] Dev origin: confirm the default of the step 2 dev origin setting (`http://localhost:5173`) or change it to the one found in Validar; apply the Validar choice for the proxied `Host`; `ivlia web` opens that origin. Backend tests for both installations.
- [x] Same origin (decision 2026-11-09): FastAPI serves the built SPA from the package and returns `index.html` for non-`/api` paths. In dev, Vite proxies `/api` to the API. The build output goes to `backend/src/ivlia/api/static/`, gitignored (assumed). When it is missing (dev with Vite, backend tests), FastAPI does not serve the SPA and the API still works (assumed).
- [x] Lint and format: ESLint flat config with `strictTypeChecked`, react-hooks and eslint-plugin-boundaries (decision 2026-11-09):
  - features do not import each other; common code goes to `shared/`;
  - `shared/` does not import features;
  - `api/` imports only `contract/`;
  - nothing imports `app/`;
  - `model/` imports neither React nor `api/`;
  - only the chat adapter imports assistant-ui.

  Also Prettier, knip, `tsc --noEmit`.
- [x] Tests: Vitest with React Testing Library and MSW (Node: `http` handler that returns a `ReadableStream` for SSE). Coverage-v8 thresholds per glob: 100 % on `features/*/model/`, 95 % on the rest (decision 2026-11-09); `src/components/ui` excluded.
- [x] End-to-end: Playwright with axe against FastAPI serving the built SPA (assumed, closest to production). The Playwright config generates a random token per run, passes it to the server started by `webServer` in `IVLIA_API_TOKEN`, which the env-first secret lookup reads first (step 2), and passes the same value to the tests (assumed). The test asks the API for a one-time link with that token (decision 2026-11-09), opens it, sends a message, sees the hello-world answer, and finds no axe violations. `just setup` installs the Playwright browser (network: user confirms the first time).
- [x] `justfile`: add the frontend checks to `check` (Prettier, ESLint, knip, `tsc`, contract generation check, Vitest with coverage, build, Playwright). Add `just dev-web`: `ivlia-server` and Vite together for development (name assumed).
- [x] PostToolUse hook: extend it for `frontend/**` (Prettier and ESLint with `--fix` on the edited file), with tests.
- [x] `.claude/rules/frontend.md` with `paths: frontend/**`: only links to the standards document.
- [x] Record the outcome of the Dependabot and `pnpm-lock.yaml` risk in the decision map. Outcome (user decision 2026-11-10): pnpm is pinned in `mise.toml` instead of `packageManager`, so the lockfile is one YAML document; `pnpm audit` runs in CI as a second layer (step 5).
- [x] Update the standards document and `AGENTS.md` "Current state".

### 4.4 User-only actions

- [x] User only: confirm the Vite scaffold, the spike's dependencies, and then the rest of the list (including `shadcn init`).
- [x] User only: after the merge, check that Insights > Dependency graph lists the JavaScript dependencies (decision 2026-11-10).
- [x] User only: approve the push and merge the PR.

### 4.5 Done criteria

- `just check` exits 0, including the contract generation check, ESLint with the boundaries rules, knip, `tsc`, Vitest thresholds and Playwright with axe.
- Changing the JSON Schema without regenerating makes `just check` fail.
- In development, `ivlia web` opens the chat, and sending a message shows the hello-world answer streamed from the API.
- The same works with the built SPA served by FastAPI.
- The Vite dev origin is accepted only in the dev installation.
- Editing a frontend file triggers the PostToolUse hook.

### 4.6 Standards document in this PR

- Creates `frontend.md`: layout and boundaries, lint and type rules, `ui/` exceptions, SSE client, chat adapter, testing and coverage, end-to-end and accessibility.
- Extends `api.md` (generated TS types and Ajv validation, same-origin serving, dev origin), `ai-development.md` (PostToolUse hook for frontend files, `.claude/rules/frontend.md`) and `security.md` (dev origin).

### 4.7 Open questions

None.

## Step 5: CI

Status: done. PR title: `ci(ci): <summary>`.

### 5.1 Goal

Run `just check` in GitHub Actions on every PR and on `main`, plus the CI-only checks: CodeQL, OpenSSF Scorecard, Dependabot, the PR title check and the weekly external link check. Then make them required in the ruleset. Design: [docs/08](../08-ingenieria-y-calidad.md) ("Herramientas por parte", "Git"), [docs/06](../06-datos-y-seguridad.md) ("Seguridad"), [docs/09](../09-ia-en-el-desarrollo.md) ("Guardarraíles": CI is the final arbiter).

### 5.2 Validar scope

- jdx/mise-action v5.2.7; actions/checkout; caching for uv, pnpm, pre-commit and Playwright.
- CodeQL advanced setup with languages `python`, `javascript-typescript`, `actions`.
- ossf/scorecard-action (current version, `publish_results`, permissions).
- amannn/action-semantic-pull-request v6 (types, scopes, `requireScope`).
- lychee-action v2.9.0 and how to open or update one issue.
- Dependabot: ecosystems `uv`, `npm` (for pnpm), `github-actions`; `cooldown: default-days: 7`; whether `commit-message.prefix: "build(deps)"` produces titles like `build(deps): bump …` that pass the title check. Yes: use it in every ecosystem (decision 2026-11-09). No: use the documented way to get that title (for example prefix `build` with `include: scope`, if it yields `(deps)`). The user is told the outcome.
- Dependabot support for the `pre-commit` ecosystem and for `mise.toml`, with `cooldown` (decision 2026-11-09). Supported: add those ecosystems with `cooldown: default-days: 7`. Not supported: `just update-tools` (runs `pre-commit autoupdate` and updates the versions in `mise.toml`) and a monthly workflow that opens an issue to run it; the user checks the 7-day age by hand before merging. The user is told the outcome, per ecosystem.
- zizmor findings on the new workflows; SHA pinning with version comments.

### 5.3 Tasks

- [x] All workflows: actions pinned by full SHA with a version comment; top-level `permissions: {}` or `contents: read`, widened per job only where needed; `persist-credentials: false` on checkout (decision 2026-11-09).
- [x] `.github/workflows/ci.yml`: on `pull_request` and `push` to `main`; mise-action; `just setup`; `just check`. One job name that the ruleset can require.
- [x] `.github/workflows/codeql.yml`: CodeQL advanced, languages `python`, `javascript-typescript`, `actions` (decision 2026-11-09).
- [x] `.github/workflows/scorecard.yml`: OpenSSF Scorecard on `main` and weekly.
- [x] `.github/workflows/pr-title.yml`: amannn/action-semantic-pull-request v6; standard Conventional Commits types; scopes `backend`, `frontend`, `cli`, `docs`, `ci`, `repo`, `deps`; scope required.
- [x] `.github/workflows/links.yml`: weekly and manual; lychee-action on all Markdown with network; on failure, open an issue or update the open one (with `gh`, assumed) (decision 2026-11-09). Internal links and anchors keep blocking in `just check`.
- [x] `.github/dependabot.yml`: `uv` (directory `/backend`), `npm` (root workspace), `github-actions` (`/`); `cooldown: default-days: 7`; no wildcard groups (decision 2026-11-09); commit message `build(deps)` per Validar (decision 2026-11-09). Also `pre-commit` and mise if Validar found them supported (decision 2026-11-09).
- [x] For each of pre-commit and mise that Dependabot does not support (decision 2026-11-09): `just update-tools` and `.github/workflows/tool-updates.yml` (name assumed), monthly, which opens an issue or updates the open one. Outcome (Validar 2026-11-10): pre-commit is supported and is a Dependabot ecosystem; mise is not. `just update-tools` runs `mise upgrade --bump`, and mise's own `minimum_release_age = "7d"` keeps the cooldown, so no hand check of the age is needed.
- [x] `pnpm audit` in `ci.yml` (decision 2026-11-10): a second layer next to Dependabot alerts for JavaScript.
- [x] `just check` passes zizmor and actionlint on the new workflows.
- [x] Update the standards document and `AGENTS.md` "Current state".

### 5.4 User-only actions

- [x] User only: make sure CodeQL default setup is off (advanced setup replaces it).
- [x] User only: enable Dependabot alerts and Dependabot security updates ([docs/06](../06-datos-y-seguridad.md), "Seguridad").
- [x] User only: after the first green run, add the required status checks to the `main` ruleset: CI (`just check`), PR title, CodeQL.
- [x] User only: approve the push and merge the PR.

### 5.5 Done criteria

- On the step 5 PR, CI, CodeQL and PR title checks run and are green.
- A test PR with a title outside the format fails the title check.
- The links workflow runs from manual dispatch and, with a broken external link, opens an issue.
- Scorecard publishes a result for the repository.
- Dependabot lists its ecosystems (three, plus pre-commit and mise if supported) in the repository's dependency graph settings; for an unsupported one, the tool-updates workflow runs from manual dispatch and opens an issue.
- The ruleset requires the checks: a PR with a red check cannot be merged.

### 5.6 Standards document in this PR

- Creates `ci.md`: CI workflows and what each checks, workflow security rules, CI-only checks, Dependabot policy, required checks.
- Extends `README.md` (PR title check), `repository.md` (required checks in the ruleset; how pre-commit hooks and mise tools are updated) and `security.md` (CodeQL, Scorecard, Dependabot, pinned actions).

### 5.7 Open questions

None.

## Step 6: Release

Status: done. PR title: `ci(repo): <summary>`.

### 6.1 Goal

Automate one SemVer version for the whole repository and its CHANGELOG with release-please, and publish each release on GitHub with a wheel that contains the built SPA, its provenance attestation and the Sigstore bundle. The use installation installs a tagged wheel with `uv tool install`. Design: [docs/08](../08-ingenieria-y-calidad.md) ("Entrega").

### 6.2 Validar scope

- googleapis/release-please-action v5: manifest config, `bump-minor-pre-major`, `extra-files` for TOML (`backend/pyproject.toml`) and JSON (`frontend/package.json`), `pull-request-title-pattern`.
- actions/create-github-app-token (current version, inputs).
- actions/attest-build-provenance (or its current successor) and how to export the bundle as `*.sigstore.json` for Scorecard Signed-Releases.
- Build backend (decision 2026-11-09): whether `uv_build` can include the built SPA, which is gitignored, in the wheel. Yes: keep `uv_build`. No: switch to hatchling and include the SPA with `artifacts`. The user is told the outcome.
- How `backend/uv.lock` follows the version bump that release-please makes in `backend/pyproject.toml` without hand-editing a generated file (rule 9). Possible outcomes: a job on the release PR runs `uv lock` and commits with the App token, or a dynamic version from the tag (needs hatchling). The user is told and decides.
- The first version release-please computes from `0.0.0` with `feat` commits and `bump-minor-pre-major` (expected `0.1.0`).
- `uv tool install` from a wheel file or URL; `gh attestation verify`.
- Risk (found in step 4): the built SPA lives in `backend/src/ivlia/api/static/`, which is gitignored; check that the build backend still puts it in the wheel (many exclude git-ignored files) and how the release builds it first.

### 6.3 Tasks

- [x] `release-please-config.json` and `.release-please-manifest.json` (starting at `0.0.0`, assumed): one package for the repository; default changelog sections; `bump-minor-pre-major: true`; `extra-files` for `backend/pyproject.toml` and `frontend/package.json` (decision 2026-11-09). Release PR title pattern that passes the title check, for example `chore(repo): release ${version}` (the default `chore(main)` would fail it).
- [x] Build backend per Validar (decision 2026-11-09). Outcome (Validar 2026-11-10): `uv_build` packs the gitignored SPA (checked by building the wheel), so it stays.
- [x] `uv.lock` update on version bumps, per Validar and the user's decision. Outcome (user decision 2026-11-10): a job in `release.yml` regenerates on the release PR branch, with the App token, the generated files that carry the version: `uv.lock` and, found on the first release PR, `openapi.json`.
- [x] `.github/workflows/release.yml`: on push to `main`, get a token from the GitHub App with actions/create-github-app-token and run release-please (decision 2026-11-09).
- [x] When a release is created, a job with minimal permissions: build the SPA, put it into the Python package, `uv build --wheel`, create the provenance attestation, attach the wheel and the `.sigstore.json` bundle to the release (decision 2026-11-09). No public registry. The attestation uses `actions/attest` (Validar 2026-11-10).
- [x] `CHANGELOG.md` is generated by release-please and repeats section headings (MD024): add it to the markdownlint `ignores` and to `.prettierignore` (rule 9; assumed).
- [x] README: install with `uv tool install <wheel>` from a tagged release; verify with `gh attestation verify`.
- [x] Update the standards document and `AGENTS.md` "Current state".

### 6.4 User-only actions

- [x] User only: create the GitHub App with the minimum permissions release-please needs (contents and pull requests, read and write), install it on the repository, and store its ID as a variable and its private key as a secret.
- [x] User only: approve the push and merge the PR; then merge the first release PR.

### 6.5 Done criteria

- After the step 6 PR merges, release-please opens a release PR whose title passes the title check, and CI runs on it.
- After the release PR merges, a GitHub release exists with the wheel and a `.sigstore.json` asset.
- `gh attestation verify <wheel> --repo <owner>/ivlia` succeeds.
- `uv tool install <wheel>` in a clean environment works, `ivlia --help` runs, and `ivlia-server` serves the SPA. The test runs with `UV_TOOL_DIR` and `UV_TOOL_BIN_DIR` set to a temporary folder inside `.dev/`, so nothing is written to `~/.local` (assumed), with `IVLIA_HOME` set to a temporary directory and `IVLIA_ENV=dev` (or a test keyring service name), so it never creates a real use installation or writes to the system keychain (assumed). A real use installation is "User only" and outside Phase 0.
- The versions in `backend/pyproject.toml` and `frontend/package.json` match the release tag.

### 6.6 Standards document in this PR

- Creates `release.md`: versioning and CHANGELOG, release workflow and its credential, build backend, release assets and provenance, how to install and verify a release.
- Extends `security.md` (provenance and the GitHub App credential).

### 6.7 Open questions

None.

## Phase 0 done criteria

From [docs/10](../10-plan-y-pendientes.md), slice 1:

- `just check` passes in CI with all checks active.
- `ivlia ask` and the web chat return a hello-world answer through the API.

Phase 0 does not include what the design or the decisions of 2026-11-09 postpone: retrieval evaluation and `just eval` (slice 3), the knowledge database and `ivlia reindex` (slice 3), checkpoints and backup (slice 2), ports other than the LLM one and event types other than token, end and error (each in the slice that uses it), Zod (first form), mutmut and Stryker, ty, the assistant-ui spike (before slice 6), launchd.

## Final PR: archive this plan

Status: done. PR title: `docs(docs): archive phase 0 plan`. Only after the step 6 done criteria (release PR, release assets, attestation, install) and the Phase 0 done criteria are verified.

- [x] Mark this plan as archived: status line and a note at the top.
- [x] Update `AGENTS.md` "Current state": Phase 0 done; next: slice 2; remove the link to this plan.
- [x] User only: approve the push and merge the PR.

## Sources

- Design: `docs/00` to `docs/10`, read in full on 2026-11-09; after that day's design changes, the changed sections of docs/02, 06, 07, 08, 09 and 10 were re-read in part.
- User decisions of 2026-11-09, recorded in this plan as "(decision 2026-11-09)".
- Tool versions and behaviours named in this plan were checked on 2026-11-09, during planning, against official registries and documentation (PyPI, npm, GitHub releases and the projects' docs). This plan did not re-read them. Each step's Validar re-confirms them before use and records the sources it read in the standards document.
