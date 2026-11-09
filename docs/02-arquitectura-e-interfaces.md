# ivlia · 02 Arquitectura e interfaces

Nov 8, 2026 · @rlopc

ivlia combina Clean Architecture y arquitectura hexagonal: el dominio y los casos de uso no dependen de ninguna tecnología concreta, y todo lo que está fuera (modelos, bases de datos, interfaces, herramientas) se conecta mediante puertos.

## Arquitectura

### Principios

- Abstracción solo en fronteras reales: existe una lista cerrada de puertos y lo que no esté en ella es código concreto. Puertos: LLM, Embedder, Reranker, VectorStore, GraphStore, Tool, Memory, Approval, Transcript y Extractor. La lista se amplía, con un ADR, cuando llegue la voz (texto a voz y reconocimiento de fonemas).
- Cada puerto tiene tests de contrato que cualquier adaptador debe pasar.
- Las dependencias van siempre hacia dentro: los adaptadores dependen de la aplicación, la aplicación del dominio, y el dominio no depende de ninguna otra capa ni tecnología. Lo comprueba una herramienta en CI (import-linter en Python, eslint-plugin-boundaries en TypeScript).
- El desarrollo de ivlia es independiente de su ejecución real: no comparten configuración ni datos (ver «09 IA en el desarrollo»).

### Estructura del repositorio (monorepo)

- `backend/`: paquete Python `ivlia`, con FastAPI (REST y SSE). Contiene el dominio, la aplicación, los adaptadores y la CLI (subpaquete `ivlia.cli`), que se distribuyen juntos.
- `frontend/`: web en React, Vite y TypeScript, como SPA.
- `docs/`: documentación del proyecto.
- `openspec/`: especificaciones vigentes y cambios propuestos (ver «09 IA en el desarrollo»).
- `AGENTS.md`, `CLAUDE.md` y `.claude/`: instrucciones y configuración para Claude Code (ver «09 IA en el desarrollo»).

### Contrato único de la API

El contrato de eventos (token de respuesta, llamada a herramienta, aprobación pendiente, cita, delegación, aviso, error, fin) se define con modelos de Pydantic, que son su fuente. De ellos se exporta un JSON Schema versionado, y la CI falla si el exportado no coincide con el versionado. El contrato se publica en el OpenAPI 3.2 de la API, que describe cada evento del flujo SSE. La CLI usa los modelos de Pydantic y la web consume tipos generados a partir del JSON Schema, para no duplicar esquemas. El transporte es un detalle de la interfaz: la aplicación emite eventos del contrato y el endpoint solo los serializa. Los clientes ignoran los tipos de evento que no conocen y lo registran.

### Orquestación

LangGraph es el framework de orquestación de agentes y forma parte de la capa de aplicación, sin adaptador que copie su API. Un ADR lo documenta. El dominio define su propio estado del agente y la aplicación lo traduce al estado de LangGraph. Una regla de import-linter prohíbe importar `langgraph` fuera de `application/orchestration`. LangGraph aporta las interrupciones para aprobaciones y los checkpoints, que se guardan en SQLite. Los checkpoints guardan solo la ejecución en curso, en un fichero propio, y se podan al terminar el turno. La conversación vive en el historial de la memoria (ver «04 Conocimiento y memoria») y la aplicación construye el estado de LangGraph a partir de él en cada turno.

## Interfaces

La CLI y la web son clientes de la misma API de ivlia. Hay un único camino de entrada, con los mismos permisos y la misma política de datos, salvo los comandos de mantenimiento de la CLI (ver «CLI»). Añadir otra interfaz más adelante, como la voz, no toca el núcleo.

### API

- Escucha solo en el Mac del usuario (localhost) y exige un token local. El token lo genera ivlia al primer arranque y se guarda como cualquier otro secreto (ver «07 Transversales»). Abrirla a la red local exigiría autenticación real.
- La CLI envía el token en una cabecera. La web no llega a verlo: `ivlia web` abre el navegador con un enlace de un solo uso, que la API canjea por una cookie de sesión `HttpOnly` y `SameSite=Strict`. Las dos formas pasan por la misma comprobación. La API rechaza las peticiones cuyo `Host` u `Origin` no sean los suyos, para impedir el DNS rebinding.
- El servidor se arranca con `ivlia-server`, tanto en desarrollo como en la instalación de uso.
- El contrato de eventos (ver «Contrato único de la API», arriba) se considera estable tras dos rebanadas consecutivas sin cambios que rompan compatibilidad (solo se añaden campos opcionales). Un test de compatibilidad lo verifica con ejemplos de la versión anterior.

### CLI

Usa la API para todo salvo `ivlia backup` e `ivlia restore`, que llaman al caso de uso `application/maintenance` y actúan sobre los ficheros locales con los permisos del usuario del sistema. `ivlia backup` hace una copia en caliente consistente; `ivlia restore` exige el servidor parado y lo comprueba con un fichero de bloqueo. Una regla de import-linter limita `ivlia.cli` a importar el contrato, la configuración y `application/maintenance`.

Tiene dos modos:

- Chat interactivo: `ivlia chat`.
- Comandos sueltos, que sirven en scripts: `ivlia ask "..."`, `ivlia web`, `ivlia reindex`, `ivlia memory list`. La administración (reindexar, ver el registro) vive en estos comandos y no en el chat.

### Web

Usa Tailwind, shadcn/ui y assistant-ui, con TanStack Query, React Router y Zod. La sirve la propia API, en el mismo origen; en desarrollo, el servidor de Vite reenvía las peticiones a la API. La primera versión tiene solo el chat:

- Respuesta en directo.
- Citas con su nivel de confianza.
- Aprobaciones de acciones.
- Resumen de la delegación entre agentes.

Después se añaden, en rebanadas finas, la revisión de memoria, el registro de acciones, el grafo de conocimiento (con Cytoscape.js) y el visor de trazas.

## Fuentes

Consultadas el 9 de noviembre de 2026.

- [LangGraph: Persistence](https://docs.langchain.com/oss/python/langgraph/persistence): parcial (checkpoints frente a almacén). Respalda: los checkpoints son estado de corto plazo y se podan.
- [langgraph-checkpoint-sqlite en PyPI](https://pypi.org/project/langgraph-checkpoint-sqlite/) y [su código fuente](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py): parcial (configuración y tablas). Respalda: checkpoints en un fichero SQLite local.
- [FastAPI: Server-Sent Events](https://fastapi.tiangolo.com/tutorial/server-sent-events/): resumen de búsqueda. Respalda: SSE nativo en FastAPI desde la 0.135.
- [Speakeasy: SSE en OpenAPI](https://www.speakeasy.com/openapi/content/server-sent-events), [Swagger: OpenAPI 3.2.0](https://swagger.io/blog/swagger-launches-support-for-openapi-3-2-0/) y [Redocly: OpenAPI 3.2](https://redocly.com/blog/openapi-3-2): resumen de búsqueda. Respalda: OpenAPI 3.2 describe flujos SSE con `itemSchema`.
- [LangGraph Agent Server: streaming](https://docs.langchain.com/langsmith/streaming), [AI SDK: stream protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol), [Anthropic: streaming](https://platform.claude.com/docs/en/api/messages-streaming), [OpenAI Realtime con WebSocket](https://developers.openai.com/api/docs/guides/realtime-websocket), [MCP: transportes](https://modelcontextprotocol.net/specification/latest/basic/transports), [Render](https://render.com/articles/sse-vs-websockets-llm-streaming) y [Ably](https://ably.com/topic/websockets-vs-sse-ai-chat): resumen de búsqueda. Respalda: SSE para chat en streaming y WebSocket para tiempo real bidireccional.
