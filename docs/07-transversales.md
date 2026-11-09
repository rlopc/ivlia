# ivlia · 07 Transversales

Nov 8, 2026 · @rlopc

Aspectos que afectan a todo ivlia.

## Configuración

Tres capas: los valores por defecto van en el código, los ajustes del usuario en un archivo TOML (fuera del repositorio en la instalación de uso; en desarrollo, en una carpeta del repositorio ignorada por git), y los secretos fuera de ambos. Los secretos se buscan, por orden, en variables de entorno, en el almacén de secretos del sistema (mediante `keyring`) y, si el almacén no está disponible, en un fichero de la carpeta de datos de ivlia legible solo por el usuario. Los secretos que genera ivlia, como el token de la API, se crean solos al primer arranque y se guardan en el almacén o, si no está disponible, en ese fichero. Cada instalación usa un nombre de servicio propio en `keyring`. La instalación de desarrollo nunca usa el almacén del sistema: solo variables de entorno o el fichero de su carpeta de datos. Todo se valida al arrancar. Si algo está mal, ivlia no arranca y dice qué falla.

## Observabilidad

Logs estructurados y trazas OpenTelemetry desde la primera rebanada. Se guardan solo en el Mac, sin exportador externo. Por defecto registran metadatos (modelo, tokens, herramienta, duración) y no el contenido de los mensajes; el contenido solo se registra en un modo de depuración explícito y local. El nivel 3 nunca se registra.

## Evaluaciones

Tres capas:

1. Tests deterministas de herramientas y permisos, incluida la defensa contra la inyección de prompts.
2. Evaluaciones de recuperación con el conjunto de preguntas de referencia (por ejemplo, recall@5 ≥ 0,8 como umbral inicial, que se ajusta con los primeros resultados sobre el corpus de ejemplo).
3. Modelo como juez con rúbricas. Con modelos locales solo se usa de forma comparativa (A frente a B, misma rúbrica) y no como puntuación absoluta.

Los prompts son artefactos versionados en el repositorio, con tests de instantánea. Cambiar un prompt es un PR.

## Copias de seguridad

`ivlia backup` hace una copia consistente de los datos de la instalación en la que se ejecuta y `ivlia restore` la recupera. Un test prueba la restauración con los datos de ejemplo.
