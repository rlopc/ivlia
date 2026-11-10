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

- The API listens only on `127.0.0.1` and requires a local token. The CLI sends it in a header; the web gets a one-time link exchanged for an `HttpOnly`, `SameSite=Strict` cookie. The API rejects requests whose `Host` or `Origin` is not its own ([docs/02](../02-arquitectura-e-interfaces.md), "API"). Details and tests: [api.md](api.md#host-and-origin), [api.md](api.md#web-session).

### Data leaks to models, logs or the repository

- Data levels: each component declares the maximum level it accepts and the policy blocks the rest; level 3 never goes to models or logs. A secret detector marks and replaces secrets before they are stored or sent ([docs/06](../06-datos-y-seguridad.md)). Arrives with the data layer.
- Secrets live outside the code and the settings file; the development installation never uses the system keyring ([docs/07](../07-transversales.md)). The secrets file has mode `0600` and the installation folder `0700`; a secrets file readable by others stops the start ([backend.md](backend.md#secrets)).
- Logs and traces stay on the Mac and carry no message content by default: content fields and exception messages are removed, frame locals are never logged, spans keep no query strings and no exception messages ([backend.md](backend.md#logs-and-traces)).
- Third-party telemetry that an environment variable could switch on (LangSmith tracing, FastAPI's built-in telemetry and its OTLP auto-configuration) is off in code, with tests ([backend.md](backend.md#third-party-telemetry)).
- Tests never reach the real keychain: `keyring` points at its failing backend in every test ([backend.md](backend.md#tests-and-coverage)).
- gitleaks runs in pre-commit (staged changes) and in `just check` (history). GitHub secret scanning with push protection is enabled. See [repository.md](repository.md#pre-commit).

### Compromised dependencies and tools

- Exact pins, lockfiles and a 7-day cooldown ([README](README.md#versions-policy)).
- Binaries installed by mise are verified with the checksums in `mise.lock`; pre-commit hooks are pinned by revision or run locally from lockfiles ([repository.md](repository.md#pre-commit)). Known gap: pipx tools have no checksum ([repository.md](repository.md#known-limitations-and-risks-to-revisit)).
- GitHub Actions pinned and audited with zizmor and actionlint. CodeQL, Dependabot and OpenSSF Scorecard arrive in step 5.

### The AI agent acting outside its scope

- Claude Code permissions (allow, ask, deny) and the Bash sandbox: writes only in the project, network only to allowed domains, no access to the use installation folder or secret folders ([ai-development.md](ai-development.md#claude-code-permissions)).
- Permission rules match command text and can be bypassed. The real guards are the sandbox and the GitHub ruleset on `main` (no force push, no deletion, PR required, no bypass) ([repository.md](repository.md#github)). The user reviews and merges every PR.
- The sandbox does not cover the Read, Edit, Write and web tools, nor hooks; permission rules are the only guard for them.
- Commands outside the allow list ask, and Claude cannot leave the sandbox; only `just setup` runs outside it, after the user approves ([ai-development.md](ai-development.md#bash-sandbox)).
- The sandbox does not stop a command from using the system keychain. A run from the repository with `IVLIA_HOME` set but without `IVLIA_ENV=dev` counts as the use installation and stores its API token there. Manual runs during development always set `IVLIA_ENV=dev`.
- The reviewer agent reviews every branch before the user, with attention to secrets, permissions and network.

## Reporting

Private vulnerability reporting is enabled on GitHub ([SECURITY.md](../../SECURITY.md)).
