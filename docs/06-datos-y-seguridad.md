# ivlia · 06 Datos y seguridad

Nov 8, 2026 · @rlopc

## Política de datos

Cada dato tiene un nivel de datos, y cada componente declara el nivel máximo que puede recibir. La política se aplica de forma automática.

### Niveles

| Nivel | Nombre | Puede ir a |
| --- | --- | --- |
| 0 | Público | Cualquier componente, incluso externo en la nube |
| 1 | Interno | Componentes de la red local |
| 2 | Privado | Solo el Mac del usuario |
| 3 | Secreto | Nunca a modelos ni a logs |

### Reglas

- Los datos derivados (resúmenes, embeddings, hechos de memoria) heredan el nivel más alto de los datos de los que salen.
- El nivel de cada dato lo fija su origen (por ejemplo, la carpeta de la que viene) y el usuario puede cambiarlo por carpeta. En la carpeta propia de ivlia manda el nivel heredado de cada documento, no el de la carpeta.
- Lo que no está clasificado se trata como Privado (nivel 2).
- Si un dato supera el nivel máximo del componente que lo recibiría, ivlia bloquea la operación y pregunta al usuario. El nivel 3 siempre se bloquea.
- Clasificar es automático: reglas por origen más un detector de secretos que marca como nivel 3 lo que lo parezca. Cuando llegue la extracción de conocimiento con modelos (ver «04 Conocimiento y memoria»), un modelo podrá subir el nivel de un dato, nunca bajarlo.
- Un secreto (nivel 3) que el usuario escriba en el chat o que llegue en el resultado de una herramienta se sustituye por una marca antes de guardarlo y antes de enviarlo al modelo, también en el historial, los checkpoints y los logs, y ivlia avisa al usuario. En las notas se excluye solo el fragmento detectado y el resto se indexa.

## Seguridad

- Un modelo de amenazas, escrito en el documento de estándares desde la fase 0: qué protege, de quién y cómo (separación de datos e instrucciones, aprobaciones, sandbox).
- Escaneo de secretos con gitleaks en local y con el escaneo de secretos de GitHub, que bloquea el push, análisis con CodeQL y dependencias vigiladas con Dependabot.
