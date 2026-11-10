# Repository

## Tool versions

- [mise.toml](../../mise.toml) pins node, pnpm, uv, just, lychee, gitleaks, actionlint and pre-commit (with pre-commit-uv). `mise.lock` is enabled (`lockfile = true`) and holds the versions and the checksums of the downloaded binaries for macOS arm64 and Linux x64.
- pnpm is pinned only in `mise.toml`, not in `packageManager` of `package.json`: with `packageManager`, pnpm 12 writes `pnpm-lock.yaml` as two YAML documents, which GitHub's dependency graph does not read, so Dependabot would raise no security alerts for JavaScript. Corepack is not used.
- Python is not in mise: uv reads [backend/.python-version](../../backend/.python-version). Python dependencies: [backend.md](backend.md#project).
- pre-commit is installed by mise's pipx backend, which uses uv. `mise.lock` stores its version, and `.mise/locks/pipx-pre-commit/` (versioned) its dependency graph: a `uv.lock` with the hash of every package. mise needs that folder to install it.
- The root pnpm workspace ([pnpm-workspace.yaml](../../pnpm-workspace.yaml)) holds Prettier, markdownlint-cli2 and OpenSpec as exact dev dependencies, with a single `pnpm-lock.yaml`. `frontend/` is its other package ([frontend.md](frontend.md)).
- `.mise/` (mise local state) is gitignored. A fresh clone needs `mise trust` before `mise install`.
- `[env]` in `mise.toml` also sets `IVLIA_ENV=dev` and `IVLIA_HOME=<repo>/.dev`, so any command in the repository uses the dev installation ([backend.md](backend.md#configuration)).

## `just` recipes

Defined in the [justfile](../../justfile). It exports `UV_EXCLUDE_NEWER="7 days"` (cooldown for the pre-commit environments), `OPENSPEC_TELEMETRY=0`, `DO_NOT_TRACK=1`, and `IVLIA_ENV=dev` with `IVLIA_HOME=<repo>/.dev` (the dev installation).

- `just setup`: `mise install`, `pnpm install --frozen-lockfile`, the Playwright Chromium browser, `uv sync --locked` for `backend/`, `pre-commit install` and `pre-commit install-hooks`. Uses the network; the only recipe that installs.
- `just check`: every local check, stopping at the first error: `pre-commit run --all-files`, `gitleaks git`, the tests of both `.claude` hooks, `openspec validate --all --strict`, the offline link check, `just check-backend` and `just check-frontend`.
- `just check-backend`: mypy, import-linter, and the tests under coverage with its two reports ([backend.md](backend.md#tests-and-coverage)). All through `uv run --locked`. ruff runs in pre-commit.
- `just check-frontend`: the contract check, ESLint, knip, Vitest with coverage, the build (`tsc -b`, then `vite build`) and Playwright ([frontend.md](frontend.md)). Prettier runs in pre-commit. Playwright starts a server and a browser, so it runs outside Claude Code's sandbox.
- `just contract`: exports the event contract and the OpenAPI document, and generates the frontend's types and validator ([api.md](api.md#export)).
- `just dev`: `ivlia-server --reload` on port 8766, for the dev installation.
- `just dev-web`: `just dev` and the Vite dev server together; `ivlia web` opens Vite ([frontend.md](frontend.md#development)).
- `just fix`: Prettier and markdownlint auto-fixes.
- `just update-tools`: `mise upgrade --bump`, which upgrades every tool in `mise.toml` to its newest release at least 7 days old and updates `mise.lock`. Uses the network. `tool-updates.yml` reminds monthly ([ci.md](ci.md#dependabot)).
- `just review-diff`: writes the diff against `main` and the changed-file list to `.dev/review/` for the reviewer agent.

## Pre-commit

Configured in [.pre-commit-config.yaml](../../.pre-commit-config.yaml), with pre-commit and pre-commit-uv.

- Dependabot updates the `rev` of remote hooks ([ci.md](ci.md#dependabot)).
- Rule: a tool that has a lockfile runs as a local hook with the locked version. Local hooks use `language: unsupported` and call their tool through `mise exec --`, so they work where mise is not activated (IDEs, git GUIs, a shell started before activation).
  - gitleaks and actionlint: installed by mise (binaries whose checksums `mise.lock` records).
  - markdownlint-cli2 and Prettier: run through pnpm.
  - ruff format and ruff check: run through `uv run --locked --project backend`.
- zizmor and shellcheck have no lockfile in the repository: they are remote hooks pinned by revision.
- Hooks: gitleaks (staged changes), actionlint (workflows), zizmor, shellcheck, markdownlint-cli2 with `--fix`, ruff format and ruff check with `--fix` (Python in `backend/`), Prettier.
- A hook that changes files fails that run; running `just check` again passes.
- `minimum_pre_commit_version` is set. prek is not used: it is still 0.x; revisit at 1.0.

## Formatting

- Prettier owns JavaScript, TypeScript, JSON, YAML and CSS ([.prettierrc.json](../../.prettierrc.json)). It ignores Markdown ([.prettierignore](../../.prettierignore)).
- markdownlint-cli2 owns Markdown. Rules are in [.markdownlint.jsonc](../../.markdownlint.jsonc) (line length and first-line-heading rules off; duplicate headings allowed between non-siblings, because `docs/04` has two "Fuentes" headings at different levels). Skipped files are in [.markdownlint-cli2.jsonc](../../.markdownlint-cli2.jsonc).
- shellcheck: SC2016 is disabled only in `.claude/hooks/researcher-bash-guard.test.sh`, with a reason (literal test commands).

## Generated files

Never edited by hand; regenerated with their command and excluded from Prettier and markdownlint.

- Lockfiles: `pnpm-lock.yaml`, `mise.lock` with `.mise/locks/` (regenerate with `mise lock`), and `backend/uv.lock`.
- `CHANGELOG.md` and `.release-please-manifest.json`: written by release-please ([release.md](release.md#versioning-and-changelog)).
- `backend/schemas/events.schema.json` and `backend/schemas/openapi.json`: regenerate with `just contract` ([api.md](api.md#export)).
- `frontend/src/contract/`: regenerate with `just contract` ([api.md](api.md#frontend-types-and-validator)). Also excluded from ESLint, coverage and knip.
- OpenSpec output: `.claude/skills/openspec-*/` and `.claude/commands/opsx/` (regenerate with `openspec update` after an upgrade). See [ai-development.md](ai-development.md#openspec).

`pnpm-lock.yaml` is one YAML document, which GitHub's dependency graph reads, because pnpm is not pinned in `packageManager` ([tool versions](#tool-versions)).

## Link checking

`lychee --offline --include-fragments` checks local links and anchors in all Markdown; `just check` runs it. External links are checked weekly in CI ([ci.md](ci.md#workflows)).

## Repository files

- `README.md`, `SECURITY.md`, `CONTRIBUTING.md` and `LICENSE` at the root.
- `.github/`: [pull request template](../../.github/pull_request_template.md) and issue forms (bug report, feature request) with blank issues disabled and a link to private security reporting.
- No CODEOWNERS, Code of Conduct or DCO until contributions open.
- `.gitignore` excludes local files (`*.local.*`), `.dev/` (the dev installation, Validar reports, review diffs), mise's local state in `.mise/` except `.mise/locks/`, the backend scratch folders of the lint hook test, and build and cache outputs.

## License

AGPL-3.0-or-later. The full text goes in `LICENSE`; `package.json` declares the same identifier.

## GitHub

- Only squash merging is allowed. The commit title is the PR title and the body is blank.
- Ruleset on `main`, active, with no bypass: restrict deletions, block force pushes, require linear history, require a pull request with 0 approvals, squash merge only, and the required status checks of [ci.md](ci.md#workflows).
- Private vulnerability reporting is enabled (see [SECURITY.md](../../SECURITY.md)).
- Secret scanning and push protection are enabled (default on public repositories).

## Known limitations and risks to revisit

- `just setup` and CI run `mise install` without `--locked`, because strict mode fails for the pipx backend without a mise-managed Python (checked 2026-11-10). Whether the checksums in `mise.lock` are still verified without `--locked` is not confirmed; mise's docs say only that a recorded checksum is still verified for backends exempt from strict mode. pre-commit's own dependencies are pinned with hashes in `.mise/locks/`. Revisit.
- Dependency overrides in [pnpm-workspace.yaml](../../pnpm-workspace.yaml) (`overrides`) carry a security fix that a dependency has not released yet. Each one says when to remove it.
- gitleaks is in maintenance mode (security fixes only); its README points to Betterleaks, by the same maintainer. Revisit.
- actionlint (rhysd) has had no release since 1.7.12 (2026-03-30) and no commit since 2026-04-19. mise's registry marks it deprecated in favour of jactionlint, a fork created on 2026-10-05 by mise's own maintainer, which also adds security and policy checks (zizmor covers those here) and changes fast (9 releases and a new major in 5 weeks). actionlint stays, pinned, and mise's install shows the deprecation notice. Revisit when a workflow needs syntax actionlint does not know, when jactionlint settles, or if actionlint is archived (checked 2026-11-10).
- prek is still 0.x. Revisit at 1.0.
