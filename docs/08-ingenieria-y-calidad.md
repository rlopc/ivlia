# ivlia · 08 Ingeniería y calidad

Nov 8, 2026 · @rlopc

## Herramientas por parte

| Área | Herramientas |
| --- | --- |
| Interfaz común | `just` en la raíz, que orquesta Python y pnpm (`just check` ejecuta todas las comprobaciones locales salvo la evaluación de recuperación, que va en `just eval`) |
| Backend y CLI (Python) | uv (con `exclude-newer` relativo), ruff (formato y análisis), mypy, pytest, import-linter |
| Frontend (TypeScript) | pnpm (con `minimumReleaseAge`), ESLint (strictTypeChecked, react-hooks, eslint-plugin-boundaries), Prettier, knip, Vitest con React Testing Library y MSW, Playwright con axe |
| Repositorio | pre-commit con gitleaks, actionlint, zizmor y shellcheck; CodeQL, Dependabot con periodo de espera y OpenSSF Scorecard |

Solo se ejecutan en CI: CodeQL, OpenSSF Scorecard, Dependabot, la comprobación del título del PR y la de enlaces externos. En local, la comprobación de enlaces se ejecuta sin red.

El periodo de espera de las dependencias es el mismo en pnpm, uv y Dependabot (7 días, provisional: se confirma en la validación del primer paso de la fase 0).

## Necesidades con herramienta provisional

Cada una se elige en el paso Validar de la fase 0 que corresponda y la elección se escribe en el documento de estándares.

| Necesidad | Origen | Candidatos |
| --- | --- | --- |
| Versiones de Python y Node | Entorno reproducible | `.python-version` (uv); mise o `engines` en `package.json` para Node |
| Migraciones de SQLite | «01 Visión y alcance»: base de datos con su migración inicial | Alembic, o scripts SQL numerados con `PRAGMA user_version` |
| Tipos de TypeScript generados del JSON Schema | «02 Arquitectura e interfaces»: contrato único | json-schema-to-typescript o json-schema-to-zod |
| Comprobación de Markdown y enlaces | «09 IA en el desarrollo»: la CI valida el Markdown y los enlaces | markdownlint-cli2 y lychee |
| Comprobación del título del PR | Formato `<tipo>(<área>): <resumen>` | action-semantic-pull-request |
| Cobertura | Umbrales de «Pruebas» | pytest-cov y la cobertura de Vitest |
| Comprobaciones rápidas de pre-commit | «09 IA en el desarrollo»: antes de cada commit | ruff y Prettier, como hooks locales con la versión de los lockfiles |
| Versiones y CHANGELOG | «Entrega»: a partir de Conventional Commits | release-please o python-semantic-release |

## Tipado

mypy en modo estricto, provisional (ver «mypy o ty» en «10 Plan y pendientes»). Las excepciones de tipos se permiten solo en los módulos que integran librerías externas (adaptadores y `application/orchestration`), nunca en el dominio. Cada una es lo más estrecha posible y lleva un comentario con el motivo.

## Pruebas

- TDD: rojo, verde, refactor.
- Cobertura: 100 % en el dominio y 95 % en el resto.
- Tests de contrato por puerto.
- mutmut (Python) y Stryker (TypeScript) más adelante, sobre el dominio y sin bloquear PRs hasta que el dominio se estabilice.

## Git

- Ramas cortas, una por PR, fusionadas por squash en `main`, la única rama permanente. Una rebanada puede repartirse en varios PRs.
- Cada cambio deja `main` funcionando: no se fusiona un PR con la CI en rojo.
- Commits en formato Conventional Commits.
- Título de PR: `<tipo>(<área>): <resumen>`, con los tipos de Conventional Commits y las áreas backend, frontend, cli, docs, ci, repo y deps (actualizaciones de dependencias). Tras el squash es el mensaje del commit.

## Entrega

ivlia puede estar en uso y en desarrollo a la vez. Cada versión nueva debe poder seguir usando lo generado con las anteriores.

- Una sola versión para todo el repositorio, con SemVer. La versión y el CHANGELOG se generan a partir de los Conventional Commits.
- La instalación de uso solo instala versiones etiquetadas, nunca `main`.
- Los datos originales (memoria, historial, registro de acciones, documentos extraídos y configuración del usuario) se migran. Cada cambio de formato incluye su migración, solo hacia delante, y un test la aplica sobre datos creados con la versión anterior. El registro de acciones conserva su cadena de hashes verificable.
- Los datos derivados de las notas (índice, vectores y grafo) se regeneran con `ivlia reindex` en vez de migrarse. Los checkpoints se descartan.
- Al arrancar con migraciones pendientes, el servidor hace primero una copia (el mismo caso de uso que `ivlia backup`) y después las aplica. Si una migración falla, ivlia no arranca y dice qué falla.
- Volver atrás es instalar la versión anterior y restaurar la copia. Lo generado después de la copia se pierde.

## Documentación en tres capas

1. Documento de estándares: describe solo el estado actual del proyecto, sin su historia.
2. ADRs numerados e inmutables, solo para decisiones difíciles de revertir con alternativas defendibles y que no sean evidentes.
3. Mapa de decisiones Final o Provisional, con "revisar cuando" en las provisionales. Se edita en el sitio.

Regla: todo PR actualiza en el mismo PR la documentación afectada: las especificaciones si cambia el comportamiento y el documento de estándares si cambian herramientas o prácticas. La plantilla de PR lo recuerda.

## Fuentes

Consultadas el 9 de noviembre de 2026.

- [uv: Dependabot](https://docs.astral.sh/uv/guides/integration/dependabot/), [GitHub: opciones de Dependabot](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference) y [pydevtools: periodo de espera en uv](https://pydevtools.com/handbook/how-to/how-to-protect-against-python-supply-chain-attacks-with-uv/): resumen de búsqueda. Respalda: `exclude-newer` relativo desde uv 0.9.17 y periodo de espera de Dependabot alineado con uv.
- [pydevtools: ty](https://pydevtools.com/handbook/topics/ty/): resumen de búsqueda. Respalda: ty sigue en beta (0.0.93, octubre de 2026).
