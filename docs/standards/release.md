# Release

How ivlia is versioned, released and installed. Design: [docs/08](../08-ingenieria-y-calidad.md) ("Entrega"). The workflow: [.github/workflows/release.yml](../../.github/workflows/release.yml).

## Versioning and CHANGELOG

- One SemVer version for the whole repository, computed from the Conventional Commits on `main` by release-please ([release-please-config.json](../../release-please-config.json), with the current version in `.release-please-manifest.json`).
- One package at `.`, `release-type: simple`, tags `vX.Y.Z` (`include-component-in-tag: false`). The first release is `0.1.0` (`initial-version`; the manifest's `0.0.0` is not a release). Before 1.0.0, `bump-minor-pre-major` makes a breaking change bump the minor version.
- release-please writes the version into `backend/pyproject.toml` and `frontend/package.json` (`extra-files`) and keeps `CHANGELOG.md`. `CHANGELOG.md` and the manifest are generated: never edit them by hand. `CHANGELOG.md` is excluded from markdownlint, because it repeats section headings, and the manifest from Prettier.
- The changelog uses release-please's default sections. Commits of hidden types alone (`build`, `ci`, `docs`, `chore`, …) do not open a release.

## Release workflow

On every push to `main`:

1. `release-please` opens or updates the release PR, titled `chore(repo): release X.Y.Z`, which the title check accepts. When that PR is merged, it tags the release and creates the GitHub release.
2. `sync`, while there is a release PR (found by release-please's `autorelease: pending` label): regenerates on its branch the generated files that carry the version, with their own commands, and commits them if they changed. They are `uv.lock`, which records the project's own version (`uv lock`; otherwise `uv run --locked` fails), and `backend/schemas/openapi.json`, whose `info.version` is the package version (the backend export of `just contract`; otherwise the export check fails). It runs after every release-please pass, because each pass rewrites the release branch.
3. `publish`, when a release was created: builds the SPA and the wheel from the tag, attests the wheel's build provenance, and attaches the wheel and its `.sigstore.json` bundle to the release.

## Credential

- release-please and `lock` act with a token of a GitHub App installed on this repository only, with read and write access to contents and pull requests. Events made with `GITHUB_TOKEN` do not trigger workflows, so its release PRs would never get the required checks.
- The App's client ID is the repository variable `RELEASE_APP_CLIENT_ID`, and its private key the secret `RELEASE_APP_PRIVATE_KEY`. Each job asks for a short-lived token narrowed to the permissions it needs; the action revokes it when the job ends.
- `publish` uses `GITHUB_TOKEN` with `contents: write` to upload assets, and `id-token: write` and `attestations: write` for the attestation.
- No cache in this workflow: a poisoned cache must never reach a release.

## Build

- Build backend `uv_build`. It packs everything under `backend/src/ivlia/`, including the built SPA in `api/static/`, which git ignores: the backend does not read `.gitignore` (checked by building the wheel, 2026-11-10).
- Only a wheel is built (`uv build backend --wheel`), after `pnpm --filter ivlia-frontend run build`. An sdist would not contain the built SPA.
- No public registry: the wheel lives only in the GitHub release.

## Provenance

- `actions/attest` creates a SLSA build provenance attestation for the wheel, signed with Sigstore's public-good instance and stored by GitHub.
- The same bundle is attached as `<wheel>.sigstore.json`, so it can be checked offline, and so OpenSSF Scorecard's Signed-Releases check sees a signature on each release.

## Install and verify

Only tagged releases are installed for use, never `main`.

```sh
gh release download vX.Y.Z --repo rlopc/ivlia --pattern '*.whl*'
gh attestation verify ivlia-X.Y.Z-py3-none-any.whl --repo rlopc/ivlia \
  --signer-workflow rlopc/ivlia/.github/workflows/release.yml
uv tool install ./ivlia-X.Y.Z-py3-none-any.whl
```

- `gh attestation verify` checks that the wheel's digest matches an attestation made by this repository's release workflow (`--signer-workflow`). Offline: add `--bundle ivlia-X.Y.Z-py3-none-any.whl.sigstore.json`.
- `uv tool install` exposes `ivlia` and `ivlia-server`. Installed from a wheel, PEP 610 records `archive_info`, so it starts as the use installation ([backend.md](backend.md#configuration)).
- To try a release without touching `~/.local`, the real installation or the system keychain, set `UV_TOOL_DIR` and `UV_TOOL_BIN_DIR` to a folder inside `.dev/`, `IVLIA_HOME` to a temporary folder and `IVLIA_ENV=dev`, which never uses the keychain.
- The release is created by release-please and then gets its assets. If GitHub's immutable releases are turned on, uploading to a published release fails: `publish` would then need release-please to create a draft and publish it at the end.
