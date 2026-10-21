# Guía para reproducir pruebas - CitaFácil

## Estado de referencia y evidencia verificada

La guía se preparó para la revisión Git:

```text
1e14b3c045e385343fc1809d72b2db9026c86b3d
```

En esta revisión se ejecutó, desde `backend/`, el siguiente comando en un
entorno aislado:

```text
python -m pytest -q -p no:cacheprovider
```

Resultado verificado: **34 passed, 20 warnings, código de salida 0**.

La ejecución verificada fue una alternativa de compatibilidad, no una
reproducción exacta de `requirements.txt`:

| Elemento | Ejecución verificada |
|---|---|
| Python | 3.13.1 |
| FastAPI | 0.157.0 |
| SQLAlchemy | 2.1.5 |
| Pydantic | 2.14.1 |
| pydantic-settings | 2.16.1 |
| pytest | 9.1.1 |
| httpx | 0.28.1 |
| Base de datos | SQLite temporal |
| Twilio | Sin credenciales; modo demo |

El README todavía menciona **19 passed (Python 3.12)**. Esa cifra quedó
desactualizada: corresponde a una etapa anterior. `FINAL_PROJECT_REPORT.md`,
las cuatro colecciones de pruebas y la ejecución anterior indican 34 al incluir
HU-03 y HU-04.

## 1. Reproducción exacta con las versiones fijadas

### Requisito principal

Use **Python 3.12.x**. `backend/requirements.txt` fija FastAPI 0.111.0,
SQLAlchemy 2.0.30, Pydantic 2.7.4, pytest 8.2.2, httpx 0.27.0 y
`psycopg2-binary==2.9.9`, entre otras dependencias. El historial de la
aplicación documenta Python 3.12 como el entorno usado con esos pins.

No presente una instalación en Python 3.13/3.14 con librerías actualizadas como
reproducción exacta. En este equipo, los pins de `pydantic-core` y
`psycopg2-binary` no se instalaron en las versiones de Python disponibles:
intentaron compilar y `psycopg2-binary` pidió `pg_config`.

### Comprobación de la revisión

Desde la raíz del repositorio:

```powershell
git rev-parse HEAD
```

```bash
git rev-parse HEAD
```

Debe devolver el hash de la sección anterior. Si devuelve otro, anótelo junto
con la salida de pruebas; los resultados sólo son comparables si se sabe qué
revisión se ejecutó.

### Windows PowerShell - instalación exacta

Desde la raíz:

```powershell
py -3.12 --version
Set-Location backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Si la política de ejecución bloquea la activación, no cambie políticas globales;
use directamente `\.venv\Scripts\python.exe` en los comandos siguientes.

### Linux/macOS - instalación exacta

Desde la raíz:

```bash
python3.12 --version
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

En Linux, si `psycopg2-binary` intenta compilar en vez de descargar una rueda,
instale Python 3.12 compatible y vuelva a crear el entorno. No cambie
`requirements.txt` para llamar a eso una reproducción exacta.

### Variables de entorno para pruebas

No se requieren secretos. El archivo `tests/conftest.py`, cargado antes de la
aplicación, fuerza estas variables para cada ejecución:

```text
DATABASE_URL=sqlite:///<directorio-temporal>/citafacil_test.db
ADMIN_TOKEN=test-token
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=
```

La fixture `fresh_db` borra y recrea las tablas de esa base temporal antes y
después de cada prueba, y agrega un servicio `Corte`. No configure credenciales
reales de Twilio para pruebas: aunque las tenga en `.env`, `conftest.py` las
vacía. La ruta temporal se construye con `tempfile.gettempdir()`, por lo que es
portable entre Windows, Linux y macOS.

## 2. Ejecución de la suite exacta

Todos los comandos de esta sección se ejecutan desde `backend/`, con el entorno
virtual activado.

| Objetivo | Comando |
|---|---|
| Suite completa | `python -m pytest -q` |
| Sin caché de pytest | `python -m pytest -q -p no:cacheprovider` |
| Base, perfil y reserva | `python -m pytest tests/test_booking.py -q` |
| Calendario HU-02 | `python -m pytest tests/test_hu02_calendar.py -q` |
| Cancelación HU-04 | `python -m pytest tests/test_hu04_cancellation.py -q` |
| Previsión HU-03 | `python -m pytest tests/test_hu03_forecast.py -q` |
| Una prueba individual | `python -m pytest tests/test_hu03_forecast.py::test_backtest_reports_mae_when_enough_data -q` |

En PowerShell sin activar el entorno, sustituya `python` por
`.\.venv\Scripts\python.exe`. En Linux/macOS sin activarlo, use
`.venv/bin/python`.

### Guardar salida y código de retorno

Desde `backend/`, PowerShell:

```powershell
python -m pytest -q -p no:cacheprovider 2>&1 | Tee-Object -FilePath pytest-output.txt
$exitCode = $LASTEXITCODE
"PYTEST_EXIT_CODE=$exitCode" | Tee-Object -FilePath pytest-exit-code.txt
exit $exitCode
```

Desde `backend/`, Linux/macOS:

```bash
set -o pipefail
python -m pytest -q -p no:cacheprovider 2>&1 | tee pytest-output.txt
exit_code=${PIPESTATUS[0]}
printf 'PYTEST_EXIT_CODE=%s\n' "$exit_code" | tee pytest-exit-code.txt
exit "$exit_code"
```

Los archivos generados son evidencia local de la ejecución. No los suba si
contienen datos no deseados; las pruebas no usan secretos ni producción.

## 3. Ejecución alternativa documentada (no exacta)

Esta ruta sólo sirve si no se dispone de Python 3.12 y se necesita verificar la
lógica en SQLite. Fue la ruta usada para obtener el resultado de 34 pruebas en
esta revisión. Instala versiones actuales compatibles, distintas de las fijadas.

Desde `backend/` en PowerShell, con Python 3.13:

```powershell
py -3.13 -m venv .venv-alt
.\.venv-alt\Scripts\python.exe -m pip install fastapi "uvicorn[standard]" SQLAlchemy pydantic pydantic-settings python-dotenv twilio APScheduler httpx tzdata pytest
.\.venv-alt\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

En Linux/macOS, con un Python compatible instalado:

```bash
python3 -m venv .venv-alt
.venv-alt/bin/python -m pip install fastapi 'uvicorn[standard]' SQLAlchemy pydantic pydantic-settings python-dotenv twilio APScheduler httpx tzdata pytest
.venv-alt/bin/python -m pytest -q -p no:cacheprovider
```

Esta alternativa **no prueba** la matriz exacta de versiones del proyecto ni
PostgreSQL. Registre siempre las versiones obtenidas con:

```bash
python -m pip show fastapi SQLAlchemy pydantic pydantic-settings pytest httpx psycopg2-binary
```

## 4. Relación entre historias y pruebas

| Historia / área | Archivo | Pruebas y comportamiento verificado |
|---|---|---|
| Base, HU-01 y HU-05 | `tests/test_booking.py` | Teléfono válido/inválido; reserva y conflicto 409; slot retirado; validación 422; token admin; `test_customer_profile_booking_and_private_upcoming`; `test_customer_invalid_code_cannot_access_data`. |
| HU-02 calendario | `tests/test_hu02_calendar.py` | Días cerrados/pasados; duración de servicio y 20/19 inicios; día lleno; conflicto 409; cambio de mes; cupo que disminuye y reintento rechazado. |
| HU-04 cancelación | `tests/test_hu04_cancellation.py` | Token aleatorio con hash; ID/token erróneo rechazado; GET sin cancelación; POST libera slot; segundo intento rechazado; token de otra cita; citas pasadas, realizadas o previamente canceladas. |
| HU-03 previsión | `tests/test_hu03_forecast.py` | Promedio por día de semana; siete días; días cerrados; sin datos; estados incluidos/excluidos; información posterior al corte; histórico/futuro; advertencias; MAE de backtest; autorización admin y parámetros. |

El conteo actual es 34: 8 en `test_booking.py`, 5 en
`test_hu02_calendar.py`, 6 en `test_hu04_cancellation.py` y 15 en
`test_hu03_forecast.py`.

## 5. Pruebas manuales locales

Las pruebas manuales son complementarias: no sustituyen la suite ni deben
presentarse como automatizadas.

### Preparar una base demo separada

Desde `backend/` en PowerShell:

```powershell
$env:DATABASE_URL = "sqlite:///./citafacil-demo.db"
$env:ADMIN_TOKEN = "demo-admin-token"
$env:TWILIO_ACCOUNT_SID = ""
$env:TWILIO_AUTH_TOKEN = ""
$env:TWILIO_WHATSAPP_FROM = ""
python seed.py
python seed_forecast_demo.py
python -m uvicorn app.main:app --reload
```

En Linux/macOS:

```bash
export DATABASE_URL='sqlite:///./citafacil-demo.db'
export ADMIN_TOKEN='demo-admin-token'
export TWILIO_ACCOUNT_SID=''
export TWILIO_AUTH_TOKEN=''
export TWILIO_WHATSAPP_FROM=''
python seed.py
python seed_forecast_demo.py
python -m uvicorn app.main:app --reload
```

Abra `frontend/index.html?api=http://localhost:8000` y
`frontend/admin.html?api=http://localhost:8000`. No abra el frontend sin el
parámetro `api`, porque por defecto apunta a una URL de Render.

| Flujo | Pasos | Resultado esperado |
|---|---|---|
| Reserva y calendario | Elegir servicio, fecha futura disponible, hora, nombre y teléfono chileno válido; reservar. | La cita se crea y el horario deja de estar disponible. Un segundo intento del mismo horario recibe un conflicto. |
| Cancelación | Abrir el enlace privado mostrado en el resultado de la reserva y confirmar. | Abrirlo primero no modifica la cita; confirmar cambia a `cancelled` y el slot reaparece. |
| Perfil y próximas citas | Solicitar acceso con el teléfono usado; tomar el OTP del log de modo demo; completar el nombre si se solicita; abrir próximas citas. | Sólo aparecen las citas activas y futuras de ese cliente. |
| Previsión | Iniciar sesión en `admin.html` con `demo-admin-token` tras ejecutar `seed_forecast_demo.py`. | Se ven historial y siete días de pronóstico sobre datos marcados como sintéticos; puede aparecer MAE si hay datos suficientes. |

Para eliminar únicamente los datos sintéticos de previsión de esa base demo,
ejecute `python seed_forecast_demo.py --clear` con el mismo `DATABASE_URL`.
No ejecute esa acción contra una base que no sea de demostración.

## 6. Problemas frecuentes y soluciones verificadas

| Problema | Causa probable | Solución |
|---|---|---|
| `No matching distribution` o compilación de `pydantic-core`/`psycopg2-binary` | Python 3.13/3.14 con pins preparados para Python 3.12. | Repetir la ruta exacta con Python 3.12. Como alternativa no exacta, usar el entorno `.venv-alt` descrito arriba. |
| `pg_config executable not found` | `psycopg2-binary==2.9.9` intenta compilar en lugar de usar una rueda. | Usar Python 3.12 compatible para la reproducción exacta. No sustituir ese paquete y llamar al resultado reproducción exacta. |
| `ModuleNotFoundError: app` | Se ejecutó pytest desde la raíz en vez de `backend/`. | Cambiar a `backend/` y ejecutar `python -m pytest`. |
| Tests con datos inesperados | Se está usando una base persistente o se importó la app antes de fijar variables. | Ejecutar pytest normal: `conftest.py` define la URL temporal antes de importar `app.*` y recrea las tablas. |
| Intento de WhatsApp real | Hay credenciales locales de Twilio. | Las pruebas las vacían. Para la demo, exportar las tres variables vacías antes de iniciar Uvicorn. |
| `401` en el panel admin | El token no coincide. | En la demo local usar `demo-admin-token`; en tests se fuerza `test-token`. |
| Calendario no apunta al backend local | El frontend conserva una API en `localStorage` o usa Render por defecto. | Abrir con `?api=http://localhost:8000` o usar “Configurar API” en el pie de página. |

## 7. Limitaciones de la validación

- La suite actual fue verificada en SQLite temporal; **PostgreSQL no fue probado**
  en esta validación.
- La ejecución de 34 pruebas en Python 3.13 usa versiones alternativas; no
  sustituye una ejecución exacta en Python 3.12 con los pins.
- No se probaron envíos reales de WhatsApp; se forzó el modo demo.
- Las advertencias actuales proceden de APIs deprecadas de Starlette/TestClient
  y de `datetime.utcnow()` en SQLAlchemy. No hicieron fallar la suite, pero
  deben planificarse para mantenimiento.
- Las aprobaciones humanas de Reviewer y QA siguen pendientes; los resultados
  técnicos no equivalen a una firma humana.
