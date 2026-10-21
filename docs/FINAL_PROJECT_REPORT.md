# Reporte final - Proyecto 1: CitaFácil

## Resumen ejecutivo

Se extendió CitaFácil, un sistema web de reservas basado en FastAPI, SQLAlchemy,
SQLite/PostgreSQL y frontend HTML/CSS/JavaScript. El objetivo fue trabajar sobre
una aplicación existente aplicando un Feature Sprint asistido por IA, manteniendo
control humano, pruebas automatizadas y trazabilidad Git.

## Alcance entregado

| ID | Historia de usuario | Entrega validada |
|---|---|---|
| HU-01 | Como usuario recurrente, quiero reservar con mis datos guardados para no repetirlos. | Perfil de cliente, verificación temporal y reserva autenticada. La aplicación base no tiene pago, por lo que la reutilización cubre los datos que sí solicita su reserva. |
| HU-02 | Como cliente, quiero un calendario dinámico de disponibilidad para elegir fecha sin intentos fallidos. | Calendario mensual por servicio, estados de día y revalidación de conflicto 409. |
| HU-03 | Como administrador, quiero una previsión basada en el histórico para planificar capacidad y precios. | Promedio por día de semana, gráfico, advertencias y backtest MAE; no modifica precios automáticamente. |
| HU-04 | Como cliente, quiero cancelar mediante un enlace privado para liberar mi horario sin llamar al negocio. | Token de un solo uso lógico por cita, hash en BD, previsualización y cancelación explícita. |
| HU-05 | Como cliente registrado, quiero ver mis próximas citas para recordar mis reservas. | Consulta privada de citas futuras activas del cliente autenticado. |

## Proceso y trazabilidad

- Repositorio propio con ramas `feature/hu-01-profile-reuse`,
  `feature/hu-02-calendario-dinamico`, `feature/hu-03-prevision-demanda`,
  `feature/hu-04-cancelacion-privada` y `feature/hu-05-my-appointments`.
- PR equivalentes fusionadas y commits por historia. HU-04 fue integrada
  posteriormente en `main` porque su PR original quedó apilada sobre HU-02.
- Roles rotados por etapas y evidencia técnica/QA en
  `docs/REVIEW_QA_STAGES.md`.
- Registro de intervenciones, correcciones y límites de IA en
  `docs/AI_INTERVENTIONS.md`.

## Uso responsable de IA

La IA apoyó análisis, implementación y pruebas. No se aceptó código sin
verificación: se corrigieron expectativas de pruebas de cupos, se hizo portátil
la base temporal de tests y se corrigió la generación de datos para el backtest.
La previsión es estadística explicable, no un modelo entrenado. Las limitaciones
pendientes, como el proveedor real de OTP/WhatsApp y el token de cancelación en
URL, quedan documentadas y no se ocultan.

## Validación

La ejecución final de `python -m pytest -q` reportó **34 passed**: 8 pruebas base,
5 de HU-02, 6 de HU-04 y 15 de HU-03. Las pruebas cubren autorización,
disponibilidad, doble reserva, datos de perfil, calendario, cancelación y
previsión.

Para reproducir exactamente los pins de `backend/requirements.txt` se recomienda
Python 3.12. En el equipo de validación sólo había Python 3.13/3.14; los pins de
`pydantic-core` y `psycopg2-binary` no tienen rueda compatible y requieren
compilación. La validación funcional se ejecutó con dependencias actuales
compatibles y SQLite.

## Demostración sugerida

1. Abrir la reserva pública y seleccionar un servicio.
2. Mostrar el calendario: día disponible, domingo cerrado y selección de hora.
3. Crear una cita y demostrar el enlace privado de cancelación.
4. Cancelar la cita y mostrar que el cupo reaparece.
5. Acceder como cliente y mostrar próximas citas.
6. Abrir el panel admin y explicar la previsión, sus datos históricos y el MAE.
7. Ejecutar `python -m pytest -q` o mostrar el resultado de 34 pruebas.

## Pendientes posteriores a la entrega

- Obtener las firmas o confirmaciones humanas de Reviewer y QA por etapa.
- Configurar un proveedor real, limitación de solicitudes y auditoría para OTP.
- Usar Python 3.12 en CI o actualizar los pins y probar PostgreSQL.
- Evitar tokens en URL en una versión de producción.
