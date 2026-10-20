"""HU-02: calendario dinámico, días cerrados, cupos y conflictos."""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal
from app.main import app
from app.utils import local_now

client = TestClient(app)


def _next_open_day_at(hour: int) -> datetime:
    day = (local_now() + timedelta(days=1)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    while day.weekday() in {6}:  # domingo cerrado por configuración por defecto
        day += timedelta(days=1)
    return day


def _next_weekday(weekday: int):
    day = (local_now() + timedelta(days=1)).date()
    while day.weekday() != weekday:
        day += timedelta(days=1)
    return day


def _calendar(service_id: int, day) -> dict:
    response = client.get(
        f"/api/availability/calendar?service_id={service_id}&month={day.strftime('%Y-%m')}"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["month"] == day.strftime("%Y-%m")
    days = {item["date"]: item for item in body["days"]}
    assert len(days) >= 28
    return {"body": body, "days": days}


def _service_id(name: str = "Corte") -> int:
    db = SessionLocal()
    try:
        return db.query(models.Service).filter_by(name=name).one().id
    finally:
        db.close()


def _create_service(name: str, duration_min: int) -> int:
    db = SessionLocal()
    try:
        service = models.Service(name=name, duration_min=duration_min, price=0, active=True)
        db.add(service)
        db.commit()
        db.refresh(service)
        return service.id
    finally:
        db.close()


def test_calendar_marks_closed_days_and_past_days():
    sid = _service_id()
    closed_day = _next_weekday(6)  # domingo
    closed_days = _calendar(sid, closed_day)["days"]
    assert closed_days[closed_day.isoformat()]["status"] == "closed"
    assert closed_days[closed_day.isoformat()]["available_count"] == 0
    assert client.get(
        f"/api/availability?service_id={sid}&date={closed_day.isoformat()}"
    ).json() == []

    yesterday = (local_now() - timedelta(days=1)).date()
    past_days = _calendar(sid, yesterday)["days"]
    assert past_days[yesterday.isoformat()]["status"] == "past"
    assert past_days[yesterday.isoformat()]["available_count"] == 0
    assert client.get(
        f"/api/availability?service_id={sid}&date={yesterday.isoformat()}"
    ).json() == []


def test_calendar_depends_on_service_duration():
    sid_30 = _service_id()
    sid_60 = _create_service("Corte largo", 60)
    day = _next_open_day_at(11).date()

    cal_30 = _calendar(sid_30, day)
    cal_60 = _calendar(sid_60, day)

    assert cal_30["body"]["duration_min"] == 30
    assert cal_60["body"]["duration_min"] == 60
    day_30 = cal_30["days"][day.isoformat()]
    day_60 = cal_60["days"][day.isoformat()]
    assert day_30["status"] == day_60["status"] == "available"
    # Inicios cada 30 min entre 10:00 y 20:00: 20 cupos de 30 min; con 60 min
    # el último inicio válido es 19:00, así que quedan 19 cupos.
    assert day_30["available_count"] == 20
    assert day_60["available_count"] == 19


def test_calendar_marks_full_day_and_booking_conflicts():
    sid = _service_id()
    day = _next_open_day_at(11)
    db = SessionLocal()
    try:
        db.add(
            models.Appointment(
                customer_name="Bloqueo",
                customer_phone="+56900000000",
                service_id=sid,
                start_at=day.replace(hour=10, minute=0),
                end_at=day.replace(hour=20, minute=0),
                status=models.STATUS_CONFIRMED,
            )
        )
        db.commit()
    finally:
        db.close()

    day_info = _calendar(sid, day.date())["days"][day.date().isoformat()]
    assert day_info["status"] == "full"
    assert day_info["available_count"] == 0
    assert client.get(
        f"/api/availability?service_id={sid}&date={day.date().isoformat()}"
    ).json() == []

    conflict = client.post(
        "/api/appointments",
        json={
            "customer_name": "Cliente",
            "customer_phone": "+56911111111",
            "service_id": sid,
            "start_at": day.isoformat(),
        },
    )
    assert conflict.status_code == 409
    assert "no está disponible" in conflict.json()["detail"]


def test_calendar_updates_when_month_changes():
    sid = _service_id()
    today = local_now().date()
    next_month_day = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    previous_month_day = today.replace(day=1) - timedelta(days=1)

    next_month = _calendar(sid, next_month_day)
    assert next_month["body"]["month"] == next_month_day.strftime("%Y-%m")
    assert all(day.startswith(next_month_day.strftime("%Y-%m")) for day in next_month["days"])

    previous_month = _calendar(sid, previous_month_day)
    assert previous_month["body"]["month"] == previous_month_day.strftime("%Y-%m")
    assert all(item["status"] == "past" for item in previous_month["days"].values())


def test_calendar_count_updates_after_booking_and_conflict_is_visible():
    sid = _service_id()
    day = _next_open_day_at(11)
    before = _calendar(sid, day.date())["days"][day.date().isoformat()]
    assert before["available_count"] == 20

    created = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "+56987654321",
            "service_id": sid,
            "start_at": day.isoformat(),
        },
    )
    assert created.status_code == 201, created.text

    after = _calendar(sid, day.date())["days"][day.date().isoformat()]
    assert after["available_count"] == before["available_count"] - 1
    assert after["status"] == "available"

    repeated = client.post(
        "/api/appointments",
        json={
            "customer_name": "Diego",
            "customer_phone": "+56912345678",
            "service_id": sid,
            "start_at": day.isoformat(),
        },
    )
    assert repeated.status_code == 409
