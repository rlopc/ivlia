# Backend

The Python package `ivlia` in `backend/`: domain, application, adapters, API and (from step 3) the CLI. Design: [docs/02](../02-arquitectura-e-interfaces.md). The HTTP API has its own page: [api.md](api.md).

## Project

- A simple uv project (not a workspace) with a src layout: [backend/pyproject.toml](../../backend/pyproject.toml), `backend/uv.lock`, and `backend/.python-version` (Python 3.14).
- Build backend: `uv_build`. `[tool.uv]` sets `required-version` and `exclude-newer = "7 days"` (the cooldown, [README](README.md#versions-policy)).
- Dependencies are pinned to exact versions in `pyproject.toml`. Runtime and the `dev` group are listed there; `uv.lock` holds the full tree.
- Every command goes through `uv run --locked` or `uv sync --locked`, so nothing rewrites `uv.lock` by accident. Adding or upgrading a dependency needs the user's confirmation.
- `LICENSE` lives at the repository root, outside the package, so the wheel does not include it yet. Step 6 (release) resolves it.

## Layout and layers

Layer first, in `backend/src/ivlia/`:

| Package | Holds | May import |
| --- | --- | --- |
| `domain/` | `agents`, `memory`, `knowledge`, `models`, `tools`, `data_policy`: entities, rules and ports | nothing outside the domain, no framework |
| `contract/` | Pydantic models of the events and request bodies shared with the clients | `domain` |
| `config/` | installation identity, settings, secrets | `contract`, `domain` |
| `application/` | use cases (`chat`), `orchestration` (LangGraph), `maintenance` | `config`, `contract`, `domain` |
| `api/`, `adapters/`, `cli/` | HTTP API; port implementations, logs, traces, SQLite; command line | the layers below, not each other |
| `bootstrap.py` | the composition root: builds everything in start order | everything |
| `server.py` | `ivlia-server` | `bootstrap` and the layers below, never `adapters` directly |

Import rules, checked by import-linter (`[tool.importlinter]` in `pyproject.toml`, `include_external_packages = true`):

- Dependencies point inwards, in the order of the table (a `layers` contract). `api`, `adapters` and `cli` are independent of each other.
- The domain imports no framework (a `forbidden` contract listing the runtime dependencies).
- Only `bootstrap` imports `adapters`; `server` reaches them only through it.
- `langgraph`, `langsmith` and `langchain_core` are imported only in `application/orchestration` ([ADR 0001](../decisions/adr/0001-langgraph-orchestration.md)).
- From step 3: `ivlia.cli` imports only `contract`, `config` and `application/maintenance`.

Each contract was checked to fail when its rule is broken.

## Ports and contract tests

- Ports are typed `Protocol`s in the domain module they belong to (the LLM port is `domain/models/llm.py`). Only the ports of the closed list in [docs/02](../02-arquitectura-e-interfaces.md) exist, and each one is created in the slice that uses it. Phase 0 has only the LLM port.
- Ports are `runtime_checkable`, so a contract test can check that an adapter implements them.
- Each port has a contract base class in `backend/tests/port_contracts/`. An adapter's test subclasses it and provides the `adapter` fixture. Base class names do not start with `Test`, so pytest collects them only through subclasses.
- Phase 0 has one adapter: `adapters/hello_world_llm.py`, which always streams "Hello, world!".

## Typing

- mypy strict with the `pydantic.mypy` plugin, over `src` and `tests` (`[tool.mypy]`). Test helpers are imported from `tests/` (`mypy_path`, `explicit_package_bases`), as pytest does.
- The domain uses standard `dataclass`es and enums, not Pydantic.
- Type exceptions are allowed only in adapters and `application/orchestration`, as narrow as possible, each with a comment. There are none today.

## Lint and format

ruff formats and lints (`[tool.ruff.lint]`); it runs as a pre-commit hook, and the PostToolUse hook runs it after each edit by Claude ([ai-development.md](ai-development.md#hooks)). Line length is left to the formatter (`E501` ignored). In tests, `S101` (assert) and `PLR2004` (literal values) are ignored.

| Family | Why |
| --- | --- |
| `F`, `E`, `W` | Pyflakes and pycodestyle: real errors and basic style. |
| `I` | Sorted imports. |
| `N` | PEP 8 naming. |
| `UP` | Modern syntax for the target Python. |
| `B` | Likely bugs (bugbear). |
| `A` | No shadowing of builtins. |
| `C4`, `PERF`, `PIE`, `SIM`, `RET` | Simpler, faster, more direct code. |
| `S` | Security issues (bandit). |
| `BLE`, `TRY` | No blind `except`; clear exception handling. |
| `DTZ` | No naive datetimes. |
| `PTH` | `pathlib` instead of `os.path`. |
| `TC` | Imports used only for typing go in `TYPE_CHECKING` blocks. |
| `ASYNC` | Blocking calls inside async code. |
| `PT` | pytest style. |
| `ARG` | Unused arguments. |
| `PL` | Pylint checks. |
| `G`, `LOG` | Correct use of `logging`. |
| `T20` | No `print`. |
| `RUF` | ruff's own checks. |

Not used: `FBT` (boolean arguments) and `ERA` (commented-out code).

`TC` and run-time annotations: Pydantic, FastAPI and LangGraph read annotations when the code runs, so their imports must stay real. `runtime-evaluated-base-classes` and `runtime-evaluated-decorators` cover Pydantic models and FastAPI routes. Elsewhere a real import keeps a `# noqa: TC00x` with the reason (for example the LangGraph state in `application/orchestration/graph.py`).

`# noqa` is always narrow (one code, one line) and carries its reason.

## Tests and coverage

- pytest (`[tool.pytest]`): `importlib` import mode; `pythonpath = ["tests"]` for helpers such as `api_client.py` and `port_contracts/`.
- Every warning is an error. The only exception is a known deprecation inside `langsmith`, ignored by message and module.
- The `langsmith` pytest plugin, which comes with `langgraph`, is disabled (`-p no:langsmith_plugin`).
- `tests/conftest.py` removes every `IVLIA_*` variable before each test and points `keyring` at its failing backend, so no test reaches the real keychain.
- API tests use FastAPI's `TestClient`, which runs on httpx2 (Starlette 1.10). Classic httpx is not a dependency of ivlia; it arrives only through `langchain-core`.
- Async code is tested with `asyncio.run` inside synchronous tests; there is no async pytest plugin.
- coverage.py runs once and reports twice (`just check-backend`): the domain at 100 %, the rest at 95 %. Branch coverage is on.

## Configuration

Design: [docs/07](../07-transversales.md) ("Configuración"). Code: `ivlia.config`.

- Installation identity comes only from the environment, because the settings file lives inside the installation folder:
  - `IVLIA_ENV`: `use` (default) or `dev`.
  - `IVLIA_HOME`: the installation folder, an absolute path. Default: `~/Library/Application Support/ivlia`.
  - In the repository, `just` and mise set `IVLIA_ENV=dev` and `IVLIA_HOME=<repo>/.dev` ([justfile](../../justfile), `[env]` in [mise.toml](../../mise.toml)). mise overrides these variables for commands that run through its shims, such as `uv` inside the repository.
- Start guard: if `IVLIA_HOME` is not set and the package was installed from a folder (PEP 610 `direct_url.json` with `dir_info`, as the editable install of `backend/` is), ivlia does not start and says why. A release installed from a wheel (`archive_info`) starts with the default folder.
- Settings: defaults in code (`ivlia.config.settings.Settings`), then `IVLIA_HOME/config.toml`, then `IVLIA_*` environment variables, with the environment winning. Unknown keys are errors. An invalid value stops the start with a message that names the setting and the value.
- Settings today: `port` (default 8765 in use, 8766 in dev), `dev_origin`, `keyring_service` (default `ivlia`), `log_content` (default off) and `trace_console` (default off).

## Secrets

`ivlia.config.secrets`. Values are `SecretStr`, so they are hidden in reprs and logs.

- Lookup order: the `IVLIA_<NAME>` variable, then the system keyring (service `keyring_service`), then `IVLIA_HOME/secrets.json`.
- The dev installation never uses the keyring.
- Generated secrets, such as the API token (32 random bytes, URL-safe), are created on first use and stored in the keyring. If the keyring fails, they go to the file.
- The file is written atomically, with mode `0600`. If it is readable by other users or is not a JSON object of strings, ivlia does not start.

## Installation folder

- `bootstrap` creates `IVLIA_HOME` with mode `0700` before anything writes into it.
- It holds `config.toml`, `secrets.json`, `memory.sqlite3` and `logs/` (`ivlia.log`, `traces.jsonl`).

## Migrations

`ivlia.adapters.sqlite.migrations`.

- An own runner, forward only. Each database has a folder of SQL files `NNNN_description.sql`, numbered from 0001 with no gaps, shipped inside the package.
- `PRAGMA user_version` holds the last migration applied. Connections use `autocommit=False`, so each migration and its `user_version` update run in one transaction; a failure rolls both back and stops the start with the file name.
- A new database gets every migration. An existing database with pending migrations does not start, because migrating needs a backup first and backups arrive in slice 2. A database newer than the code does not start either.
- Phase 0 has only the memory database, whose `0001` creates the `installation` table. `bootstrap` writes its one row (id, creation date, version) at first start.

## Logs and traces

Design: [docs/07](../07-transversales.md) ("Observabilidad"). Nothing leaves the Mac: there is no external exporter.

- Code logs through the standard `logging` module. structlog only formats records (`adapters/observability/logs.py`): JSON lines in `IVLIA_HOME/logs/ivlia.log`, rotating at 10 MB with 5 backups, with `trace_id` and `span_id` from the current span.
- Content never reaches the log unless `log_content` is on:
  - The extra fields `content`, `text`, `prompt`, `reply` and `messages` are replaced by `[removed]`.
  - So is what logged exceptions say (message, notes, syntax error line), also inside exception groups, because it can quote the conversation.
  - Frame locals are never logged, even in debug mode.
- With `log_content` on, everything is logged, level 3 data included. Phase 0 has no level 3 data; masking secrets in logs arrives with the secret detector in slice 2 ([docs/10](../10-plan-y-pendientes.md)).
- Log messages are fixed text. Content goes only in the extra fields above, never interpolated into the message.
- Traces: an OpenTelemetry `TracerProvider` (`adapters/observability/traces.py`) that always exports to `IVLIA_HOME/logs/traces.jsonl` (one span per line, rotating through `logging`), and also to the console if `trace_console` is on.
- Spans: one per HTTP request (`api/tracing.py`, without the query string) and one per use case (`chat`). Spans record the exception type, never its message: the SDK's `record_exception` and `set_status_on_exception` are off, and the status is set by hand.

## Third-party telemetry

Both are switched off in code and covered by tests, because an environment variable alone would turn them on:

- LangSmith: `langsmith.configure(enabled=False)` in `application/orchestration/graph.py`. `LANGSMITH_TRACING=true` would otherwise send runs, with the messages, to LangSmith's cloud.
- FastAPI's built-in telemetry: off ([api.md](api.md#tracing)).

## Server

- `ivlia-server` (`[project.scripts]`, `ivlia/server.py`) builds the app with `bootstrap` and runs uvicorn on `127.0.0.1` only, on the configured port.
- uvicorn's logs go to ivlia's JSON log (`log_config=None`), and its access log is off, because request lines carry query strings and so one-time link codes.
- `--reload` restarts on code changes through `ivlia.bootstrap:app_factory`, and only in the dev installation; it is refused before anything is built. `just dev` runs it.
- Known limitation of reload mode: the supervising process and the server process both open the log and trace files, and `RotatingFileHandler` is not safe across processes, so a rotation can lose lines. It affects only the dev installation.
- A start error (`StartupError`: invalid or malformed configuration or secrets file, or a migration problem) prints its message and exits with status 1.
