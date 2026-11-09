# ivlia · 04 Conocimiento y memoria

Nov 8, 2026 · @rlopc

## Memoria

La memoria guarda lo que ivlia recuerda del usuario y de sus conversaciones. Es un módulo separado del conocimiento (ver más abajo): la memoria es lo que ivlia aprende sobre el usuario y el conocimiento son las fuentes que el usuario ya tiene.

### Qué guarda

- Historial de conversaciones. Es la fuente de verdad de la conversación; los checkpoints de LangGraph son estado de trabajo y se podan (ver «02 Arquitectura e interfaces»).
- Hechos sobre el usuario.

### Alcance

Los hechos son globales o de un tema. El tema lo define el usuario.

### Almacenamiento de la memoria

SQLite propio de ivlia, con el historial, los hechos y el registro de acciones. En la instalación de uso vive fuera del repositorio; en desarrollo, en una carpeta del repositorio ignorada por git.

### Reglas de guardado

- El guardado es automático y deja un registro que el usuario puede revisar y corregir.
- Un hecho nuevo que actualiza o contradice uno existente del mismo alcance lo reemplaza, y el anterior queda archivado. Si no está claro, se guarda como nuevo y el usuario lo resuelve al revisar la memoria.
- Antes de guardar, cada hecho recibe un nivel de datos (ver «06 Datos y seguridad»). Lo que sea de nivel 3, como un secreto, nunca se guarda.

## Conocimiento

El módulo Conocimiento construye y consulta el grafo de conocimiento, y permite que ivlia responda sobre las fuentes del usuario con citas. Es un módulo separado con sus propios puertos. Sus datos viven fuera del repositorio en la instalación de uso, y en una carpeta del repositorio ignorada por git en desarrollo.

El **grafo de conocimiento** es la red que une todo lo que ivlia sabe de las fuentes del usuario. Sus **nodos** son documentos y apartados de las notas, proyectos (solo como referencias) y, más adelante, conceptos. Sus **aristas** son las relaciones entre ellos: enlaces, etiquetas, carpetas y, más adelante, relaciones extraídas con un modelo. Cada nodo y cada arista guardan su fuente y su nivel de datos.

### Fuentes

- Notas del usuario: documentos Markdown compatibles con Obsidian, con enlaces wikilink (`[[fichero]]`, `[[fichero#Título]]`, `[[fichero#^id]]`). Los nombres de fichero son únicos en todo el conjunto de notas. Algunos documentos existentes aún usan enlaces Markdown normales mientras se migran, y ivlia lee los dos tipos.
- Proyectos del usuario: solo una referencia (nombre, ubicación y qué prácticas o herramientas aplica). El detalle no se indexa: se consulta al asistente del proyecto (ver «03 Agentes y herramientas»).

### Construcción del grafo

Se construye primero con la estructura que ya existe: enlaces, etiquetas y carpetas. La extracción de conceptos con un modelo llega después.

### Extracción de conocimiento

Una tarea de extracción convierte una fuente (un PDF, una web, una transcripción de audio…) en un documento Markdown con wikilinks y lo añade al grafo de conocimiento. Cada tipo de fuente tiene su extractor, detrás del puerto Extractor. El documento generado se escribe en la carpeta propia de ivlia, una subcarpeta dentro de la carpeta de notas, guarda la referencia a la fuente original y hereda su nivel de datos (ver «06 Datos y seguridad»). Se indexa y se cita como cualquier otra nota. Llega después de la primera versión, junto con la extracción de conceptos con un modelo. ivlia no escribe en la carpeta de notas un documento cuyo nivel supere el máximo declarado para esa carpeta (por ejemplo, si se sincroniza con la nube): si lo supera, bloquea la operación y pregunta. Comprueba las colisiones de nombres y nunca sobrescribe un documento que el usuario haya editado.

### Indexado

- El reindexado es manual (`ivlia reindex`) al principio. El incremental llega después.
- Cada vector guarda qué modelo de embeddings lo creó. Si el usuario cambia de modelo, ivlia lo detecta, avisa de que el índice está desactualizado y no mezcla vectores de modelos distintos hasta reindexar.
- ivlia solo escribe en su propia carpeta.

### Búsqueda

Búsqueda híbrida: palabras clave, vectores y recorrido del grafo de conocimiento, con un reordenador final. Las respuestas citan sus fuentes e indican un nivel de confianza. La fórmula de la confianza (por ejemplo, la puntuación del reordenador y el acuerdo entre fuentes) se fija con los primeros resultados sobre el corpus de ejemplo.

### Almacenamiento del conocimiento

| Cuándo | Almacenamiento |
| --- | --- |
| Primero | Un solo SQLite: FTS5 para palabras clave, sqlite-vec para vectores y una tabla de aristas para el grafo de conocimiento. Los puertos VectorStore y GraphStore dejan abierto el cambio. |
| Después | Una base de datos de grafos (ArcadeDB o Neo4j) cuando se cumpla alguna de estas condiciones: recorridos de 3 saltos o más con p95 superior a 200 ms, medidos sobre un grafo sintético del tamaño de la instalación de uso; más de un millón de aristas, según las métricas (sin contenido) de la instalación de uso; o una consulta que SQL no exprese bien (camino más corto, patrones de subgrafo, centralidad), que es un criterio cualitativo y no se mide. |

La elección entre ArcadeDB (Apache 2.0, modo embebido desde Python con sus bindings, que incluyen su propio Java) y Neo4j Community (GPLv3, compatible con AGPL, más maduro) se hace en ese momento con una prueba de un día para cada una. Las licencias están pendientes de verificar en esa prueba.

### Calidad

Existe un conjunto de preguntas de referencia sobre un corpus de ejemplo sintético o público (de 20 a 50, con respuesta esperada). Las evaluaciones de recuperación se ejecutan con él en CI desde la primera rebanada de conocimiento. En CI se usan modelos pequeños que funcionan sin GPU, fijados por versión y guardados en caché. La evaluación se ejecuta en los PRs que tocan conocimiento, prompts o configuración de modelos, y cada semana. Los umbrales tienen margen para la variación entre equipos.

Los umbrales se calibran con ese corpus. Con las notas reales solo se hace una evaluación manual local, y esos datos no salen del Mac ni entran en CI ni en el repositorio.

## Fuentes

Consultadas el 9 de noviembre de 2026.

- [arcadedb-embedded en PyPI](https://pypi.org/project/arcadedb-embedded/): resumen de búsqueda. Respalda: bindings de Python con Java incluido (JRE 25), sin instalar Java aparte.
