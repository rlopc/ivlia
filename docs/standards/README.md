# Standards

The standards document describes the current state of the project's tools and practices, in detail and without history. It links to the configuration files instead of copying their values, so the files stay the single source. Any change of tools or practices updates it in the same pull request. Design rationale lives in the Spanish design documents ([docs/00-indice.md](../00-indice.md)); decisions that are hard to reverse live in ADRs.

## Files

- [repository.md](repository.md): tool versions, `just`, pre-commit, repository files and GitHub settings.
- [ai-development.md](ai-development.md): Claude Code configuration, Validar, reviewer and OpenSpec.
- [security.md](security.md): threat model and security measures.
- [backend.md](backend.md): the Python package: layers, typing, tests, configuration, secrets, migrations, logs and traces, `ivlia-server`.
- [api.md](api.md): the HTTP API: contract and its export, frontend types and validator, OpenAPI, endpoints, same origin and dev origin, Host and Origin, token, web session.
- [frontend.md](frontend.md): the SPA: layout and boundaries, lint and types, SSE client, chat, tests, end-to-end and accessibility.
- [ci.md](ci.md): GitHub Actions workflows, their security rules, required checks and Dependabot.
- [release.md](release.md): versioning and CHANGELOG, the release workflow and its credential, the wheel, provenance, install and verify.

## Git

- Short branches named `<type>/<short-description>` (for example `chore/repo-setup`), created from `main`, the only permanent branch.
- One pull request per step, squash-merged into `main`. `main` always works and `just check` is green.
- PR title: `<type>(<area>): <summary>`. Types are the standard Conventional Commits types (`feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`, `ci`, `perf`, `style`, `revert`). Areas: `backend`, `frontend`, `cli`, `docs`, `ci`, `repo`, `deps` (dependency updates). After the squash the title is the commit message. CI checks the format ([ci.md](ci.md#workflows)).
- The user reviews and merges every PR. Settings that enforce this: [repository.md](repository.md#github).

## Documentation rule

Every pull request updates the documentation it affects in the same PR:

- Specs, if behaviour changed.
- This standards document, if tools or practices changed.
- An ADR, if the decision is hard to reverse and has defensible alternatives.
- The decision map, if a decision changed.
- Obsolete descriptions found along the way.

The [PR template](../../.github/pull_request_template.md) lists these checks.

## Decisions and ADRs

- The decision map, [docs/decisions/README.md](../decisions/README.md), lists every technical decision with its status (Final or Provisional), when to revisit it and a link to where it is explained.
- A decision that is hard to reverse and has defensible alternatives gets an ADR in [docs/decisions/adr/](../decisions/adr/): numbered (`NNNN-short-title.md`), MADR minimal format (context and problem, considered options, decision outcome, consequences), with `status` and `date` in its front matter.
- ADRs are immutable. A change of mind is a new ADR; the old one gets `status: superseded by NNNN`.
- The pull request that takes or changes a decision updates the map, and the ADR if there is one.

## Versions policy

- Tools and dependencies are pinned to exact versions, and every ecosystem has a lockfile: [mise.toml](../../mise.toml) with `mise.lock`, [package.json](../../package.json) with `pnpm-lock.yaml`, and [backend/pyproject.toml](../../backend/pyproject.toml) with `backend/uv.lock`. pre-commit has no remote hooks: each hook runs a tool locked in one of those lockfiles ([repository.md](repository.md#pre-commit)).
- Cooldown: a version is used only when it is at least 7 days old.
  - mise: `minimum_release_age = "7d"` in [mise.toml](../../mise.toml), which `mise upgrade` (`just update-tools`) respects. CI pins mise itself to the same version as the Mac ([ci.md](ci.md#the-ci-job)), and `min_version` in `mise.toml` refuses an older one.
  - uv: `exclude-newer = "7 days"` in [backend/pyproject.toml](../../backend/pyproject.toml).
  - pre-commit's own dependencies are locked in `.mise/locks/` by mise's pipx backend, with the same cooldown: `mise lock` on 2026-11-11 wrote `exclude-newer` exactly 7 days back. Observed, not documented by mise.
  - pnpm: `minimumReleaseAge: 10080` (minutes) in [pnpm-workspace.yaml](../../pnpm-workspace.yaml).
  - Dependabot: `cooldown: default-days: 7` in every ecosystem ([ci.md](ci.md#dependabot)).
- mise's cooldown needs a release date: for a version without one, mise warns that it could not check it; read the warnings of `just update-tools`.
- Exceptions (for example an urgent security fix) are explicit and per package: `exclude-newer-package` in uv, `minimumReleaseAgeExclude` in pnpm, `minimum_release_age_excludes` in mise. Dependabot security updates ignore the cooldown.
- Current exceptions:
  - mise 2026.11.5 in CI, until 2026-11-16: `mise.lock` is in lockfile format 4, which mise 2026.11.0 (the newest release 7 days old on 2026-11-10) cannot read. CI uses the Mac's version instead.
- Before using a version, the Validar step re-confirms it ([ai-development.md](ai-development.md#validar)).
