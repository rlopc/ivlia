# ivlia · 10 Plan y pendientes

Nov 8, 2026 · @rlopc

## Plan de construcción

ivlia se construye en rebanadas verticales finas, cada una supervisable y con una prueba que demuestra que funciona. Estas son las siete primeras, en orden.

1. **Estructura completa (fase 0).** Monorepo con `backend/` (módulos de agentes, memoria, conocimiento, modelos, herramientas y política de datos, con el puerto LLM y su adaptador de hola mundo (el resto de puertos de la lista cerrada se crean en la rebanada que los usa), y la CLI como subpaquete), `frontend/` y `docs/`. Incluye `just`, CI completa, configuración en tres capas, mecanismo de migraciones, OpenTelemetry, JSON Schema de eventos con OpenAPI generado, el documento de estándares de «08 Ingeniería y calidad» y la configuración de «09 IA en el desarrollo». Terminada cuando `just check` pasa en CI con todas las comprobaciones activas, y `ivlia ask` y el chat web devuelven una respuesta de hola mundo a través de la API.
2. **Chat central real.** Ollama y LangGraph reales en el agente central, con respuesta en directo, historial de conversación en el SQLite de memoria, checkpoints de la ejecución en curso en un SQLite aparte que se podan al terminar el turno (ver «02 Arquitectura e interfaces»), y enmascarado de secretos: un detector marca como nivel 3 lo que lo parezca y lo sustituye por una marca antes de enviarlo al modelo y de guardarlo en el historial, los checkpoints y los logs (ver «06 Datos y seguridad»); `ivlia backup` e `ivlia restore`. Terminada cuando un test de extremo a extremo con un modelo simulado verifica la secuencia de eventos, la traza se ve en consola, un test prueba que una conversación continúa después de podar sus checkpoints, otro prueba que un secreto escrito en el chat no llega al modelo, a SQLite ni a los logs, y otro prueba la restauración de una copia.
3. **Conocimiento v1.** Corpus de ejemplo y conjunto de preguntas de referencia (ver «04 Conocimiento y memoria»), ingesta de notas en SQLite (FTS5, sqlite-vec y aristas de enlaces), con nivel de datos por carpeta de origen en cada nodo, arista y vector, y exclusión de los fragmentos secretos; `ivlia reindex` y respuestas con citas. Terminada cuando la evaluación de recuperación sobre el conjunto de referencia alcanza el umbral inicial de «07 Transversales», en CI, y un test prueba que un fragmento secreto de una nota no se indexa.
4. **Agente Knowledge y delegación.** El agente Knowledge consulta el grafo de conocimiento y el central le delega, con `@agente` para forzarlo y el evento de resumen de delegación. Terminada cuando un test de extremo a extremo con un modelo simulado verifica que el central delega en Knowledge y que la respuesta llega con citas y con el resumen de delegación.
5. **Aprobaciones y herramientas.** Puerto Tool con lista permitida, niveles de permiso, interrupción de LangGraph, tiempo límite igual a rechazo, registro encadenado por hash, detector de secretos aplicado a los resultados de herramientas antes de que lleguen al modelo, y una herramienta de escritura de prueba que solo existe en desarrollo. Terminada cuando tests deterministas prueban cada nivel de permiso, el tiempo límite, la detección de manipulación del registro y que un secreto en el resultado de una herramienta no llega al modelo.
6. **Web real.** Citas, aprobaciones y resumen de delegación en el chat. Terminada cuando una prueba de Playwright aprueba y rechaza una acción de la herramienta de escritura de prueba contra la API real y MSW cubre los eventos del esquema.
7. **Memoria.** Hechos globales y por tema con nivel de datos, archivado, `ivlia memory list` y comandos para corregir hechos y resolver los dudosos. Terminada cuando tests prueban que un secreto (nivel 3) nunca se guarda, que un hecho nuevo archiva al anterior y que corregir un hecho archiva el original.

Las rebanadas posteriores (agente Code, agente Learning, voz, grafo de conocimiento en base de datos propia) se definen después con el mismo criterio. La primera que conecte un componente que pueda enviar datos fuera del Mac (por ejemplo, modelos externos, asistentes de proyecto, búsqueda en internet o herramientas MCP) incluye el bloqueo por nivel de datos máximo del componente.

## Pendiente de decidir o investigar

| Tema | Cuándo se decide |
| --- | --- |
| Ubicación de las notas del usuario (carpetas a indexar) | Antes de la rebanada 3 |
| Cómo se conecta ivlia a los asistentes de cada proyecto (protocolo y alcance) | Antes de implementar el agente Code |
| Sandbox: tecnología y restricciones de las operaciones simples | Antes de permitir a los agentes ejecutar comandos o código |
| Base de datos de grafos (ArcadeDB o Neo4j) | Cuando se cumpla un criterio de entrada (ver «04 Conocimiento y memoria»), con una prueba de un día para cada una |
| Modelos locales concretos y motor definitivo | Con las evaluaciones propias, a partir de la rebanada 2 |
| Tecnología de voz | Cuando llegue el grupo de voz y aprendizaje |
| mypy o ty | Se revisa cuando ty madure con FastAPI y LangGraph |
| Fórmula de confianza de las citas y umbrales de las evaluaciones | Rebanada 3, con los primeros resultados sobre el corpus de ejemplo |
| Estado del dominio frente al de LangGraph | Se revisa en la rebanada 5, cuando entren las interrupciones |
| Copias de seguridad: qué se copia, dónde y cómo se cifra | Antes de la rebanada 2 |
| Servicio launchd y su instalación | Antes del primer uso real |
| Cómo se detecta que un hecho actualiza a otro | Rebanada 7 |
| Pasar los workflows de `ubuntu-24.04` a `ubuntu-26.04` ([ci.md](standards/ci.md#rules-for-every-workflow)) | Después de fusionar las PR apiladas pendientes, en su propia PR |
| Confirmar que Scorecard acepta `ubuntu-24.04` al publicar resultados ([ci.md](standards/ci.md#scorecard)) | En la primera ejecución de `scorecard.yml` en `main` |
| Confirmar que `analyze (actions)` pasa sin `actions: read` y que `paths-ignore` excluye `frontend/src/contract/` ([ci.md](standards/ci.md#codeql)) | En la primera ejecución de `codeql.yml` en `main` |
| Comprobar si Claude Code revisa la redirección de salida de un comando excluido del sandbox (`gh-repo.sh`, `git push`) ([ai-development.md](standards/ai-development.md#github-access)) | Antes de ampliar la lista de comandos excluidos |
