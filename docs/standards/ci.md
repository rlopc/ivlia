# CI

GitHub Actions in [.github/workflows/](../../.github/workflows/) and Dependabot in [.github/dependabot.yml](../../.github/dependabot.yml). CI runs the same checks as the developer's Mac (`just check`) and adds the ones that only make sense on GitHub. It is the final arbiter ([docs/09](../09-ia-en-el-desarrollo.md), "Guardarraíles").

## Workflows

| Workflow | When | What |
| --- | --- | --- |
| `ci.yml` (job `just check`) | pull requests to `main`, pushes to `main` | `mise install`, `just setup`, Playwright's system packages, `just check`, `pnpm audit --audit-level high` |
| `codeql.yml` (jobs `analyze (…)`) | pull requests, pushes to `main`, weekly | CodeQL advanced setup for `actions`, `javascript-typescript` and `python`, `build-mode: none` |
| `scorecard.yml` | pushes to `main`, weekly | OpenSSF Scorecard, published, with SARIF to code scanning |
| `pr-title.yml` (job `PR title`) | pull request opened, edited, synchronized or reopened | the title follows Conventional Commits with a required scope ([README](README.md#git)) |
| `links.yml` | weekly, manual | external links with lychee; on failure, opens the "Broken external links" issue or comments on the open one |
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

## The CI job

- mise-action installs mise 2026.11.0 only (`install: false`), verified against its signed checksums; a `mise install` step installs the tools, with the job's read-only token to avoid GitHub API rate limits. The action would add `--locked`, which fails for pre-commit (pipx backend; see [repository.md](repository.md#known-limitations-and-risks-to-revisit)).
- Checkout with `fetch-depth: 0`, because gitleaks scans the whole history.
- Two caches: mise-action's own, of the installed tools (on by default, renewed every 30 days), and one `actions/cache` for the pnpm store, the uv cache and pre-commit's environments, keyed on their lockfiles and config. `uv cache prune --ci` keeps the uv part small. Playwright's browser is not cached, as Playwright advises; its system packages are installed on each run.
- No cache in release workflows (step 6): a poisoned cache must never reach a published artifact.
- `pnpm audit` complements Dependabot alerts for JavaScript; it fails on high or critical advisories. Before the first run it found one (re2js, through markdownlint), fixed with a pnpm override ([repository.md](repository.md#known-limitations-and-risks-to-revisit)).

## Scorecard

Publishing results restricts the workflow: no `env` or `defaults`, no `run` steps, and only Scorecard's allowed actions (checkout, scorecard-action, upload-artifact, upload-sarif). `id-token: write` exists only in its job.

## Dependabot

| Ecosystem | Directory | Updates |
| --- | --- | --- |
| `uv` | `/backend` | `pyproject.toml`, `uv.lock` |
| `npm` | `/` | the pnpm workspace, `pnpm-lock.yaml`; whether it also updates `frontend/package.json` is checked after the merge (the alternative is `directories: ["/", "/frontend"]`) |
| `github-actions` | `/` | the workflows' SHAs and version comments |
| `pre-commit` | `/` | `rev` in `.pre-commit-config.yaml` |

- Weekly, with `cooldown: default-days: 7`, the same cooldown as uv, pnpm and mise ([README](README.md#versions-policy)). No groups.
- Titles: `prefix` and `prefix-development` `build(deps)`, which by Dependabot's documented colon rule should give `build(deps): …`, a title the check accepts; the first Dependabot PR confirms it. `include: "scope"` is not used: it would give `build(deps-dev)`, a scope the check rejects.
- Security updates are enabled by the user in the repository settings; they ignore the cooldown.
- Risk to check on the first uv update: `required-version` of uv in `backend/pyproject.toml` refuses other uv versions, and Dependabot runs its own. If it fails, widen the range or keep uv updates by hand.
- mise is not a Dependabot ecosystem. `tool-updates.yml` reminds monthly to run `just update-tools`, which runs `mise upgrade --bump`: mise's own `minimum_release_age = "7d"` (in `mise.toml`, checked in mise's settings reference) keeps the same cooldown. Nothing updates three pins, so the reminder lists them: mise's version in `ci.yml`, `pre-commit-uv` in `mise.toml`, and uv's `required-version` in `backend/pyproject.toml`.
