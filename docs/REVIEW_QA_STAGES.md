# Revisiones y QA por etapa

Este documento deja evidencia de la revisión técnica y QA ejecutados al integrar
la entrega final. No sustituye la firma o aprobación humana de los integrantes.
Las asignaciones rotan los roles acordados; la revisión registrada aquí fue
asistida por Codex el 2026-10-21 y debe ser presentada como tal.

| Etapa | Alcance | Developer asignado | Reviewer asignado | QA asignado |
|---|---|---|---|---|
| 1 | HU-01 perfil reutilizable y HU-05 próximas citas | Jack | Francisco | Alex |
| 2 | HU-02 calendario y HU-04 cancelación privada | Francisco | Alex | Jack |
| 3 | HU-03 previsión de demanda | Alex | Jack | Francisco |

## Etapa 1 - perfil y próximas citas

**Revisión técnica asistida:** se verificó que el acceso de cliente usa un reto
de un solo uso, que el token es temporal y que `GET /api/me/appointments` filtra
por el cliente autenticado y por citas futuras activas. La reserva autenticada
usa el perfil guardado y mantiene la reserva de visitante por compatibilidad.

**QA asistido:** `test_customer_profile_booking_and_private_upcoming` cubre la
reserva con perfil y la consulta privada; `test_customer_invalid_code_cannot_access_data`
cubre un código incorrecto. Resultado en la ejecución final: aprobado dentro de
la suite de 34 pruebas.

**Riesgo abierto:** el reto de acceso se entrega en modo demo; antes de producción
debe seleccionarse un proveedor de WhatsApp, añadir límites de solicitudes y
confirmar el flujo de entrega real.

## Etapa 2 - calendario y cancelación

**Revisión técnica asistida:** el calendario reutiliza el motor de disponibilidad
en lugar de duplicar reglas. HU-04 almacena sólo el hash SHA-256 del token de
cancelación, requiere `POST` explícito para cancelar y libera el horario al
cambiar la cita a `cancelled`.

**QA asistido:** `test_hu02_calendar.py` cubre días cerrados, cupos, cambio de
mes y conflictos 409. `test_hu04_cancellation.py` añade seis pruebas para token
privado, previsualización sin efectos, cancelación, liberación del horario y
estados no cancelables. Resultado en la ejecución final: aprobado dentro de la
suite de 34 pruebas.

**Riesgo abierto:** el token se transporta en la URL de previsualización y puede
quedar en logs del servidor. Es aceptable para la demostración, no como diseño
final de alta seguridad.

## Etapa 3 - previsión de demanda

**Revisión técnica asistida:** la previsión usa promedio histórico por día de la
semana con ventana configurable de 28 días. Excluye cancelaciones, reporta
advertencias ante datos insuficientes y muestra un backtest MAE. No se presenta
como modelo de IA entrenado ni altera precios o inventario automáticamente.

**QA asistido:** `test_hu03_forecast.py` aporta 15 pruebas deterministas sobre
fechas, estados, datos insuficientes, autenticación, validación de parámetros y
backtest. Resultado en la ejecución final: aprobado dentro de la suite de 34
pruebas.

## Resultado de integración

La suite se ejecutó después de integrar HU-04: `34 passed`. La comprobación se
realizó en Python 3.13 con dependencias compatibles actuales porque los pins
actuales del proyecto requieren Python 3.12 para instalar sin compilación local.

## Aprobaciones humanas pendientes

| Etapa | Reviewer | QA | Estado para firma |
|---|---|---|---|
| 1 | Francisco | Alex | Pendiente de confirmación humana |
| 2 | Alex | Jack | Pendiente de confirmación humana |
| 3 | Jack | Francisco | Pendiente de confirmación humana |
