# ivlia · 03 Agentes y herramientas

Nov 8, 2026 · @rlopc

## Agentes

Un agente central habla con el usuario y delega en agentes especializados por área. Cada especializado puede gestionar su propio grupo de subagentes, hasta una profundidad máxima configurable.

| Agente | Función | Cuándo |
| --- | --- | --- |
| Central | Habla con el usuario, decide a quién delegar y compone la respuesta | Primero |
| Knowledge | Consulta el grafo de conocimiento y responde con citas | Primero |
| Code | Habla con los asistentes de cada proyecto: les consulta sobre sus proyectos y les propone acciones a partir del conocimiento del grafo | Después |
| Learning | Apoya el aprendizaje, empezando por el inglés | Después |

### Reglas de funcionamiento

- Delegación: el central elige agente según su descripción. El usuario puede forzar uno escribiendo `@agente`.
- Profundidad: configurable, y empieza en 1 (el central delega en especializados, que no delegan a su vez). El motivo de la jerarquía es que cada agente especializado trabaja con menos contexto.
- Contexto: cada agente recibe el mínimo necesario y puede pedir más.
- Modelo: cada agente declara el modelo que usa.
- Definición: mixta. La configuración (descripción, modelo, herramientas permitidas, límites) va en archivos y el comportamiento, en código.
- Transparencia: el usuario ve por defecto un resumen de la delegación y puede pedir el detalle.
- Límites: pasos, tokens y tiempo, por agente y globales.

## Herramientas y permisos

Las herramientas son las acciones que un agente puede ejecutar: leer archivos, buscar en internet, ejecutar comandos. Todas pasan por un único puerto Tool.

### Puerto Tool

- Adaptadores nativos (código propio) y un adaptador MCP para herramientas externas.
- Cada agente tiene una lista permitida de herramientas, y una política central puede restringirla más.
- El contenido que llega de fuera (webs, documentos, resultados de herramientas) es datos no fiables: va marcado como datos y no puede disparar herramientas de escritura sin aprobación. Tests deterministas lo verifican.

### Niveles de permiso

| Nivel | Acciones | Qué ocurre |
| --- | --- | --- |
| Libre | Lectura | Se ejecuta sin preguntar |
| Con confirmación | Escritura y comandos | El usuario aprueba cada acción |
| Bloqueado | Acciones peligrosas | Nunca se ejecutan |

### Aprobaciones

- La API emite un evento de aprobación pendiente. La CLI o la web muestran la acción exacta con Aprobar y Rechazar.
- Si el usuario no contesta en un tiempo límite, la acción se rechaza.
- Cada decisión queda en un registro de acciones que permite detectar manipulaciones: una cadena de hashes en el SQLite de memoria.

### Sandbox

- Operaciones simples: se ejecutan en el Mac con restricciones.
- Comandos y código: se ejecutan en un contenedor aislado, sin red por defecto.
- Los comandos se lanzan con un entorno limpio, que solo incluye las variables permitidas.
- Hasta que el sandbox exista, ningún agente ejecuta comandos ni código.

### Asistentes de proyecto

Cada proyecto del usuario tiene su propio asistente de desarrollo. ivlia se conecta a él mediante el puerto Tool (por ejemplo, con su adaptador MCP) para consultarle sobre su proyecto y para proponerle acciones. Consultar no necesita confirmación si el asistente de proyecto se conecta en un modo de solo lectura que él mismo garantiza; si no lo garantiza, consultar también la necesita. Sus respuestas son datos no fiables, como cualquier resultado de herramienta. Proponer o enviar una acción necesita la confirmación del usuario. Cada asistente de proyecto declara el nivel de datos máximo que puede recibir, y ivlia bloquea la operación y pregunta si el mensaje lo supera (ver «06 Datos y seguridad»).
