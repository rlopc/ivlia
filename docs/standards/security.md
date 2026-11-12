# Security

Threat model required by [docs/06](../06-datos-y-seguridad.md) ("Seguridad"). Reporting: [SECURITY.md](../../SECURITY.md).

## Assets

- User data, by level 0 (public) to 3 (secret): [docs/06](../06-datos-y-seguridad.md) ("Política de datos"). Real user data never enters this repository.
- Secrets: the API token, model keys and any credential. See [docs/07](../07-transversales.md) ("Configuración").
- The action log: a hash chain in the memory SQLite that records every approval decision ([docs/03](../03-agentes-y-herramientas.md), "Aprobaciones").
- The repository and its supply chain: dependencies, tools, hooks and CI.

## Threats and measures

### Prompt injection in external content

Web pages, documents and tool results can carry instructions.

- Untrusted content is marked as data and cannot trigger write tools without approval; deterministic tests verify it ([docs/03](../03-agentes-y-herramientas.md), "Puerto Tool"). Arrives with the agents (slice 2 onwards).
- Permission levels and approvals: free reads, confirmed writes and commands, blocked dangerous actions; unanswered approvals are rejected ([docs/03](../03-agentes-y-herramientas.md)).
- Until the sandbox for commands exists, no agent runs commands or code ([docs/03](../03-agentes-y-herramientas.md), "Sandbox").

### Malicious local web pages and DNS rebinding

- The API listens only on `127.0.0.1` and requires a local token. The CLI sends it in a header ([backend.md](backend.md#cli)); the web gets a one-time link exchanged for an `HttpOnly`, `SameSite=Strict` cookie. The API rejects requests whose `Host` or `Origin` is not its own ([docs/02](../02-arquitectura-e-interfaces.md), "API"). Details and tests: [api.md](api.md#host-and-origin), [api.md](api.md#web-session).
- The Vite dev origin is allowed only in the dev installation; the Vite proxy keeps the browser's `Origin` and rewrites only `Host` ([api.md](api.md#same-origin-and-dev-origin)).
- The SPA has a strict Content-Security-Policy: it can load and connect only to its own origin, and cannot be framed. Its third-party UI library includes a cloud client that ivlia never uses; the policy would block it, and the end-to-end test fails on any request to another origin ([api.md](api.md#same-origin-and-dev-origin)).

### Data leaks to models, logs or the repository

- Data levels: each component declares the maximum level it accepts and the policy blocks the rest; level 3 never goes to models or logs. A secret detector marks and replaces secrets before they are stored or sent ([docs/06](../06-datos-y-seguridad.md)). Arrives with the data layer.
- Secrets live outside the code and the settings file; the development installation never uses the system keyring ([docs/07](../07-transversales.md)). The secrets file has mode `0600` and the installation folder `0700`; a secrets file readable by others stops the start ([backend.md](backend.md#secrets)).
- Logs and traces stay on the Mac and carry no message content by default: content fields and exception messages are removed, frame locals are never logged, spans keep no query strings and no exception messages ([backend.md](backend.md#logs-and-traces)).
- Third-party telemetry that an environment variable could switch on (LangSmith tracing, FastAPI's built-in telemetry and its OTLP auto-configuration) is off in code, with tests ([backend.md](backend.md#third-party-telemetry)).
- Tests never reach the real keychain: `keyring` points at its failing backend in every test ([backend.md](backend.md#tests-and-coverage)).
- gitleaks runs in pre-commit (staged changes) and in `just check` (history). GitHub secret scanning with push protection is enabled. See [repository.md](repository.md#pre-commit).

### Compromised dependencies and tools

- Exact pins, lockfiles and a 7-day cooldown ([README](README.md#versions-policy)).
- `mise.lock` records the checksums of the binaries mise downloads; pre-commit hooks run locally, each with a tool from a lockfile ([repository.md](repository.md#pre-commit)). pre-commit and its dependencies are locked with hashes in `uv.lock`. `just setup` and CI install the tools with `mise install --locked`. mise itself is verified against its signed checksums by mise-action in CI.
- GitHub Actions pinned by SHA, with minimal permissions, and audited with zizmor and actionlint ([ci.md](ci.md#rules-for-every-workflow)).
- Releases: the wheel has a SLSA build provenance attestation and its Sigstore bundle; `gh attestation verify` checks it before installing ([release.md](release.md#install-and-verify)). The release workflow uses no cache, and acts through a GitHub App token limited to this repository, with contents and pull requests, short-lived and revoked after each job ([release.md](release.md#credential)).
- CodeQL (Python, JavaScript/TypeScript, workflows), Dependabot version and security updates with a 7-day cooldown, `pnpm audit` in CI, and OpenSSF Scorecard ([ci.md](ci.md)).

### The AI agent acting outside its scope

- Claude Code permissions (allow, ask, deny) and the Bash sandbox: writes only in the project, network only to allowed domains, no access to the use installation folder or secret folders ([ai-development.md](ai-development.md#claude-code-permissions)).
- Permission rules match command text and can be bypassed. The real guards are the sandbox and the GitHub ruleset on `main` (no force push, no deletion, PR required, no bypass) ([repository.md](repository.md#github)). The user reviews every PR and decides when it merges: Claude merges only when asked, after the user approves the command, and with auto-merge, so GitHub merges only when the required checks pass ([ai-development.md](ai-development.md#github-access)).
- The sandbox does not cover the Read, Edit, Write and web tools, nor hooks; permission rules are the only guard for them.
- Commands outside the allow list ask, and Claude cannot leave the sandbox; only `just setup`, `.claude/bin/gh-repo` and `git push` run outside it, through the permission rules ([ai-development.md](ai-development.md#bash-sandbox)). `gh-repo` and pushes use a token limited to this repository; every GitHub write asks ([ai-development.md](ai-development.md#github-access)).
- The sandbox does not stop a command from using the system keychain. A run from the repository can only be the dev installation, which never uses the keychain: the start guard refuses anything else ([backend.md](backend.md#configuration)).
- The reviewer agent reviews every branch before the user, with attention to secrets, permissions and network.

## Reporting

Private vulnerability reporting is enabled on GitHub ([SECURITY.md](../../SECURITY.md)).
