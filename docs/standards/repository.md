# Repository

## Toolchain rules

Every development tool meets these rules. Review a tool against them whenever it is added, upgraded or reconfigured.

- **Same everywhere**: a tool behaves the same in the editor, Claude Code's hooks, the terminal, pre-commit and CI. Its configuration lives only in its versioned config file; editor settings only point to it, and an editor tool that cannot is turned off.
- **One owner**: each file type has one formatter, and each check one tool. Two tools may check the same thing only when one of them reports it earlier.
- **Early feedback**: checks run as early as possible: while writing, then at commit, then in CI. Fast checks run first; slow ones in `just check` and CI.
- **Clear scope**: each tool states which files it covers and which it skips. The files it sees are the versioned ones, and generated files are skipped by every tool.
- **Consistent**: code, configuration and documentation say the same thing ([documentation rule](README.md#documentation-rule)).
- **Reproducible**: exact versions from the lockfiles, with checksums where the tool allows it; actions pinned by commit SHA. It works on macOS arm64 and Linux x64, also where mise is not activated.
- **Up to date**: current releases within the [versions policy](README.md#versions-policy).
- **Proven**: each check is shown to fail on a bad input, not only to pass (hook tests, rules checked with a forbidden case).
- **Least privilege**: a tool gets only the network, permissions and secrets it needs; local checks run offline.
- **Best practice**: configured as its official documentation recommends; any deviation is written down with its reason.
- **Minimal**: a tool is added only when no existing one covers the need.

## Tool versions

- [mise.toml](../../mise.toml) pins node, pnpm, uv, just, lychee, gitleaks, actionlint, shellcheck and zizmor. `mise.lock` is enabled (`lockfile = true`) and holds the versions and the checksums of the downloaded binaries for macOS arm64 and Linux x64.
- pnpm is pinned only in `mise.toml`, not in `packageManager` of `package.json`: with `packageManager`, pnpm 12 writes `pnpm-lock.yaml` as two YAML documents, which GitHub's dependency graph does not read, so Dependabot would raise no security alerts for JavaScript. Corepack is not used.
- Python is not in mise: uv installs it, from [.python-version](../../.python-version) at the root (exact patch).
- The root is a uv workspace ([pyproject.toml](../../pyproject.toml)), as the pnpm workspace is for Node: a non-package root (`package = false`) that holds the repository's Python tools, with `backend/` as its member. One `uv.lock`, one `.venv` and one `.python-version` at the root. uv reads `[tool.uv]` (`required-version`, `exclude-newer`) only from the root.
- pre-commit and pre-commit-hooks are dev dependencies of the root, locked with hashes in `uv.lock`. `just setup` installs everything with `uv sync --locked --all-packages`: a plain `uv sync` is exact and installs one part only (in `backend/` it removes pre-commit). `uv run` does not remove packages, so the recipes do not have this problem.
- The root pnpm workspace ([pnpm-workspace.yaml](../../pnpm-workspace.yaml)) holds Prettier, markdownlint-cli2 and OpenSpec as exact dev dependencies, with a single `pnpm-lock.yaml`. `frontend/` is its other package ([frontend.md](frontend.md)).
- `.mise/` (mise local state) is gitignored. A fresh clone needs `mise trust` before `mise install`. `just setup` and CI install with `mise install --locked`: every tool has a URL and a checksum for both platforms in `mise.lock`. `exec_auto_install = false`: `mise exec` never installs a missing tool on its own.
- `[env]` in `mise.toml` also sets `IVLIA_ENV=dev` and `IVLIA_HOME=<repo>/.dev`, so any command in the repository uses the dev installation ([backend.md](backend.md#configuration)).

## `just` recipes

Defined in the [justfile](../../justfile). It exports `OPENSPEC_TELEMETRY=0`, `DO_NOT_TRACK=1`, and `IVLIA_ENV=dev` with `IVLIA_HOME=<repo>/.dev` (the dev installation). `mise.toml` sets the last two too, and jdx/mise-action exports them in CI (its `env` input, on by default); the justfile repeats them on purpose, so every recipe uses the dev installation however `just` is started. `set ignore-comments` keeps comment lines inside linewise recipes (not shebang recipes) from being echoed or run.

- `just setup`: `mise install --locked`, `pnpm install --frozen-lockfile`, the Playwright Chromium browser, `uv sync --locked --all-packages`, `pre-commit install` and `pre-commit install-hooks` (through `uv run --locked`, like every pre-commit call). Uses the network; the only recipe that installs.
- `just check`: every local check, stopping at the first error: `pre-commit run --all-files`, `gitleaks git`, the tests of both `.claude` hooks, `openspec validate --all --strict`, `just check-links --offline`, `just check-backend` and `just check-frontend`.
- `just check-links`: lychee on every versioned Markdown file ([link checking](#link-checking)); extra arguments go to lychee.
- `just check-backend`: mypy, import-linter, and the tests under coverage with its two reports ([backend.md](backend.md#tests-and-coverage)). All through `uv run --locked`. ruff runs in pre-commit.
- `just check-frontend`: the contract check, ESLint, knip, Vitest with coverage, the build (`tsc -b`, then `vite build`) and Playwright ([frontend.md](frontend.md)). Prettier runs in pre-commit. Playwright starts a server and a browser, so it runs outside Claude Code's sandbox.
- `just contract`: exports the event contract and the OpenAPI document, and generates the frontend's types and validator ([api.md](api.md#export)).
- `just dev`: `ivlia-server --reload` on port 8766, for the dev installation.
- `just dev-web`: `just dev` and the Vite dev server together; `ivlia web` opens Vite ([frontend.md](frontend.md#development)).
- `just update-tools`: `mise upgrade --bump`, which upgrades every tool in `mise.toml` to its newest release at least 7 days old and updates `mise.lock`. Uses the network. `tool-updates.yml` reminds monthly ([ci.md](ci.md#dependabot)).
- `just review-diff [base]`: writes the diff against `base` (default `main`; pass the parent branch of a stacked PR) and the changed-file list to `.dev/review/` for the reviewer agent. `base` reaches git as a positional argument after `--end-of-options`, so it is never shell code nor a git option.

## Pre-commit

Configured in [.pre-commit-config.yaml](../../.pre-commit-config.yaml), with pre-commit. Every hook is local (`language: unsupported`), so pre-commit builds no environments and pre-commit-uv is not needed.

- Rule: every hook is local and runs a tool with a lockfile, at the locked version. Local hooks use `language: unsupported` and call their tool through `mise exec --`, so they work where mise is not activated (IDEs, git GUIs, a shell started before activation). There are no remote hooks, so Dependabot has nothing to update here.
  - gitleaks, actionlint, zizmor and shellcheck: installed by mise (binaries whose checksums `mise.lock` records). zizmor and shellcheck keep the `files`, `types` and `require_serial` of their upstream hooks; zizmor adds `--offline`, so it never uses the network locally. shellcheck on `PATH` also lets actionlint check the workflows' `run:` scripts.
  - markdownlint-cli2 and Prettier: run through pnpm.
  - ruff format and ruff check: run through `uv run --locked --project backend`.
  - pre-commit-hooks: run through `uv run --locked`, from the root's dev group.
- Hooks: pre-commit-hooks' commit checks, with the stages of their upstream definitions (`check-added-large-files`, 500 kB, with `--enforce-all` so `just check` and CI check every file, lockfiles excluded because they grow on their own; `check-case-conflict`, because macOS ignores case and CI does not; `check-merge-conflict` with `--assume-in-merge`, so it also runs outside a merge and in CI), its `end-of-file-fixer` and `trailing-whitespace` on the text files no formatter owns (see [formatting](#formatting)), gitleaks (staged changes), actionlint (workflows), zizmor, shellcheck, markdownlint-cli2 with `--fix`, ruff check with `--fix` before ruff format, as Ruff recommends (Python in `backend/` and `.claude/hooks/`), and Prettier on every file (`--ignore-unknown` and `.prettierignore` decide).
- A hook that changes files fails that run; running `just check` again passes.
- `minimum_pre_commit_version` is set. prek is not used: it is still 0.x; revisit at 1.0.

## Formatting

- Ruff owns Python: `backend/` with its own configuration, and the Claude Code hooks (`.claude/hooks/`, standard library only) with the root's: Ruff's default rules, and the project's Python, which the hooks run with.
- Prettier owns JavaScript, TypeScript, JSON, YAML and CSS ([.prettierrc.json](../../.prettierrc.json)). It ignores Markdown ([.prettierignore](../../.prettierignore)). `.jsonc` files get no trailing commas, which VS Code flags.
- Text files that no formatter owns (TOML, shell, SQL, `justfile`, the ignore files, `.python-version`): pre-commit-hooks' `end-of-file-fixer` and `trailing-whitespace`, through `uv run --locked` (it is a root dev dependency). One `files` pattern in `.pre-commit-config.yaml` (`*unowned`), kept in sync with the lint hook. `LICENSE` is left out: its text is copied verbatim.
- markdownlint-cli2 owns Markdown. Rules are in [.markdownlint.jsonc](../../.markdownlint.jsonc), each with its reason: line length and first-line-heading rules off, duplicate headings allowed between non-siblings. Skipped files are in [.markdownlint-cli2.jsonc](../../.markdownlint-cli2.jsonc).
- shellcheck: SC2016 is disabled only in the two `.claude/hooks/*.test.sh`, with a reason (literal test commands and files).

## Generated files

Never edited by hand; regenerated with their command and excluded from Prettier and markdownlint.

- Lockfiles: `pnpm-lock.yaml`, `mise.lock` (regenerate with `mise lock`), and `uv.lock` (regenerate with `uv lock`).
- `CHANGELOG.md` and `.release-please-manifest.json`: written by release-please ([release.md](release.md#versioning-and-changelog)).
- `backend/schemas/events.schema.json` and `backend/schemas/openapi.json`: regenerate with `just contract` ([api.md](api.md#export)).
- `frontend/src/contract/`: regenerate with `just contract` ([api.md](api.md#frontend-types-and-validator)). Also excluded from ESLint, coverage and knip.
- OpenSpec output: `.claude/skills/openspec-*/` and `.claude/commands/opsx/` (regenerate with `openspec update` after an upgrade). See [ai-development.md](ai-development.md#openspec).

`pnpm-lock.yaml` is one YAML document, which GitHub's dependency graph reads, because pnpm is not pinned in `packageManager` ([tool versions](#tool-versions)).

## Editor

[.vscode/extensions.json](../../.vscode/extensions.json) recommends the extensions that run the project's checks while writing: ESLint, Prettier, markdownlint, Ruff and Mypy, with the Python extension. [.vscode/settings.json](../../.vscode/settings.json) makes them follow the same checks:

- The Mypy extension runs from the nearest `pyproject.toml` (`backend/`), so it reads the project's mypy configuration, and uses the project's mypy, not its bundled one.
- Pylance type checking is off: mypy is the only type checker, in the terminal and in CI.
- Known deviation: the markdownlint extension bundles its own markdownlint-cli2 (0.23.2 in extension 0.62.1, checked 2026-11-11) and has no setting to use the project's. It reads the same config files, so it stays as early feedback; pre-commit and CI, with the project's version, decide.

## Link checking

`just check-links` runs lychee on the versioned Markdown files (`git ls-files`, the files pre-commit sees), with its options in [lychee.toml](../../lychee.toml) (anchors included; generated files skipped, as markdownlint skips them). `just check` runs it with `--offline`, for local links and anchors; `links.yml` runs it online, with the lychee of `mise.lock`. A glob is not used: lychee skips hidden folders (`.claude/`, `.github/`) and does not read nested `.gitignore` files. markdownlint's MD051 also checks anchors within the same file; it stays on because it reports them in the editor, which lychee does not. External links are checked weekly in CI ([ci.md](ci.md#workflows)).

## Repository files

- `README.md`, `SECURITY.md`, `CONTRIBUTING.md` and `LICENSE` at the root.
- `.github/`: [pull request template](../../.github/pull_request_template.md) and issue forms (bug report, feature request) with blank issues disabled and a link to private security reporting.
- No CODEOWNERS, Code of Conduct or DCO until contributions open.
- `.gitignore` excludes local files (`*.local.*`), `.dev/` (the dev installation, Validar reports, review diffs), mise's local state in `.mise/`, the scratch files of the lint hook test (its backend folders and its temporary workflows), and build and cache outputs.

## License

AGPL-3.0-or-later. The full text goes in `LICENSE`; `package.json` declares the same identifier.

## GitHub

- Only squash merging is allowed. The commit title is the PR title and the body is blank.
- Ruleset on `main`, active, with no bypass: restrict deletions, block force pushes, require linear history, require a pull request with 0 approvals, squash merge only, and the required status checks of [ci.md](ci.md#workflows).
- Private vulnerability reporting is enabled (see [SECURITY.md](../../SECURITY.md)).
- Secret scanning and push protection are enabled (default on public repositories).

## Known limitations and risks to revisit

- Dependabot's support for a uv workspace with `[dependency-groups]` at the root is not documented: check that its first run updates both the root's pre-commit and the backend's dependencies.
- mise verifies checksums on every download ("Checksums are still verified on every download"), but not tools already on disk or restored from a cache.
- Dependency overrides in [pnpm-workspace.yaml](../../pnpm-workspace.yaml) (`overrides`) carry a security fix that a dependency has not released yet. Each one says when to remove it.
- gitleaks is in maintenance mode (security fixes only); its README points to Betterleaks, by the same maintainer. Revisit.
- actionlint (rhysd) has had no release since 1.7.12 (2026-03-30) and no commit since 2026-04-19. mise's registry marks it deprecated in favour of jactionlint, a fork created on 2026-10-05 by mise's own maintainer, which also adds security and policy checks (zizmor covers those here) and changes fast (9 releases and a new major in 5 weeks). actionlint stays, pinned, and mise's install shows the deprecation notice. Revisit when a workflow needs syntax actionlint does not know, when jactionlint settles, or if actionlint is archived (checked 2026-11-10).
- prek is still 0.x. Revisit at 1.0.
