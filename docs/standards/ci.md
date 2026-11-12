# CI

GitHub Actions in [.github/workflows/](../../.github/workflows/) and Dependabot in [.github/dependabot.yml](../../.github/dependabot.yml). CI runs the same checks as the developer's Mac (`just check`) and adds the ones that only make sense on GitHub. It is the final arbiter ([docs/09](../09-ia-en-el-desarrollo.md), "Guardarraíles").

## Workflows

| Workflow | When | What |
| --- | --- | --- |
| `ci.yml` (job `just check`) | pull requests to any base branch (so stacked ones are checked early), pushes to `main` | `mise install --locked`, `just setup`, Playwright's system packages, `just check`, `pnpm audit --audit-level high` |
| `codeql.yml` (jobs `analyze (…)`) | pull requests to `main`, pushes to `main`, weekly | CodeQL advanced setup for `actions`, `javascript-typescript` and `python`, `build-mode: none` |
| `scorecard.yml` | pushes to `main`, weekly | OpenSSF Scorecard, published, with SARIF to code scanning |
| `pr-title.yml` (job `PR title`) | pull request opened, edited, synchronized or reopened | the title follows Conventional Commits with a required scope ([README](README.md#git)) |
| `links.yml` | weekly, manual | external links with `just check-links` (lychee from `mise.lock`, not lychee-action); on failure, opens the "Broken external links" issue or comments on the open one |
| `release.yml` | pushes to `main` | release-please, `uv lock` on the release PR, and the release assets ([release.md](release.md)) |
| `tool-updates.yml` | monthly, manual | opens the "Update the tools in mise.toml" issue or comments on the open one |

Required status checks on `main` ([repository.md](repository.md#github)), added by the user after the first green run: `just check`, `PR title` and the three CodeQL `analyze` jobs.

## Rules for every workflow

zizmor and actionlint check them in pre-commit, so in `just check` too.

- Actions pinned by full commit SHA, with the version in a comment. Dependabot updates both.
- `permissions: {}` at the top; each job gets only what it needs.
- `actions/checkout` with `persist-credentials: false`.
- Values from GitHub contexts reach scripts through `env:`, never as `${{ }}` inside `run:`.
- `run` steps write outputs to `GITHUB_OUTPUT`, never to `GITHUB_ENV` or `GITHUB_PATH`. (mise-action itself adds mise to `GITHUB_PATH` and exports the `[env]` of `mise.toml`.)
- No `pull_request_target`: there are no fork pull requests, and `pull_request` needs no write token.
- Issues are opened with `gh` and `issues: write`, not with third-party actions.
- Each job has a `timeout-minutes`.
- Each job runs on a fixed Ubuntu label (`ubuntu-24.04`), not `ubuntu-latest`, which GitHub moves to each new image over several weeks; runner-images suggests a fixed label "to avoid unwanted migration". Each newer GA image comes in its own pull request ([decision map](../decisions/README.md)).
- A stacked pull request retargeted to `main` gets no new run on its own (the base change is an `edited` event): merge `main` into its branch and push, so every required check runs against `main`.

## The CI job

- mise-action installs mise only (`install: false`), the same version as on the Mac, verified against its signed checksums; a `mise install --locked` step installs the tools, with the job's read-only token to avoid GitHub API rate limits.
- Checkout with `fetch-depth: 0`, because gitleaks scans the whole history.
- Two caches: mise-action's own, of the installed tools (on by default, renewed every 30 days), and one `actions/cache` for the pnpm store and the uv cache, keyed on `pnpm-lock.yaml` and `uv.lock`. `links.yml` turns mise-action's cache off, so its two tools never fill the cache that `ci.yml` restores. `uv cache prune --ci` keeps the uv part small. Playwright's browser is not cached, as Playwright advises; its system packages are installed on each run.
- No cache in the release workflow: a poisoned cache must never reach a published artifact.
- `pnpm audit` complements Dependabot alerts for JavaScript; it fails on high or critical advisories. Before the first run it found one (re2js, through markdownlint), fixed with a pnpm override ([repository.md](repository.md#known-limitations-and-risks-to-revisit)).

## Scorecard

Publishing results restricts the workflow: no `env` or `defaults`, no `run` steps, only Scorecard's allowed actions (checkout, scorecard-action, upload-artifact, upload-sarif), and a single GitHub-hosted Ubuntu runner label (the scorecard-action README; the last server code in ossf/scorecard-webapp accepts `ubuntu-latest` and `ubuntu-XX.YY` from 22.04, so `ubuntu-24.04` is expected to pass; tracked in [docs/10](../10-plan-y-pendientes.md)). `id-token: write` exists only in its job.

## Dependabot

| Ecosystem | Directory | Updates |
| --- | --- | --- |
| `uv` | `/` | the uv workspace (root and `backend/`): both `pyproject.toml`, `uv.lock`; `uv_build` is ignored, its lower bound follows uv |
| `npm` | `/` | the pnpm workspace (root and `frontend/`), `pnpm-lock.yaml`; TypeScript majors are ignored while typescript-eslint does not support them |
| `github-actions` | `/` | the workflows' SHAs and version comments |

- Weekly, with `cooldown: default-days: 7`, the same cooldown as uv, pnpm and mise ([README](README.md#versions-policy)).
- Groups: minor and patch updates come in one pull request per ecosystem, and each major update in its own, so a breaking change is reviewed alone. Every `github/codeql-action` step, in every workflow (`init`, `analyze`, `upload-sarif`), goes in one group, majors and security updates included (a group covers version updates only unless `applies-to` says otherwise), because the action fails when its steps run different versions (seen on 2026-11-12, when Dependabot split `init` and `analyze` into separate pull requests). A dependency joins the first group it matches, so the `codeql-action` group comes before the other Actions group (checked in GitHub's Dependabot options reference, 2026-11-12). That `github/codeql-action*` matches the subpath actions is not documented; other repositories use the same pattern and get one pull request.
- Titles: `prefix` and `prefix-development` `build(deps)` give `build(deps): bump …`, which the title check accepts (checked on the first Dependabot PRs, 2026-11-10; a grouped pull request's title is not checked yet). `include: "scope"` is not used: it would give `build(deps-dev)`, a scope the check rejects.
- Security updates are enabled by the user in the repository settings; they ignore the cooldown.
- uv's `required-version` did not stop Dependabot's uv updates (checked on the first one, 2026-11-10, when it was in `backend/pyproject.toml`; it is now in the root `pyproject.toml`, see [repository.md](repository.md#known-limitations-and-risks-to-revisit)).
- An update that the project's decisions rule out goes in `ignore`, with a comment pointing to the decision.
- mise is not a Dependabot ecosystem. `tool-updates.yml` reminds monthly to run `just update-tools`, which runs `mise upgrade --bump`: mise's own `minimum_release_age = "7d"` (in `mise.toml`, checked in mise's settings reference) keeps the same cooldown. Nothing updates five pins, so the reminder lists them: mise's version in `ci.yml` and `release.yml`, the Ubuntu runner label in every workflow, uv's `required-version` in the root `pyproject.toml`, `uv_build`'s lower bound in `backend/pyproject.toml`, and Python's exact version in `.python-version`.
- `uv_build`'s lower bound in `backend/pyproject.toml` is uv's version in `mise.toml`, raised with it, and Dependabot ignores `uv-build`. A lower bound above the installed uv makes uv download `uv_build` from PyPI instead of running its built-in backend, a build dependency no lockfile pins (uv's build backend docs, checked 2026-11-12; seen the same day, when Dependabot raised it to 0.13.7 with uv at 0.13.6).
