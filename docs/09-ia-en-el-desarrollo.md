# ivlia · 09 IA en el desarrollo

Nov 8, 2026 · @rlopc

Claude Code desarrolla ivlia con desarrollo guiado por especificaciones, usando OpenSpec (licencia MIT). Las especificaciones describen el comportamiento del producto. El documento de estándares (descrito en «08 Ingeniería y calidad») describe las herramientas y prácticas. El ciclo de abajo se usa desde la rebanada 2. La fase 0 crea el entorno, incluida la instalación y configuración de OpenSpec, sin ese ciclo.

## Desarrollo independiente del uso real

ivlia en desarrollo e ivlia en uso son dos instalaciones independientes. Los datos reales del usuario (notas, memoria, secretos) solo existen en la instalación de uso.

- Desarrollo: tiene su propia configuración y sus propias bases de datos, y una carpeta de notas de ejemplo (sintéticas o públicas) dentro del repositorio. Los tests y el conjunto de preguntas de referencia usan solo esos datos. El entorno donde corre Claude Code no contiene secretos reales.
- Uso: la configuración y los datos viven en el Mac, fuera del repositorio, y Claude Code no tiene acceso a ellos.

## Ciclo de cada rebanada (desde la rebanada 2)

1. **Validar.** Antes de empezar, un subagente de solo lectura busca información actual (documentación oficial, versiones, buenas prácticas) sobre las tecnologías implicadas y la contrasta con este diseño y con el estado del repositorio. Entrega un informe corto: qué se confirma, qué ha cambiado y qué riesgos hay. Si contradice el diseño, se corrige el diseño o la propuesta antes de implementar. También se hace antes de cada paso de la fase 0.
2. **Proponer.** La IA escribe el cambio en OpenSpec: `proposal.md`, `tasks.md` y las especificaciones modificadas. Punto de control 1: el usuario aprueba la propuesta junto con el informe de validación.
3. **Tests.** La IA escribe primero los tests de cada tarea (TDD). Punto de control 2: el usuario los aprueba antes de que se implemente nada.
4. **Implementar.** La IA implementa tarea a tarea hasta que los tests pasen.
5. **Verificar.** `just check` en verde y revisión independiente: un subagente con contexto limpio, que no ha visto cómo se hizo, comprueba el resultado contra la especificación.
6. **Archivar.** Las especificaciones vigentes, el documento de estándares y el mapa de decisiones quedan actualizados, y la IA da un resumen corto. Punto de control 3: el usuario revisa el PR.

Si una rebanada se reparte en varios PRs, el primero contiene la propuesta y los tests (puntos de control 1 y 2), los siguientes la implementación y el último el archivado. Los tests del primer PR se marcan como fallo esperado estricto (la CI falla si pasan) y cada PR de implementación quita la marca de los suyos. El usuario revisa cada PR.

## Modo de trabajo de la fase 0

Claude Code construye el entorno en pasos pequeños (por ejemplo: repositorio y `just`, backend, CLI, frontend, CI, y versión y entrega), guiado por este diseño. Antes de cada paso se hace una validación y el usuario ve su informe antes de empezar. No hay propuestas ni tests aprobados de antemano. Cada paso es un PR que deja `main` funcionando, con `just check` en verde, y el usuario lo revisa.

## Especificaciones

`openspec/specs/` describe el comportamiento vigente y `openspec/changes/` los cambios propuestos. Al archivar un cambio, se fusiona en `openspec/specs/` y se conserva su historial.

## Instrucciones para la IA

- `AGENTS.md` en la raíz, corto: solo lo que la IA no puede deducir del código (cómo ejecutar `just check`, el ciclo anterior, qué no debe tocar sin pedirlo) y enlaces al documento de estándares.
- `CLAUDE.md` importa `@AGENTS.md` y añade solo lo propio de Claude Code.
- Reglas por zona (backend y frontend) en `.claude/rules/`, que se cargan al tocar esa carpeta.
- Ninguna norma se duplica: la única fuente es el documento de estándares, que se enlaza.

## Guardarraíles

- Permisos de Claude Code: leer y escribir solo dentro del repositorio, de modo que no accede a los datos reales del usuario, que viven fuera de él. Los comandos salen de una lista permitida (`just`, `uv`, `pnpm` y git local). Instalar dependencias desde el fichero de bloqueo no pide confirmación. Añadir o actualizar dependencias, el push, borrar archivos, el resto del uso de la red y los secretos piden confirmación del usuario.
- La CI es el árbitro final de todas las comprobaciones.

## Las herramientas de calidad guían a la IA

Las herramientas de «08 Ingeniería y calidad» (ruff, mypy, import-linter, pytest, ESLint, Vitest, etc.) sirven para desarrollar ivlia y son lo que guía a Claude Code: ejecuta las comprobaciones, lee los errores y se corrige solo antes de que el usuario revise.

- Todas se ejecutan a través de `just`, y Claude Code las ejecuta con esos comandos.
- Tras cada edición, un hook ejecuta las comprobaciones rápidas (formateador y linter).
- `just check` ejecuta todas las comprobaciones locales salvo la evaluación de recuperación: tipos, reglas de arquitectura, tests y cobertura. La evaluación va en `just eval`, y la CI la ejecuta según «04 Conocimiento y memoria». `just check` se ejecuta en el paso Verificar, antes de abrir el PR y en CI. Antes de cada commit solo se ejecutan las comprobaciones rápidas de pre-commit (ver «08 Ingeniería y calidad»).
- La IA no da una tarea por terminada mientras alguna comprobación falle, y no desactiva ni relaja una regla para que pase.

## Documentación

La regla de actualizar la documentación en el mismo PR (ver «08 Ingeniería y calidad») incluye las especificaciones vigentes y, si la decisión es difícil de revertir, un ADR. Al archivar, la IA busca y corrige las descripciones que hayan quedado obsoletas. La plantilla de PR lo recuerda con una lista de comprobación y la CI valida el Markdown y los enlaces.

## IA por tarea

Provisional: se revisa cuando haya datos de uso.

| Tarea | IA | Modelo |
| --- | --- | --- |
| Proponer cambios, escribir especificaciones y diseñar | El modelo más capaz | Claude Fable 5.1 |
| Implementar tareas ya especificadas | Un modelo más rápido y barato | Claude Sonnet 5.5 |
| Revisión independiente | Subagente con contexto limpio, distinto y más capaz que el que implementó | Claude Opus 5.5 |
| Investigar y buscar | Subagentes de solo lectura | Claude Sonnet 5.5; Claude Haiku 5.5 para búsquedas mecánicas |

## Fuentes

Consultadas el 9 de noviembre de 2026.

- [Claude Code: memoria](https://code.claude.com/docs/en/memory): parcial (`.claude/rules/`, importaciones y `AGENTS.md`). Respalda: reglas por zona con `paths` y `CLAUDE.md` que importa `@AGENTS.md`.
- [OpenSpec](https://github.com/Fission-AI/openspec): resumen de búsqueda. Respalda: licencia MIT y archivado de cambios en `specs/`.
