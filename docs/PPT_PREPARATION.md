# Guía para crear la presentación de CitaFácil

Este archivo está pensado para entregarse a GPT junto con `FINAL_PROJECT_REPORT.md`.
Pídele una presentación breve, visual y en español, sin inventar resultados o
aprobaciones humanas.

## Prompt sugerido para GPT

> Crea una presentación de 8 diapositivas en español para el Proyecto 1 de
> Tópicos Especiales II sobre CitaFácil. Usa exclusivamente la información de
> `docs/FINAL_PROJECT_REPORT.md`, `docs/REVIEW_QA_STAGES.md` y
> `docs/AI_INTERVENTIONS.md`. Destaca el proceso de ingeniería asistido por IA,
> las cinco historias, las 34 pruebas aprobadas y las limitaciones pendientes.
> No atribuyas aprobaciones humanas que no estén confirmadas. Propón diseño
> sobrio: azul oscuro, blanco y acento turquesa; poco texto, iconos simples y
> diagramas claros. Incluye notas del presentador con una frase por diapositiva.

## Estructura de 8 diapositivas

1. **Portada** - CitaFácil, Proyecto 1, integrantes y asignatura.
2. **Punto de partida y objetivo** - Aplicación existente, Feature Sprint,
   objetivos de ingeniería asistida por IA.
3. **Arquitectura** - Frontend HTML/CSS/JS, API FastAPI, SQLAlchemy y
   SQLite/PostgreSQL; diagrama de flujo cliente -> API -> base de datos.
4. **Historias obligatorias** - HU-01, HU-02 y HU-03 con una línea de valor por
   cada una.
5. **Historias adicionales** - HU-04 y HU-05; resaltar cancelación segura y
   próximas citas.
6. **Calidad y seguridad** - 34 pruebas, prevención de doble reserva, tokens
   temporales, hash del token de cancelación y autenticación admin.
7. **Uso responsable de IA** - Qué aportó, correcciones humanas/técnicas,
   decisiones rechazadas o limitadas y registro de IA.
8. **Demostración, roles y cierre** - Secuencia de demo, tabla resumida de
   rotación y próximos pasos reales.

## Recursos visuales que conviene pedir

- Captura del calendario mensual y de la tarjeta de previsión del panel admin.
- Diagrama simple del flujo de reserva/cancelación.
- Gráfico de barras para las cinco historias, no para inventar métricas.
- Insignia visible: `34 pruebas automatizadas aprobadas`.

## Guion de demostración en vivo

Duración objetivo: 3 a 5 minutos.

1. Elegir un servicio y fecha disponible en el calendario.
2. Reservar y abrir el enlace de cancelación privado.
3. Cancelar, volver al calendario y comprobar que el cupo se liberó.
4. Mostrar el acceso de cliente y sus próximas citas.
5. En el panel admin, abrir la previsión y explicar que es un promedio histórico
   con backtest, no una predicción por IA entrenada.
6. Cerrar con el resultado de la suite y las limitaciones conocidas.
