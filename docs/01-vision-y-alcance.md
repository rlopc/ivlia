# ivlia · 01 Visión y alcance

Nov 8, 2026 · @rlopc

ivlia es un asistente personal de IA para gestionar conocimiento de cualquier tipo. Se ejecuta 100 % en local, en el Mac del usuario (Apple M2 Max, 64 GB).

## Objetivos

- Un único asistente que gestiona el conocimiento del usuario (notas, documentos y otras fuentes) y responde citando de dónde sale cada respuesta.
- Los proyectos del usuario tienen su propio asistente de desarrollo. ivlia guarda de cada proyecto una referencia y, cuando hace falta, habla con ese asistente.
- Privacidad alta: los datos no salen del equipo salvo decisión explícita, y una política de niveles lo controla.
- Modularidad: cualquier componente (modelo, base de datos, interfaz) puede cambiar de origen (local, red local o nube) sin afectar al resto.
- Calidad de producción desde el primer día, aunque el proyecto sea pequeño, para practicar desde el principio las prácticas de un proyecto grande.
- Construcción en rebanadas verticales pequeñas que el usuario pueda comprender y supervisar.

## Alcance por fases

**Fase 0**: deja el entorno de desarrollo local completo para todas las fases futuras. Cada herramienta que los documentos «08 Ingeniería y calidad» y «09 IA en el desarrollo» no aplazan explícitamente está instalada, configurada y ejecutándose sobre el código mínimo. Cada pieza de la arquitectura existe en su versión mínima que funciona (por ejemplo, la API con un endpoint básico, la CLI con un comando, la web con una página, la base de datos con su migración inicial). No hay funcionalidad real. Se construye sin desarrollo guiado por especificaciones, que se usa desde la rebanada 2.

**Fases siguientes**: se implementa el código real de cada aspecto, en rebanadas y con desarrollo guiado por especificaciones (ver «09 IA en el desarrollo»). La tabla indica qué se implementa primero y qué después.

| Aspecto | Primero | Después |
| --- | --- | --- |
| Interfaz | CLI | Web local |
| Modalidad | Texto | Voz |
| Modelos | Solo locales | Externos opcionales (red local o nube), con nivel de datos máximo |
| Fuentes de conocimiento | Notas | Otras fuentes |
| Ejecución | Nativa en macOS (launchd y scripts) | Docker |
| Agentes | Central y Knowledge | Code y Learning |
| Capacidades | Leer archivos | Ejecutar acciones con permiso y buscar en internet, por fases |

## Datos del proyecto

- Nombre: ivlia.
- Licencia: AGPL-3.0-or-later.
- Repositorio: GitHub, público.
- Idioma del código, la documentación del repositorio y los commits: inglés.

## Glosario

- ADR: registro de una decisión de arquitectura difícil de revertir, numerado y que no se modifica.
- Almacén de secretos: servicio del sistema operativo que guarda claves y contraseñas cifradas (el Llavero en macOS).
- Asistente de proyecto: asistente de desarrollo propio de cada proyecto del usuario, con el que ivlia se comunica (ver «03 Agentes y herramientas»).
- Cadena de hashes: registro en el que cada entrada incluye un resumen criptográfico (hash) de la anterior, de modo que cambiar una entrada rompe la cadena y se detecta.
- Checkpoint: copia del estado de una ejecución de LangGraph que permite pausarla y reanudarla.
- CI (integración continua): sistema que ejecuta automáticamente las comprobaciones en cada cambio.
- Clean Architecture y arquitectura hexagonal: formas de organizar el código en las que el núcleo (dominio y casos de uso) no depende de ninguna tecnología, y lo externo se conecta mediante puertos y adaptadores.
- Conventional Commits: convención para escribir mensajes de commit con un tipo (`feat`, `fix`…) y un área, que permite generar versiones y CHANGELOG automáticamente.
- Corpus de ejemplo: conjunto de notas sintéticas o públicas, dentro del repositorio, sobre el que se prueban la búsqueda y las evaluaciones.
- Desarrollo guiado por especificaciones: forma de trabajar en la que primero se escribe y se aprueba la especificación de un cambio, y después se implementa.
- DNS rebinding: ataque en el que una web externa hace que su dominio apunte a la dirección local del usuario para llegar a servicios que solo escuchan en su equipo.
- Documento de estándares: documento del repositorio que describe las herramientas y prácticas vigentes del proyecto (ver «08 Ingeniería y calidad»).
- Embeddings: representación numérica de un texto que permite buscar por significado.
- Endpoint: dirección concreta de la API (ruta y método HTTP) que atiende un tipo de petición.
- Fichero de bloqueo: fichero que fija la versión exacta de cada dependencia (`uv.lock`, `pnpm-lock.yaml`) para que todas las instalaciones sean iguales.
- FTS5: módulo de SQLite para buscar texto por palabras clave.
- Fuente de verdad: el registro que manda cuando un dato tiene varias copias.
- Grafo de conocimiento: red de nodos (documentos y apartados de las notas, proyectos como referencias y conceptos) y aristas (relaciones) construida a partir de las fuentes del usuario (ver «04 Conocimiento y memoria»).
- Hecho: dato sobre el usuario que guarda la memoria. Es global o de un tema, que define el usuario (ver «04 Conocimiento y memoria»).
- Hook: comando que Claude Code ejecuta automáticamente en un momento concreto, por ejemplo tras editar un archivo o antes de un commit.
- Interrupción: pausa de una ejecución de LangGraph a la espera de una respuesta externa, como una aprobación.
- Inyección de prompts: instrucciones ocultas en contenido externo que intentan que un agente haga algo que no se le ha pedido.
- JSON Schema: formato estándar para describir la estructura de datos JSON.
- launchd: sistema de macOS que arranca y mantiene servicios en segundo plano.
- Mapa de decisiones: lista de decisiones con su estado (Final o Provisional) y, en las provisionales, cuándo revisarlas.
- MCP: protocolo estándar para conectar herramientas externas a un agente.
- Migración: cambio en el formato de los datos guardados, junto con el código que convierte los que ya existen.
- Modelo como juez: evaluación en la que un modelo puntúa respuestas siguiendo una rúbrica (lista de criterios).
- Monorepo: un solo repositorio que contiene varias partes del proyecto.
- Nivel de datos: clasificación de cada dato de 0 (público) a 3 (secreto) que decide a qué componentes puede ir (ver «06 Datos y seguridad»).
- OpenAPI: formato estándar para describir una API HTTP.
- OpenSpec: herramienta de código abierto (MIT) para el desarrollo guiado por especificaciones. Guarda las especificaciones vigentes y los cambios propuestos.
- p95: valor por debajo del cual queda el 95 % de las mediciones, por ejemplo de tiempo de respuesta.
- Periodo de espera: tiempo mínimo desde que se publica una versión de una dependencia hasta que se acepta.
- Preguntas de referencia: preguntas con su respuesta esperada sobre el corpus de ejemplo, que sirven para medir la búsqueda.
- Puerto: interfaz que define qué necesita el núcleo de un componente externo. El adaptador es la pieza concreta que lo implementa.
- Rebanada vertical: cambio pequeño que atraviesa todas las capas necesarias y termina con una prueba que demuestra que funciona.
- recall@5: proporción de documentos relevantes que aparecen entre los 5 primeros resultados de una búsqueda.
- Reordenador: modelo que reordena los resultados de una búsqueda por relevancia.
- Sandbox: entorno aislado donde se ejecutan comandos y código sin acceso al resto del sistema.
- SemVer: numeración de versiones MAYOR.MENOR.PARCHE, según el tipo de cambio.
- SPA: aplicación web de una sola página que se ejecuta en el navegador.
- sqlite-vec: extensión de SQLite para buscar por vectores (embeddings).
- Squash: fusionar todos los commits de una rama en uno solo.
- SSE (Server-Sent Events): estándar web para que el servidor envíe eventos al cliente por una conexión HTTP.
- Subagente: agente que otro agente lanza para una tarea concreta, con su propio contexto, y que le devuelve el resultado.
- TDD: escribir primero un test que falla, después el código que lo hace pasar y, al final, mejorar el código.
- Test de contrato: test que todo adaptador de un puerto debe pasar, para que los adaptadores sean intercambiables.
- Test de instantánea: test que compara una salida con una copia guardada y falla si cambia.
- Tests de mutación: técnica que introduce pequeños errores en el código para comprobar que los tests los detectan.
- Token: tiene dos sentidos. En la API, credencial que identifica al cliente. En los modelos, unidad de texto con la que se mide la entrada y la salida.
- Transcript: puerto que convierte audio en texto.
- Traza: registro del recorrido de una petición por el sistema, con el tiempo de cada paso. OpenTelemetry es el estándar para generarlas.
- Wikilink: enlace entre notas con la forma `[[fichero]]`, propio de Obsidian.
