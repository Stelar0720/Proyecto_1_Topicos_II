# Registro de intervenciones de IA

## 2026-10-19 — HU-01 y HU-05

Codex implementó, a petición de Jack, el perfil autenticado de cliente, verificación por código de un solo uso, reserva autenticada y consulta de próximas citas. La decisión de producto pendiente es el proveedor/operación real de entrega de códigos WhatsApp y la aprobación humana de la PR por Francisco y QA por Alex.

## 2026-10-19 — HU-02

A petición de Francisco, `alosslessdev` (IA) implementó el calendario mensual de
disponibilidad reutilizando el motor de slots existente (sin un segundo motor),
el endpoint `/api/availability/calendar`, la UI de calendario y el manejo
explícito del conflicto 409. Se agregaron 5 pruebas de calendario.

Intervenciones reales:

- La primera expectativa de prueba para un servicio de 60 min era 10 cupos; el
  resultado real fue 19 inicios válidos (10:00–19:00 cada 30 min). Se corrigió
  la prueba, no el motor.
- El entorno del equipo tiene Python 3.14; las versiones fijadas de
  `pydantic-core` no compilan ahí. Las pruebas se ejecutaron en Python 3.12.
- En ese punto de la rama: **13 pruebas, 13 passed**. Twilio quedó vacío, por
  lo que no se enviaron WhatsApp reales.

No se registran aprobaciones humanas: revisión de Alex y QA de Jack pendientes.

## 2026-10-19 — HU-04

A petición de Francisco, `alosslessdev` (IA) implementó la cancelación con
enlace privado: token aleatorio de 32 bytes, hash SHA-256 en base de datos,
previsualización sin efecto, `POST` explícito de cancelación, página
`cancel.html` y reglas documentadas para citas pasadas, realizadas, ya
canceladas y tokens inválidos. Se agregaron 6 pruebas.

Intervenciones y correcciones reales:

- La verificación visual detectó que la clase CSS `.warn` se aplicaba también
  al icono y dejaba un bloque vacío; se separó en `.alert` y se corrigió el
  manejo del mensaje de error.
- Se ejecutaron **19 pruebas: 19 passed**. No se enviaron WhatsApp reales:
  Twilio quedó vacío y `send_whatsapp` operó en modo demo.

No se registran aprobaciones humanas: la revisión de Alex y la validación QA
de Jack están pendientes. Tampoco se registran errores, rechazos ni decisiones
humanas que no hayan ocurrido.

## 2026-10-21 — HU-03

A petición de Jack, la IA implementó la previsión de demanda con promedio por día
de la semana (ventana de 28 días), el endpoint `GET /api/admin/forecast`, la
tarjeta con gráfico histórico/previsión en el panel admin, un generador de datos
sintéticos claramente marcados y 15 pruebas deterministas. No se entrenó ningún
modelo ni se usó una API de IA para predecir.

Intervenciones reales:

- El entorno local tiene Python 3.14; los pins de `pydantic-core` y
  `psycopg2-binary` no compilan ahí. Para ejecutar las pruebas se instalaron
  versiones actuales sin pins en un `.venv` local (no se modificó
  `requirements.txt`).
- `tests/conftest.py` usaba `/tmp/citafacil_test.db`, inexistente en Windows;
  se cambió a `tempfile.gettempdir()` para que la suite corra en ambos sistemas.
- La primera versión de la prueba de backtest sembraba sólo el historial anterior
  al corte retrospectivo y daba MAE 2.0; luego, al promediar también los días sin
  citas, daba 1.0 porque faltaban días de la ventana. Se corrigió la siembra de
  la prueba (no el cálculo) sembrando los 35 días necesarios.
- Resultado real al cierre: **28 pruebas, 28 passed** (13 previas + 15 de HU-03).
  Twilio quedó vacío y no se enviaron WhatsApp reales.

No se registran aprobaciones humanas: revisión de Jack y QA de Francisco
pendientes.
