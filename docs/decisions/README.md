# Decisions

The decision map lists the project's technical decisions with their status, when to revisit them and where they are explained. The process is in the [standards index](../standards/README.md#decisions-and-adrs).

- **Final**: decided; changing it needs a new decision, and an ADR if the old one had one.
- **Provisional**: in use, with a known condition to revisit.

ADRs live in [adr/](adr/), numbered, in the MADR minimal format. They are immutable: a later ADR replaces an old one and the old one is marked "superseded by".

## Map

| Decision | Status | Revisit when | Link |
| --- | --- | --- | --- |
| LangGraph orchestrates the agents, inside the application layer, with no adapter | Final | — | [ADR 0001](adr/0001-langgraph-orchestration.md) |
| Domain agent state, translated to LangGraph state on each turn | Provisional | Slice 5, when interrupts arrive | [docs/10](../10-plan-y-pendientes.md) |
| Type checker: mypy strict, not ty | Provisional | When ty matures with FastAPI and LangGraph | [backend.md](../standards/backend.md#typing), [docs/10](../10-plan-y-pendientes.md) |
| OpenAPI 3.2, not the 3.1 fallback | Final | — | [api.md](../standards/api.md#openapi) |
| httpx2 as the HTTP client, with no classic httpx | Final | — | [backend.md](../standards/backend.md#tests-and-coverage) |
| Session cookie without `Secure` | Final | When Safari keeps `Secure` cookies on `http://localhost` | [api.md](../standards/api.md#web-session) |
| LangSmith tracing and FastAPI's built-in telemetry off in code | Final | — | [backend.md](../standards/backend.md#third-party-telemetry) |
| A run from a source folder starts only as the dev installation (`IVLIA_ENV=dev` and `IVLIA_HOME`) | Final | — | [backend.md](../standards/backend.md#configuration) |
| One session cookie name per installation (`ivlia_session`, `ivlia_session_dev`) | Final | — | [api.md](../standards/api.md#web-session) |
| An existing database with pending migrations does not start | Provisional | Slice 2, when backups arrive | [backend.md](../standards/backend.md#migrations) |
| pre-commit, not prek | Provisional | When prek reaches 1.0 | [repository.md](../standards/repository.md#pre-commit) |
| mise lockfile (`mise.lock`) enabled | Final | — | [repository.md](../standards/repository.md#tool-versions) |
| pnpm pinned in `mise.toml`, not in `packageManager`, so `pnpm-lock.yaml` is one YAML document that the dependency graph reads | Provisional | When GitHub's dependency graph reads two-document pnpm lockfiles | [repository.md](../standards/repository.md#tool-versions) |
| No Zod for the contract: generated TypeScript types and an Ajv validator | Provisional | When the first form arrives | [docs/plan/phase-0.md](../plan/phase-0.md) (step 4) |
