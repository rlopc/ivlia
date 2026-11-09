# ivlia · 05 Modelos

Nov 8, 2026 · @rlopc

Los modelos de IA se usan siempre a través de puertos intercambiables. Cada modelo es un ajuste de configuración.

## Grupos de modelos

| Grupo | Modelos | Cuándo |
| --- | --- | --- |
| Base | Modelo de lenguaje (chat y razonamiento), embeddings y reordenador de resultados | Primero |
| Voz y aprendizaje | Voz a texto, reconocimiento de fonemas (para evaluar la pronunciación) y texto a voz | Después |

## Punto de partida para voz y aprendizaje

Estos son los modelos que el usuario ya ha probado en sus proyectos de inglés. Son candidatos y no una decisión.

- Voz a texto: Whisper large-v3, con large-v3-turbo como candidato de producción.
- Reconocimiento de fonemas: wav2vec2-lv-60-espeak-cv-ft, con eSpeak NG, `phonemizer` (ambos GPL-3.0, compatibles con AGPL-3.0) y `jiwer` para comparar.
- Texto a voz: Piper (`OHF-Voice/piper1-gpl`, GPL-3.0, compatible con AGPL-3.0; el repositorio original con licencia MIT está archivado), con las voces `en_GB-cori-high` y `es_ES-sharvard-medium`. Cada voz tiene su propia licencia, que se revisa al elegirla.
- La voz va en un paquete opcional para no condicionar el núcleo.

## Reglas

- Motor de ejecución inicial: Ollama para el modelo de lenguaje y los embeddings. El reordenador corre en el propio proceso de ivlia, detrás del puerto Reranker.
- Ningún modelo concreto está fijado. Se eligen con las evaluaciones propias de ivlia, y cada cambio se decide con datos.
- Solo modelos locales por ahora. El puerto está preparado para modelos externos (otro equipo de la red local o nube), cada uno con un nivel de datos máximo declarado (ver «06 Datos y seguridad»).
- Todos los modelos locales configurados se cargan al arrancar y se mantienen en memoria; cada adaptador de motor lo garantiza con los medios de su motor. ivlia usa su propia instancia del motor. Al arrancar comprueba que los modelos caben en el límite de memoria configurado; si no caben, no arranca y dice qué falla.
- Si un modelo falla, ivlia reintenta un número limitado de veces y después informa del error. Nunca cambia de modelo en silencio. Si falla una pieza opcional, como el reordenador, sigue sin ella y lo avisa.

## Fuentes

Consultadas el 9 de noviembre de 2026.

- [Ollama: FAQ](https://docs.ollama.com/faq): parcial (carga, memoria y cola). Respalda: `keep_alive`, `OLLAMA_MAX_LOADED_MODELS` y el desalojo de modelos.
- [rhasspy/piper](https://github.com/rhasspy/piper) y [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl): parcial (página principal). Respalda: repositorio original archivado y nuevo con GPL-3.0.
