# Standards

The standards document describes the current state of the project's tools and practices, in detail and without history. It links to the configuration files instead of copying their values, so the files stay the single source. Any change of tools or practices updates it in the same pull request. Design rationale lives in the Spanish design documents ([docs/00-indice.md](../00-indice.md)); decisions that are hard to reverse live in ADRs.

## Files

- [repository.md](repository.md): tool versions, `just`, pre-commit, repository files and GitHub settings.
- [ai-development.md](ai-development.md): Claude Code configuration, Validar, reviewer and OpenSpec.
- [security.md](security.md): threat model and security measures.
- [backend.md](backend.md): the Python package: layers, typing, tests, configuration, secrets, migrations, logs and traces, `ivlia-server`.
- [api.md](api.md): the HTTP API: contract and its export, OpenAPI, endpoints, Host and Origin, token, web session.
- `frontend.md`: added in step 4.
- `ci.md`: added in step 5.
- `release.md`: added in step 6.

## Git

- Short branches named `<type>/<short-description>` (for example `chore/repo-setup`), created from `main`, the only permanent branch.
- One pull request per step, squash-merged into `main`. `main` always works and `just check` is green.
- PR title: `<type>(<area>): <summary>`. Types are the standard Conventional Commits types (`feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`, `ci`, `perf`, `style`, `revert`). Areas: `backend`, `frontend`, `cli`, `docs`, `ci`, `repo`, `deps` (dependency updates). After the squash the title is the commit message.
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

- Tools and dependencies are pinned to exact versions, and every ecosystem has a lockfile: [mise.toml](../../mise.toml) with `mise.lock`, [package.json](../../package.json) with `pnpm-lock.yaml`, and [backend/pyproject.toml](../../backend/pyproject.toml) with `backend/uv.lock`. Remote pre-commit hooks are pinned by revision in [.pre-commit-config.yaml](../../.pre-commit-config.yaml).
- Cooldown: a version is used only when it is at least 7 days old.
  - mise: versions in `mise.toml` are chosen by hand to respect it.
  - uv: `UV_EXCLUDE_NEWER="7 days"` in the [justfile](../../justfile) and in `[env]` of [mise.toml](../../mise.toml) (pre-commit environments, also when a hook is set up outside `just` in a shell with mise activated); `exclude-newer = "7 days"` in [backend/pyproject.toml](../../backend/pyproject.toml).
  - pnpm: `minimumReleaseAge: 10080` (minutes) in [pnpm-workspace.yaml](../../pnpm-workspace.yaml).
  - Dependabot: `cooldown` from step 5.
- Exceptions (for example an urgent security fix) are explicit and per package: `exclude-newer-package` in uv, `minimumReleaseAgeExclude` in pnpm.
- Before using a version, the Validar step re-confirms it ([ai-development.md](ai-development.md#validar)).
