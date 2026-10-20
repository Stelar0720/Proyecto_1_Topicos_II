# PR: HU-02 — calendario dinámico de disponibilidad

- **Rama:** `feature/hu-02-calendario-dinamico`
- **Base:** `main`
- **Revisión:** Alex
- **QA:** Jack

## Objetivo

Permitir que el cliente elija la fecha con un calendario mensual que refleja la
disponibilidad real del servicio seleccionado, sin crear un segundo motor de
horarios.

## Cambios

- `backend/app/availability.py`: se extrajo `_free_slots()` como única regla de
  slots; `generate_slots()` y el nuevo `generate_calendar()` la reutilizan.
  El calendario calcula los estados `available`, `full`, `closed` y `past`.
- `GET /api/availability/calendar?service_id=&month=YYYY-MM`: devuelve
  `service_id`, `duration_min`, `month` y un estado por día con
  `available_count`.
- `frontend/index.html`: calendario mensual con navegación, leyenda
  (con cupos / sin cupos / cerrado), días pasados deshabilitados, selección de
  día y carga de horarios. Al cambiar de servicio o mes se recargan los estados.
- El conflicto de reserva (HTTP 409) ahora muestra un mensaje explícito,
  refresca cupos y calendario y deja elegir otro horario.
- `POST /api/appointments` y `POST /api/me/appointments` siguen revalidando en
  el servidor con `is_slot_free()` al confirmar.

## Contrato del calendario

```json
{
  "service_id": 1,
  "duration_min": 30,
  "month": "2026-10",
  "days": [
    {"date": "2026-10-19", "status": "available", "available_count": 18},
    {"date": "2026-10-20", "status": "full", "available_count": 0},
    {"date": "2026-10-25", "status": "closed", "available_count": 0},
    {"date": "2026-10-01", "status": "past", "available_count": 0}
  ]
}
```

Precedencia acordada: `past` > `closed` > `available` > `full`. Un día pasado
se informa como `past` aunque además sea domingo.

## Pruebas

```bash
cd backend
python -m pytest
```

Resultado real: **19 passed** (8 pruebas previas, 5 de HU-02 y 6 de HU-04),
0 fallos, 21 warnings de dependencias (`datetime.utcnow` y Starlette).

Casos HU-02:

- días cerrados y pasados, con `available_count == 0` y `GET /api/availability`
  vacío;
- la duración cambia los cupos (30 min: 20 inicios; 60 min: 19 inicios);
- día lleno marcado `full` y reserva rechazada con 409;
- el calendario cambia al consultar otro mes (mes futuro y mes pasado);
- reservar descuenta un cupo y el segundo intento en el mismo horario da 409.

## Verificación manual realizada

1. `seed.py` + `uvicorn` con `DATABASE_URL` temporal y Twilio vacío.
2. `GET /api/availability/calendar?service_id=1&month=2026-10` devolvió días
   `past`, domingo `closed` y cupos reales.
3. Navegador Chromium sobre `frontend/index.html`:
   servicio → calendario de noviembre de 2026 (30 celdas, 25 disponibles,
   domingos cerrados) → día 20 → horarios → formulario → confirmación.

## Limitaciones

- No hay prueba E2E automatizada del navegador; la verificación visual se hizo
  manualmente con Chromium headless.
- El calendario cuenta inicios de slot, no cupos simultáneos: el negocio sigue
  siendo de un solo profesional.
- Los días se calculan en `America/Santiago`; un navegador en otra zona puede
  mostrar el mismo `YYYY-MM-DD` con distinto "hoy".
