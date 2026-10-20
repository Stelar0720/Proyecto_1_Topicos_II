# PR: HU-04 — cancelación con enlace privado

- **Rama:** `feature/hu-04-cancelacion-privada`
- **Base:** `feature/hu-02-calendario-dinamico` (PR apilada; incluye HU-02)
- **Revisión:** Alex
- **QA:** Jack

## Objetivo

Permitir que el cliente cancele su cita desde un enlace privado, con
confirmación explícita, liberando el horario con las reglas de disponibilidad
ya existentes.

## Diseño de seguridad

- El token se genera con `secrets.token_urlsafe(32)` (43 caracteres) al crear
  la cita.
- En `appointments.cancel_token_hash` sólo se guarda SHA-256. El token plano se
  devuelve **una vez** en `cancel_url` y se incluye en el mensaje de
  confirmación (modo demo en pruebas).
- La comparación usa `hmac.compare_digest`.
- El token está ligado a una cita: el ID por sí solo no sirve. Sin token → 422;
  token ausente/incorrecto/de otra cita → 404 sin revelar si la cita existe.
- Abrir el enlace hace `GET` de previsualización y **no modifica** la cita. La
  cancelación sólo ocurre con `POST` y el botón de confirmación.
- `cancel.html` usa `noindex` y `referrer: no-referrer` para no filtrar el
  token a CDNs de fuentes.

## Endpoints

| Método | Ruta | Efecto |
|---|---|---|
| GET | `/api/appointments/{id}/cancel?token=...` | Valida y muestra servicio, fecha y nombre. No cancela. |
| POST | `/api/appointments/{id}/cancel` con `{"token":"..."}` | Cancela y libera el horario. |

La creación de citas (`POST /api/appointments` y `POST /api/me/appointments`)
añade `cancel_url` a la respuesta. `FRONTEND_URL` permite construir el enlace
absoluto; si está vacío se devuelve `cancel.html?...` relativo.

## Reglas de cancelación

| Estado de la cita | Resultado | Efecto en el horario |
|---|---|---|
| Futura `pending` o `confirmed` | 200, pasa a `cancelled` | Se libera: el motor ignora canceladas |
| Pasada (`start_at <= ahora`), aún `pending`/`confirmed` | 409 "ya pasó" | Sin cambios |
| `done` (realizada) | 409 "ya fue realizada" | Sin cambios |
| `cancelled` (por enlace o admin) | 409 "ya fue cancelada" | Sin cambios |
| Token inválido, ausente o de otra cita | 404 (o 422 si falta el parámetro) | Sin cambios |

## Pruebas

```bash
cd backend
python -m pytest
```

Resultado real: **19 passed**, 0 fallos.

Casos HU-04:

- dos citas generan tokens distintos, de al menos 40 caracteres, y en BD sólo
  queda un SHA-256 de 64 caracteres;
- ID solo → 422; token incorrecto → 404; token de otra cita → 404;
- abrir el enlace devuelve la previsualización y deja la cita `pending`, con el
  horario aún bloqueado;
- `POST` válido → `cancelled`, el horario reaparece en `/api/availability` y el
  calendario vuelve a 20 cupos;
- segundo intento y previsualización posterior → 409;
- cita pasada, `done` y cancelada por admin → 409 sin cambios.

## Verificación manual realizada

```text
create 201 id=3 cancel.html?id=3&token=... (43 chars)
id only GET 422
wrong token 404
preview 200 {"appointment_id":3,...,"status":"pending"}
slot before cancel False
cancel 200 cancelled
slot after cancel True
second cancel 409
preview after cancel 409
```

En Chromium: el enlace mostró la tarjeta de confirmación con servicio, fecha y
nombre; el botón "Sí, cancelar mi cita" llevó a "Cita cancelada". La reserva
desde `index.html` mostró el enlace privado en la pantalla de éxito.

## Limitaciones

- El token no se puede recuperar después de crear la cita (sólo se almacena el
  hash). Si se pierde el enlace, el cliente debe contactar al negocio; el panel
  admin sigue pudiendo cancelar.
- Las citas creadas antes de esta migración tienen `cancel_token_hash = NULL` y
  no tienen enlace privado.
- El token no expira por tiempo: sigue siendo válido mientras la cita sea
  futura y no esté realizada/cancelada. La regla de cita pasada lo inutiliza.
- El token viaja en el query string del `GET` de previsualización, por lo que
  puede quedar en logs del servidor. Se acepta para esta entrega; una variante
  futura podría usar `POST` también para la previsualización.
- No se enviaron WhatsApp reales: todas las pruebas corren con credenciales
  Twilio vacías y `send_whatsapp` en modo demo.
