# PR: HU-03 — previsión de demanda para planificar capacidad y precios

- **Rama:** `feature/hu-03-prevision-demanda`
- **Base:** `main`
- **Revisión:** Jack
- **QA:** Francisco

## Objetivo

Que el administrador vea el histórico de reservas y una previsión claramente
diferenciada de los próximos siete días, para apoyar decisiones de capacidad y
precios. La funcionalidad **no** modifica precios ni capacidad automáticamente.

## Método (simple, reproducible y explicable)

**Promedio por día de la semana** sobre una ventana histórica móvil.

1. Se toma la **fecha de corte** = inicio del día actual (`America/Santiago`).
2. Ventana histórica por defecto: **28 días** anteriores al corte.
3. Para cada día futuro se promedia la demanda de ese **mismo día de la semana**
   dentro de la ventana.
   - Todos los días de la ventana cuentan como observación: un día abierto sin
     citas aporta 0 (evita inflar la previsión).
   - Si ese día de la semana no tuviera observaciones, se usa la media general
     de la ventana (`basis = overall_average`).
   - Sin ninguna observación no se pronostica: `forecast = null`
     (`basis = no_data`).
4. Los **días cerrados** (`closed_weekdays`, por defecto domingo) se pronostican
   como `0` y se marcan `closed = true`; nunca se inventa demanda para ellos.

No se entrena ningún modelo ni se usa una API de IA.

### Qué es "demanda" y cómo se tratan los estados

- Demanda de un día = cantidad de citas cuyo **día de inicio** es ese día y cuyo
  estado es `pending`, `confirmed` o `done`.
- **Las canceladas (`cancelled`) se excluyen**: no representan demanda efectiva.
  Las citas eliminadas no existen en la base y tampoco se cuentan.
- Se usa **sólo información disponible antes del corte**: se exige
  `start_at < corte` **y** `created_at < corte`. Una cita creada después del
  corte no altera el pasado.

### Comparación retrospectiva (backtest)

Cuando hay al menos 14 días con datos antes del corte retrospectivo, se
recalcula la previsión como si el corte fuera 7 días antes y se compara contra
los resultados ya conocidos de esos 7 días. Se informa el **MAE** (error
absoluto medio, en citas por día) sobre los días abiertos evaluados.

## Cambios

- `backend/app/forecast.py` (nuevo): cálculo de demanda, promedio por día de la
  semana, días cerrados, advertencias, backtest y `build_forecast()`.
- `backend/app/routers/admin.py`: `GET /api/admin/forecast` (protegido por la
  dependencia `require_admin` del router).
- `backend/app/schemas.py`: esquemas `DemandForecastOut`, `ForecastDayOut`,
  `ForecastHistoryDayOut`, `ForecastWarningOut`, `ForecastBacktestOut`.
- `frontend/admin.html`: tarjeta "Previsión de demanda" con histórico (barras
  azules), previsión (barras cian punteadas), leyenda, advertencias, MAE del
  backtest y nota de que no cambia precios ni capacidad.
- `backend/seed_forecast_demo.py` (nuevo): datos **sintéticos** marcados con
  `notes = "[SINTÉTICO HU-03]"`; `--clear` elimina sólo esas filas.
- `backend/tests/conftest.py`: ruta de la base de pruebas portátil
  (`tempfile.gettempdir()`); la ruta fija `/tmp` no existe en Windows.
- `backend/tests/test_hu03_forecast.py` (nuevo): 15 pruebas deterministas.

## Contrato

`GET /api/admin/forecast?history_days=28&days=7` — cabecera `X-Admin-Token`.

```json
{
  "cutoff": "2026-10-21",
  "history_start": "2026-09-23",
  "history_end": "2026-10-20",
  "history_days": 28,
  "forecast_days": 7,
  "method": "Promedio de la demanda por día de la semana...",
  "demand_definition": "Se cuenta una cita por su día de inicio si su estado...",
  "included_statuses": ["confirmed", "done", "pending"],
  "excluded_statuses": ["cancelled"],
  "closed_weekdays": [6],
  "observed_days": 24,
  "observed_appointments": 48,
  "warnings": [],
  "history": [{"date": "2026-09-23", "demand": 2, "closed": false}],
  "forecast": [
    {"date": "2026-10-21", "forecast": 2.0, "closed": false, "basis": "weekday_average"},
    {"date": "2026-10-25", "forecast": 0.0, "closed": true, "basis": "closed"}
  ],
  "backtest": {"cutoff": "2026-10-14", "days": 7, "evaluated_days": 6, "mae": 0.0}
}
```

`basis` posibles: `weekday_average`, `overall_average`, `closed`, `no_data`.
`backtest` es `null` si no hay datos suficientes.
`observed_days` cuenta días con al menos una cita (se usa para la advertencia de
pocos datos); el promedio sí considera todos los días de la ventana, incluidos
los que tienen demanda 0.

## Pruebas

```bash
cd backend
python -m pytest
```

Resultado real (Windows, Python 3.14, dependencias actuales sin pins porque las
versiones fijadas de `pydantic-core` y `psycopg2-binary` no compilan en 3.14):

```text
28 passed, 10 warnings in 2.72s
```

15 pruebas nuevas cubren:

- cálculo determinista del promedio por día de la semana (fechas fijas);
- fechas exactas de los próximos 7 días;
- estados incluidos (`pending`, `confirmed`, `done`) y exclusión de `cancelled`;
- días abiertos sin citas pronosticados como 0;
- citas creadas después del corte y citas futuras no cuentan como histórico;
- días cerrados con previsión 0 y marca `closed`;
- sin datos: advertencia `no_data` y previsión `null` (no se inventa demanda);
- pocos datos: advertencia `insufficient_data`;
- backtest con MAE conocido (demanda constante 2/día → MAE 0.0);
- acceso administrativo: 422 sin cabecera, 401 con token incorrecto, 200 con el
  correcto;
- validación de parámetros (`history_days` 7–90, `days` 1–14).

## Verificación manual realizada

Con base temporal y `ADMIN_TOKEN` de demo, Twilio vacío:

```bash
python seed_forecast_demo.py   # datos SINTÉTICOS, no historial real
```

El script insertó 104 filas sintéticas; el endpoint devolvió, sobre la ventana de
28 días (24 días observados, 48 citas contadas):

- histórico 2026-10-12…2026-10-20 con demanda 2, 1, 2, 1, 3, 3, 0 (domingo
  cerrado), 2, 1;
- previsión 2026-10-21…2026-10-27: 2.0, 1.0, 3.0, 3.0, 0.0 (domingo cerrado),
  2.0, 1.0;
- backtest con corte 2026-10-14: 6 días evaluados, MAE 0.0;
- `GET` sin cabecera → 422, token incorrecto → 401.

Los datos sintéticos se eliminaron al terminar (`*.db` está ignorado por git).
También se validó la sintaxis del JavaScript del panel con `node --check`.

## Limitaciones

- El promedio por día de la semana no captura tendencias, feriados, promociones,
  estacionalidad ni cambios de capacidad.
- Con menos de 14 días con datos la previsión es orientativa (se advierte); sin
  datos no hay cifra.
- La ventana de 28 días pondera igual días antiguos y recientes.
- Un día cerrado se informa con previsión 0; si el negocio abriera ese día, la
  previsión no lo sabría hasta que exista configuración por fecha.
- El backtest usa el mismo método para evaluarse (no valida contra un modelo
  alternativo) y no corrige por días cerrados ni feriados.
- La fecha de corte depende de la zona horaria configurada; navegadores en otra
  zona pueden mostrar un "hoy" distinto.
- No hay prueba E2E automatizada del navegador.
