"""HU-03: previsión de demanda con promedio por día de la semana.

Las pruebas puras usan fechas fijas y diccionarios de conteo (deterministas).
Las pruebas de API siembran citas relativas a la fecha local del negocio.
"""
from datetime import date, datetime, time, timedelta

from fastapi.testclient import TestClient

from app import forecast, models
from app.database import SessionLocal
from app.main import app
from app.utils import local_now

client = TestClient(app)
HEADERS = {"X-Admin-Token": "test-token"}

# 2026-01-05 es lunes; el domingo de esa semana es 2026-01-11.
MONDAY = date(2026, 1, 5)


def _service_id() -> int:
    db = SessionLocal()
    try:
        return db.query(models.Service).filter_by(name="Corte").one().id
    finally:
        db.close()


def _seed(
    day: date,
    hour: int,
    status: str = models.STATUS_PENDING,
    created_at: datetime | None = None,
) -> None:
    db = SessionLocal()
    try:
        start = datetime.combine(day, time(hour=hour))
        db.add(
            models.Appointment(
                customer_name="Demo",
                customer_phone="+56900000000",
                service_id=_service_id(),
                start_at=start,
                end_at=start + timedelta(minutes=30),
                status=status,
                created_at=created_at or datetime.combine(day, time(hour=8)),
            )
        )
        db.commit()
    finally:
        db.close()


def _forecast_response(**params) -> dict:
    response = client.get("/api/admin/forecast", headers=HEADERS, params=params)
    assert response.status_code == 200, response.text
    return response.json()


# ---------- Cálculo (pruebas puras, deterministas) ----------
def test_weekday_average_forecast_is_deterministic():
    counts = {
        MONDAY: 2,                    # lunes semana 1
        MONDAY + timedelta(days=7): 2,  # lunes semana 2
        MONDAY + timedelta(days=1): 1,  # martes
        MONDAY + timedelta(days=2): 0,  # miércoles sin demanda (día observado)
    }
    result = forecast.forecast_from_counts(counts, MONDAY, days=4)

    assert [item["date"] for item in result] == [
        MONDAY,
        MONDAY + timedelta(days=1),
        MONDAY + timedelta(days=2),
        MONDAY + timedelta(days=3),
    ]
    assert result[0]["forecast"] == 2.0       # media de lunes (2 y 2)
    assert result[1]["forecast"] == 1.0       # media de martes
    assert result[2]["forecast"] == 0.0       # miércoles observado sin demanda
    assert result[3]["forecast"] == 1.25      # jueves sin datos: media general
    assert result[3]["basis"] == "overall_average"


def test_forecast_covers_exactly_the_next_seven_days():
    result = forecast.forecast_from_counts({MONDAY: 3}, MONDAY, days=7)
    dates = [item["date"] for item in result]
    assert dates == [MONDAY + timedelta(days=i) for i in range(7)]


def test_closed_weekday_forecast_is_zero_and_flagged():
    result = forecast.forecast_from_counts(
        {MONDAY: 5}, MONDAY, days=7, closed_weekdays={6}
    )
    sunday = next(item for item in result if item["date"].weekday() == 6)
    assert sunday["closed"] is True
    assert sunday["forecast"] == 0.0
    assert sunday["basis"] == "closed"


def test_no_data_never_invents_demand():
    result = forecast.forecast_from_counts({}, MONDAY, days=7, closed_weekdays={6})
    open_days = [item for item in result if not item["closed"]]
    assert open_days and all(item["forecast"] is None for item in open_days)
    assert all(item["basis"] == "no_data" for item in open_days)


# ---------- Endpoint: fechas, ventana y metadatos ----------
def test_endpoint_returns_next_seven_days_and_metadata():
    body = _forecast_response()
    today = local_now().date()
    assert body["cutoff"] == today.isoformat()
    assert body["history_end"] == (today - timedelta(days=1)).isoformat()
    assert body["history_start"] == (today - timedelta(days=28)).isoformat()
    assert [item["date"] for item in body["forecast"]] == [
        (today + timedelta(days=i)).isoformat() for i in range(7)
    ]
    assert len(body["history"]) == 28
    assert set(body["included_statuses"]) == {"pending", "confirmed", "done"}
    assert body["excluded_statuses"] == ["cancelled"]
    assert body["method"] and body["demand_definition"]


# ---------- Estados incluidos/excluidos y uso exclusivo del histórico ----------
def test_only_pending_confirmed_done_count_as_demand():
    day = local_now().date() - timedelta(days=3)
    _seed(day, 10, models.STATUS_PENDING)
    _seed(day, 11, models.STATUS_PENDING)
    _seed(day, 12, models.STATUS_CONFIRMED)
    _seed(day, 13, models.STATUS_DONE)
    _seed(day, 14, models.STATUS_CANCELLED)

    body = _forecast_response()
    entry = next(item for item in body["history"] if item["date"] == day.isoformat())
    assert entry["demand"] == 4
    assert body["observed_appointments"] == 4


def test_open_days_without_bookings_forecast_zero():
    day = local_now().date() - timedelta(days=3)
    _seed(day, 10)

    body = _forecast_response()
    for item in body["forecast"]:
        forecast_day = date.fromisoformat(item["date"])
        if item["closed"] or forecast_day.weekday() == day.weekday():
            continue
        # Ningún otro día de la semana tiene citas en la ventana: media 0.
        assert item["forecast"] == 0.0


def test_information_created_after_cutoff_is_ignored():
    cutoff_dt = datetime.combine(local_now().date(), time.min)
    day = local_now().date() - timedelta(days=3)
    _seed(day, 10, models.STATUS_PENDING, created_at=cutoff_dt + timedelta(hours=1))

    body = _forecast_response()
    entry = next(item for item in body["history"] if item["date"] == day.isoformat())
    assert entry["demand"] == 0
    assert body["observed_appointments"] == 0


def test_future_appointments_are_not_historical_demand():
    today = local_now().date()
    _seed(today + timedelta(days=1), 10)
    body = _forecast_response()
    assert body["observed_appointments"] == 0


# ---------- Días cerrados ----------
def test_closed_weekdays_are_reported_without_demand():
    body = _forecast_response()
    closed_weekdays = set(body["closed_weekdays"])
    assert closed_weekdays  # la configuración por defecto cierra domingo

    closed_days = [item for item in body["forecast"] if item["date"] and
                   datetime.fromisoformat(item["date"]).weekday() in closed_weekdays]
    for item in closed_days:
        assert item["closed"] is True
        assert item["forecast"] == 0.0
    for item in body["history"]:
        if datetime.fromisoformat(item["date"]).weekday() in closed_weekdays:
            assert item["closed"] is True


# ---------- Pocos datos / sin datos ----------
def test_no_data_warns_and_leaves_forecast_empty():
    body = _forecast_response()
    assert body["observed_days"] == 0
    assert body["warnings"][0]["code"] == "no_data"
    open_days = [item for item in body["forecast"] if not item["closed"]]
    assert all(item["forecast"] is None for item in open_days)
    assert body["backtest"] is None


def test_insufficient_data_warning():
    day = local_now().date() - timedelta(days=3)
    _seed(day, 10)
    _seed(day, 11)

    body = _forecast_response()
    assert body["observed_days"] == 1
    codes = [warning["code"] for warning in body["warnings"]]
    assert "insufficient_data" in codes


# ---------- Comparación retrospectiva (MAE) ----------
def test_backtest_reports_mae_when_enough_data():
    today = local_now().date()
    # 35 días: cubren la ventana retrospectiva completa (28 días) y los 7
    # días que el backtest compara contra resultados conocidos.
    for offset in range(1, 36):
        day = today - timedelta(days=offset)
        _seed(day, 10)
        _seed(day, 11)

    body = _forecast_response()
    assert body["observed_days"] >= forecast.MIN_HISTORY_DAYS
    result = body["backtest"]
    assert result is not None
    closed = set(body["closed_weekdays"])
    back_start = today - timedelta(days=result["days"])
    expected_open_days = sum(
        1
        for i in range(result["days"])
        if (back_start + timedelta(days=i)).weekday() not in closed
    )
    assert result["evaluated_days"] == expected_open_days
    # Demanda constante de 2 por día: la previsión no puede tener error.
    assert result["mae"] == 0.0


# ---------- Acceso administrativo ----------
def test_forecast_requires_admin_token():
    assert client.get("/api/admin/forecast").status_code == 422  # sin cabecera
    assert client.get(
        "/api/admin/forecast", headers={"X-Admin-Token": "malo"}
    ).status_code == 401
    assert client.get("/api/admin/forecast", headers=HEADERS).status_code == 200


# ---------- Parámetros ----------
def test_forecast_rejects_invalid_window():
    assert client.get(
        "/api/admin/forecast", headers=HEADERS, params={"history_days": 1}
    ).status_code == 422
    assert client.get(
        "/api/admin/forecast", headers=HEADERS, params={"days": 30}
    ).status_code == 422
