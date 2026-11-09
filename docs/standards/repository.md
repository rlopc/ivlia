# Repository

## Tool versions

- [mise.toml](../../mise.toml) pins node, uv, just, lychee, gitleaks, actionlint and pre-commit (with pre-commit-uv). `mise.lock` is enabled (`lockfile = true`) and holds the versions and the checksums of the downloaded binaries for macOS arm64 and Linux x64.
- pnpm is pinned only in `packageManager` of [package.json](../../package.json); mise reads it through `idiomatic_version_file_enable_tools`. Corepack is not used.
- Python is not in mise: uv reads `.python-version` (from step 2).
- pre-commit is installed by mise's pipx backend, which uses uv. `mise.lock` stores only its version, without checksum.
- The root pnpm workspace ([pnpm-workspace.yaml](../../pnpm-workspace.yaml)) holds Prettier, markdownlint-cli2 and OpenSpec as exact dev dependencies, with a single `pnpm-lock.yaml`. `frontend/` joins it in step 4.
- `.mise/` (mise local state) is gitignored. A fresh clone needs `mise trust` before `mise install`.

## `just` recipes

Defined in the [justfile](../../justfile). It exports `UV_EXCLUDE_NEWER="7 days"` (cooldown for the pre-commit environments), `OPENSPEC_TELEMETRY=0` and `DO_NOT_TRACK=1`.

- `just setup`: `mise install`, `pnpm install --frozen-lockfile`, `pre-commit install` and `pre-commit install-hooks`. Uses the network; the only recipe that installs.
- `just check`: every local check, stopping at the first error: `pre-commit run --all-files`, `gitleaks git`, the `.claude` hook test, `openspec validate --all --strict` and the offline link check.
- `just fix`: Prettier and markdownlint auto-fixes.
- `just review-diff`: writes the diff against `main` and the changed-file list to `.dev/review/` for the reviewer agent.

## Pre-commit

Configured in [.pre-commit-config.yaml](../../.pre-commit-config.yaml), with pre-commit and pre-commit-uv.

- Rule: a tool that has a lockfile runs as a local hook with the locked version. Local hooks use `language: unsupported` and call their tool through `mise exec --`, so they work where mise is not activated (IDEs, git GUIs, a shell started before activation).
  - gitleaks and actionlint: installed by mise (binaries with checksums in `mise.lock`).
  - markdownlint-cli2 and Prettier: run through pnpm.
  - ruff will follow with `uv run --locked` in step 2.
- zizmor and shellcheck have no lockfile in the repository: they are remote hooks pinned by revision.
- Hooks: gitleaks (staged changes), actionlint (workflows), zizmor, shellcheck, markdownlint-cli2 with `--fix`, Prettier.
- `minimum_pre_commit_version` is set. prek is not used: it is still 0.x; revisit at 1.0.

## Formatting

- Prettier owns JavaScript, TypeScript, JSON, YAML and CSS ([.prettierrc.json](../../.prettierrc.json)). It ignores Markdown ([.prettierignore](../../.prettierignore)).
- markdownlint-cli2 owns Markdown. Rules are in [.markdownlint.jsonc](../../.markdownlint.jsonc) (line length and first-line-heading rules off; duplicate headings allowed between non-siblings, because `docs/04` has two "Fuentes" headings at different levels). Skipped files are in [.markdownlint-cli2.jsonc](../../.markdownlint-cli2.jsonc).
- shellcheck: SC2016 is disabled only in `.claude/hooks/researcher-bash-guard.test.sh`, with a reason (literal test commands).

## Generated files

Never edited by hand; regenerated with their command and excluded from Prettier and markdownlint.

- Lockfiles: `pnpm-lock.yaml`, `mise.lock` (and `uv.lock` from step 2).
- OpenSpec output: `.claude/skills/openspec-*/` and `.claude/commands/opsx/` (regenerate with `openspec update` after an upgrade). See [ai-development.md](ai-development.md#openspec).

`pnpm-lock.yaml` has two YAML documents; Dependabot may not raise security alerts for it (to investigate in steps 4 and 5).

## Link checking

`lychee --offline --include-fragments` checks local links and anchors in all Markdown; `just check` runs it. External links are checked weekly in CI from step 5.

## Repository files

- `README.md`, `SECURITY.md`, `CONTRIBUTING.md` and `LICENSE` at the root.
- `.github/`: [pull request template](../../.github/pull_request_template.md) and issue forms (bug report, feature request) with blank issues disabled and a link to private security reporting.
- No CODEOWNERS, Code of Conduct or DCO until contributions open.
- `.gitignore` excludes local files (`*.local.*`), `.dev/` (Validar reports, review diffs), `.mise/`, and build and cache outputs.

## License

AGPL-3.0-or-later. The full text goes in `LICENSE`; `package.json` declares the same identifier.

## GitHub

- Only squash merging is allowed. The commit title is the PR title and the body is blank.
- Ruleset on `main`, active, with no bypass: restrict deletions, block force pushes, require linear history, require a pull request with 0 approvals, squash merge only. Required status checks are added in step 5.
- Private vulnerability reporting is enabled (see [SECURITY.md](../../SECURITY.md)).
- Secret scanning and push protection are enabled (default on public repositories).

## Known limitations and risks to revisit

- pipx tools have no checksum in `mise.lock`. `just setup` runs `mise install` without `--locked`, because strict mode fails for the pipx backend without a mise-managed Python. Whether checksums are still verified without `--locked` is to be confirmed in the step 5 Validar.
- gitleaks is in maintenance mode (security fixes only). Revisit.
- prek is still 0.x. Revisit at 1.0.
