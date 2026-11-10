# API

The HTTP API of `ivlia-server`, in `ivlia.api`. Design: [docs/02](../02-arquitectura-e-interfaces.md) ("Contrato único de la API", "API"). The package around it: [backend.md](backend.md).

## Contract

- The events streamed by the chat are Pydantic models in `ivlia.contract.events`, a union discriminated on `type`. Phase 0 has `token` (`text`), `end` and `error` (`message`); each slice adds its own.
- Request and response bodies the clients share also live in `ivlia.contract` (`ChatRequest`, `SessionLink`), because the CLI imports only the contract.
- Fields with a default, such as `type`, are marked required in the exported schema, because they are always sent (`json_schema_serialization_defaults_required`).
- Tolerant reader: clients ignore event types they do not know and log them. The contract is considered stable after two consecutive slices without breaking changes, that is, with only optional fields added ([docs/02](../02-arquitectura-e-interfaces.md)).

## Export

- `just contract` writes `backend/schemas/events.schema.json` (JSON Schema 2020-12, serialization mode) and `backend/schemas/openapi.json`, then generates the frontend's types and validator from the schema. All are generated, versioned and excluded from Prettier.
- A test fails if either file differs from what the code generates. It was checked to fail after changing a model or a route without exporting again.
- The OpenAPI document is built as for the use installation, without real settings or secrets. Its `info.version` is the package version.

## Frontend types and validator

`frontend/scripts/generate-contract.ts` (run by `just contract`) writes `frontend/src/contract/` from a copy of `events.schema.json`:

- `events.ts`: TypeScript types from json-schema-to-typescript, a union discriminated on `type` (`ApiEvent`, not `Event`, which the DOM already names). Unknown fields are left out of the types; the validator still accepts them.
- `validate-event.js`: a standalone Ajv validator (`ajv/dist/2020`, `discriminator: true`), with no run-time dependency on Ajv; `validate-event.d.ts` types it as a guard for `ApiEvent`.
- The copy is adjusted first: `discriminator.mapping` is removed (Ajv does not support it), `type: "object"` is added at the root (Ajv's strict mode wants it with `discriminator`), and property titles are removed (they would become one type alias per field).
- The files carry a "Generated ... Do not edit" header and are excluded from Prettier, ESLint and coverage. `pnpm run contract:check`, in `just check`, regenerates in memory and fails if a versioned file differs, so a schema change without `just contract` fails the check.
- Zod is not used for the contract ([decision map](../decisions/README.md)).

## OpenAPI

- Version 3.2.0 (`app.openapi_version`). The SSE response of `POST /api/chat` uses `itemSchema`; FastAPI fills its `data` with `contentMediaType: application/json` and the event union as `contentSchema`.
- A test validates the document with openapi-spec-validator as 3.2. The validator does not follow `$ref` inside `contentSchema`, so another test checks that every target of the union's `discriminator.mapping` exists.
- `/openapi.json` is served in every installation. Swagger UI (`/docs`, loaded from a CDN) only in the dev installation; it renders the 3.2 document, `POST /api/chat` included (checked 2026-11-10). ReDoc is off.

## Endpoints

All routes live under `/api`; every other path belongs to the SPA ([same origin](#same-origin-and-dev-origin)).

| Route | Auth | Answer |
| --- | --- | --- |
| `GET /api/health` | none | `{"status": "ok"}` |
| `POST /api/chat` | token or session | SSE stream of contract events for `{"message": "..."}` (non-empty) |
| `POST /api/session/link` | token only | `SessionLink`: a one-time link to open the web |
| `GET /api/session?code=...` | the one-time code | `303` to `/` with the session cookie |

The chat endpoint only serializes the events of the `Chat` use case: `token` events, then `end`. If the reply fails, the stream ends with `error` instead of `end`, with a generic message; the details go to the log.

## Same origin and dev origin

- FastAPI serves the built SPA from the package (`ivlia.api.spa`): `vite build` writes it to `backend/src/ivlia/api/static/` (gitignored). `/assets/*` are its files, known top-level files (the favicon) are served by name, and any other non-API path gets `index.html`. A path never reaches the disk outside that folder (tested with encoded `..`). Unknown `/api` paths are 404.
- Without a built SPA (dev with Vite, backend tests), FastAPI serves only the API.
- SPA responses carry a strict `Content-Security-Policy` (`default-src 'self'`, `connect-src 'self'`, `object-src 'none'`, `frame-ancestors 'none'`, among others): the page cannot reach any other origin. The end-to-end test checks that no request leaves the origin and that the policy reports no violation.
- Development: Vite (`http://localhost:5173`) proxies `/api` to the API with `changeOrigin: true`. The proxy rewrites only `Host`, to the API's own, which the Host allowlist accepts; `Origin` stays the dev origin, which only the dev installation allows. Adding `localhost:5173` to the Host allowlist instead would widen it for nothing.
- `web_origin` (`ivlia.config`): where the browser opens the web. In use, the API itself; in dev, `dev_origin`. One-time links point there, so the session cookie belongs to the origin that uses it; the proxy passes `Set-Cookie` and the relative `303` to `/` unchanged.

## Listening and port

- Only `127.0.0.1` ([backend.md](backend.md#server)). Opening the API to the network would need real authentication ([docs/02](../02-arquitectura-e-interfaces.md)).
- Port 8765 in the use installation and 8766 in dev, configurable with `port`.

## Host and Origin

`HostOriginGuard`, an ASGI middleware in `api/guards.py`, runs before authentication and answers 403:

- `Host` must be `127.0.0.1:<port>` or `localhost:<port>`. This blocks DNS rebinding.
- `Origin`, when present, must be `http://127.0.0.1:<port>` or `http://localhost:<port>`; in the dev installation also `dev_origin` (default `http://localhost:5173`, the Vite server). `null` and every other origin are rejected.
- A request without `Origin`, such as the CLI's, is not rejected for it. The token header and the `SameSite=Strict` cookie cover cross-site requests, and the Host check covers DNS rebinding.
- Starlette's `TrustedHostMiddleware` is not used: it answers 400 and does not check `Origin`.

## Token

- The API token is a secret generated at first start ([backend.md](backend.md#secrets)).
- The CLI sends `Authorization: Bearer <token>`. The API compares it with `secrets.compare_digest`. A missing or wrong token gets 401 with `WWW-Authenticate: Bearer`.
- The OpenAPI document declares the Bearer scheme and the session cookie as alternatives.

## Web session

`api/sessions.py`. The web never sees the token.

- `POST /api/session/link`, with the token, mints a one-time code (256 random bits) valid for 60 seconds and returns its link, on the [web origin](#same-origin-and-dev-origin). `ivlia web` opens it in the browser, and accepts only a link to that origin's `/api/session`.
- `GET /api/session?code=...` exchanges the code, once, for a new session and sets the session cookie: `HttpOnly`, `SameSite=Strict`, `Path=/`, `Max-Age` of 7 days.
- The cookie is `ivlia_session` in the use installation and `ivlia_session_dev` in dev. Both run on `127.0.0.1` and cookies ignore the port, so one shared name would make each installation overwrite the other's session in the same browser.
- No `Secure` attribute: Safari does not keep `Secure` cookies on `http://localhost` (WebKit bug 232088).
- Sessions live 7 days in server memory, so a restart ends every session. A used, expired or unknown code gets 401.
- One check accepts the token or the cookie (`Auth.token_or_session`); minting a link accepts only the token.
- Tests use a fake clock for the 60-second and 7-day limits.

## Status codes

- 401: missing or invalid token or session, or an invalid link code.
- 403: foreign `Host` or `Origin`.
- 422: invalid request body.

## Tracing

- `RequestSpan` (`api/tracing.py`) opens one span per request, response body included, with the method, the path and the status code. It never records the query string, which can hold a link code. On an unhandled exception it records only the exception type.
- FastAPI's built-in telemetry is off (`telemetry=` in `create_app`). Its spans record the query string with only a few cloud signature parameters redacted, and `FASTAPI_OTEL_AUTO_CONFIGURE=true` would add exporters. A test checks that it stays off with that variable set.
