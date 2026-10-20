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
