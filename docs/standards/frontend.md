# Frontend

The SPA in `frontend/`: React with TypeScript, built with Vite, served by FastAPI on the API's own origin. Design: [docs/02](../02-arquitectura-e-interfaces.md) ("Web"). The API and the contract it consumes: [api.md](api.md).

## Project

- A package of the root pnpm workspace (`ivlia-frontend`, [frontend/package.json](../../frontend/package.json)), with the single root `pnpm-lock.yaml`. Dependencies are pinned to exact versions; adding or upgrading one needs the user's confirmation.
- TypeScript 6.0 with `strict` in its three projects: `tsconfig.app.json` (`src/`), `tsconfig.node.json` (configs and `scripts/`) and `tsconfig.e2e.json` (`e2e/`, with the DOM types for code that runs in the page). TypeScript 7 is not used yet: typescript-eslint supports `<6.1`.
- `@/` is `src/`, in `tsconfig.json`, `tsconfig.app.json`, `vite.config.ts` and `components.json`.
- Tailwind 4 through `@tailwindcss/vite`. shadcn (style `base-nova`, Base UI primitives) writes its components to `src/components/ui/` and its helper to `src/shared/lib/utils.ts`.
- `components.json` keeps `iconLibrary: "lucide"`, but `lucide-react` is not installed: a `shadcn add` of a component with icons adds it, and that is a new dependency the user confirms.
- Scripts: `contract`, `contract:check`, `lint`, `knip`, `test`, `build` (`tsc -b`, then `vite build`), `e2e`. `just check-frontend` runs all but `contract`, which `just contract` runs ([repository.md](repository.md)).

## Layout and boundaries

By feature, in `frontend/src/`:

| Folder | Holds | May import |
| --- | --- | --- |
| `app/` | entry, routes and providers | everything below |
| `features/<name>/` | a feature's pages and components | its own `adapter/` and `model/`, `shared/`, `components/ui/`, `api/`, `contract/` |
| `features/<name>/adapter/` | the bridge to a third-party UI library | its feature's `model/`, `shared/`, `components/ui/`, `api/`, `contract/` |
| `features/<name>/model/` | pure logic | its feature's `model/`, `contract/`; no React |
| `api/` | the only code that uses the network | `contract/` |
| `shared/`, `components/ui/` | code used by more than one feature; shadcn components | each other |
| `contract/` | generated types and validator ([api.md](api.md#frontend-types-and-validator)) | nothing |

eslint-plugin-boundaries enforces it (`boundaries/dependencies` in [eslint.config.js](../../frontend/eslint.config.js), default `disallow`):

- Features do not import each other; nothing imports `app/`.
- External packages are allowed, except: only `features/chat/adapter/` imports `@assistant-ui/*`, and a `model/` imports no React.
- Each rule was checked to fail with a forbidden import.

An entities layer (as in Feature-Sliced Design) is added only if it appears.

## Lint, types and format

- ESLint flat config: `@eslint/js` recommended, typescript-eslint `strictTypeChecked` with `projectService`, eslint-plugin-react-hooks 7 (`recommended`, which includes the React Compiler rules) and boundaries. Imports are resolved with `eslint-import-resolver-typescript`.
- `src/components/ui/` keeps the basic rules but not the type-aware ones, because the shadcn CLI writes it. A component that is modified moves out of `ui/`. `tsc` and Prettier still cover it.
- Prettier from the root, with the root `.prettierignore`: run it from the repository root, never from `frontend/`, or the generated `src/contract/` is reformatted.
- knip ([frontend/knip.json](../../frontend/knip.json)) finds unused files, exports and dependencies. It ignores the exports of `src/contract/` and `src/components/ui/`, and two files nothing imports yet: the validator's declaration and shadcn's `utils.ts`.
- ESLint ignores `src/contract/`, build output and test reports.

## SSE client

`src/api/chat.ts`: `streamChat(message, signal?)` posts `{"message": ...}` to `/api/chat` and yields contract events.

- `fetch`, then `TextDecoderStream` and eventsource-parser's `EventSourceParserStream`, read with a stream reader.
- It checks the status first (401 means the session ended; it says to run `ivlia web`) and that `Content-Type` is `text/event-stream`.
- Each event is validated with the generated Ajv validator. Tolerant reader: an unknown `type` (Ajv's `discriminator` error `mapping`) is skipped and logged with a fixed message, without its content; any other invalid event is an error.
- Errors are `ApiError` with a message shown as is, also when the connection fails in the middle of the stream. A cancellation (`signal`) passes through unchanged. When the caller stops reading, the response is closed.
- Requests use the session cookie (same origin); the web never sees the token.

## Chat UI

- `features/chat/model/messages.ts`: the chat state as pure functions over contract events (`userMessage`, `pendingReply`, `applyEvent`, `failReply`, `finishReply`). A reply whose stream ends without `end` or `error` is marked incomplete. The `switch` on event types has no `default`, so TypeScript fails to compile if a type is not handled.
- `features/chat/adapter/`: the only code that knows assistant-ui. `useChatRuntime` wraps the state in `useExternalStoreRuntime`; `ChatThread` builds the chat from assistant-ui's unstyled primitives (`ThreadPrimitive`, `ComposerPrimitive`, `MessagePrimitive`, `ErrorPrimitive`), styled with Tailwind. Replacing assistant-ui means replacing this folder.
- assistant-ui's styled registry components are not used, because they import assistant-ui outside the adapter.
- `features/health/`: the API status in the header, with TanStack Query.
- Routes (React Router, declarative mode): `/` is the chat; any other path is a not-found page.

## Tests and coverage

- Vitest with jsdom and React Testing Library; tests sit next to the code (`*.test.ts(x)`).
- MSW (`src/test/server.ts`) fakes the API; an unhandled request fails the test (`onUnhandledFrame: "error"`). MSW's `sse` handler works only in browsers, so SSE responses are `http` handlers that return a `ReadableStream` (`src/test/sse.ts`).
- jsdom has no `ResizeObserver`, which assistant-ui needs: `src/test/setup.ts` stubs it.
- Coverage (v8): 100 % for `features/*/model/`, 95 % for the rest. Excluded: tests, test helpers, `src/contract/`, `src/components/ui/` and `src/app/main.tsx`, which only mounts the app.

## End-to-end and accessibility

- Playwright ([frontend/playwright.config.ts](../../frontend/playwright.config.ts)) with Chromium, against the built SPA served by FastAPI, as in use. `just setup` installs the browser.
- `webServer` starts `ivlia-server` on port 8767 with a temporary `IVLIA_HOME`, a random token per run in `IVLIA_API_TOKEN`, and `IVLIA_DEV_ORIGIN` set to the server itself, so one-time links point at it. The dev installation's data is never touched.
- `e2e` serves the SPA as last built: run `pnpm run build` first (`just check-frontend` does). The temporary folder is removed at the end (`e2e/teardown.ts`).
- The test mints a link with the token, opens it, sends a message and sees the hello-world answer. It also checks that axe finds no violations, that no request leaves the page's origin, and that no `securitypolicyviolation` event fires.

## Development

- `just dev-web` runs `ivlia-server --reload` and Vite together. Vite listens on `http://localhost:5173` (`strictPort`) and proxies `/api` to the API with `changeOrigin: true` ([api.md](api.md#same-origin-and-dev-origin)).
- In the dev installation, `ivlia web` opens Vite; always browse `localhost`, not `127.0.0.1`, because cookies are per host.
