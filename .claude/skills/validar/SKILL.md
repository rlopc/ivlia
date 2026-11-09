---
name: validar
description: Paso Validar, antes de cada paso de la fase 0 y de cada rebanada. Comprueba versiones, documentación oficial y buenas prácticas de las herramientas implicadas, las compara con el diseño, el plan y el repositorio, y guarda un informe corto que el usuario ve antes de empezar.
---

# Validar

Procedimiento del paso Validar descrito en `docs/09-ia-en-el-desarrollo.md` («Ciclo de cada rebanada») y en el plan de la fase 0 (`docs/plan/phase-0.md`, regla común 1).

## Entrada

- El paso o la rebanada que va a empezar.
- Su alcance de Validar: en la fase 0, la sección «Validar scope» del paso en el plan; desde la rebanada 2, las tecnologías de la propuesta.

## Procedimiento

1. Lee el alcance y las secciones del diseño y del plan que enlaza. No cargues todo `docs/`.
2. Usa la red solo con la confirmación del usuario.
3. Delega la lectura de fuentes en el agente `researcher`, invocándolo con el modelo Sonnet. Dale un encargo completo: objetivo, puntos que comprobar, fuentes oficiales primero, límites, presupuesto de llamadas y formato de salida. Si los puntos son independientes, reparte el trabajo en varios encargos.
4. Para cada versión, comprueba también el periodo de espera de 7 días: si la última versión tiene menos, indica la última que lo cumple.
5. Compara el resultado con el diseño, el plan y el estado del repositorio. Lo que contradiga una decisión no se cambia: se presenta al usuario con las opciones.

## Salida

Guarda el informe en `.dev/validar-step-N.md` (fase 0) o `.dev/validar-<rebanada>.md`, ignorados por git, y muéstralo al usuario antes de empezar. Su resumen va después en la descripción del PR.

Formato:

- **Confirmado:** lo que coincide con el diseño y el plan.
- **Cambiado:** lo que difiere, con el dato exacto (versión y fecha, sintaxis, opción) y qué implica.
- **Riesgos:** lo que puede fallar o hay que vigilar.
- **Fuentes:** cada URL con lo leído de ella (completa, parcial o resumen).
