"""HU-04: enlace privado de cancelación, reglas y liberación del horario."""
import hashlib
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app import models
from app.cancellation import hash_cancel_token
from app.database import SessionLocal
from app.main import app
from app.utils import local_now

client = TestClient(app)


def _next_open_day_at(hour: int):
    day = (local_now() + timedelta(days=1)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    while day.weekday() == 6:
        day += timedelta(days=1)
    return day


def _service_id() -> int:
    db = SessionLocal()
    try:
        return db.query(models.Service).filter_by(name="Corte").one().id
    finally:
        db.close()


def _book(hour: int):
    response = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "+56987654321",
            "service_id": _service_id(),
            "start_at": _next_open_day_at(hour).isoformat(),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _token(cancel_url: str) -> str:
    return parse_qs(urlparse(cancel_url).query)["token"][0]


def _appointment(appt_id: int) -> models.Appointment:
    db = SessionLocal()
    try:
        return db.query(models.Appointment).filter_by(id=appt_id).one()
    finally:
        db.close()


def test_cancel_token_is_random_hashed_and_bound_to_one_appointment():
    first = _book(11)
    second = _book(12)
    assert second["id"] != first["id"]

    first_token = _token(first["cancel_url"])
    second_token = _token(second["cancel_url"])
    assert first_token != second_token
    assert len(first_token) >= 40
    assert first_token not in ("", "1", str(first["id"]))

    db_token = _appointment(first["id"]).cancel_token_hash
    assert db_token == hashlib.sha256(first_token.encode()).hexdigest()
    assert db_token == hash_cancel_token(first_token)
    assert len(db_token) == 64
    assert db_token != first_token  # nunca se persiste el token plano


def test_id_alone_and_wrong_tokens_cannot_cancel():
    appt = _book(11)
    appt_id = appt["id"]
    token = _token(appt["cancel_url"])

    # Sin token: la petición ni siquiera es válida.
    assert client.get(f"/api/appointments/{appt_id}/cancel").status_code == 422
    assert client.post(f"/api/appointments/{appt_id}/cancel", json={}).status_code == 422
    assert client.post(
        f"/api/appointments/{appt_id}/cancel", json={"token": ""}
    ).status_code == 422

    wrong = "x" * len(token)
    assert client.get(
        f"/api/appointments/{appt_id}/cancel", params={"token": wrong}
    ).status_code == 404
    assert client.post(
        f"/api/appointments/{appt_id}/cancel", json={"token": wrong}
    ).status_code == 404
    assert _appointment(appt_id).status == models.STATUS_PENDING


def test_opening_link_does_not_cancel_and_slot_stays_blocked():
    day = _next_open_day_at(11)
    appt = _book(11)
    appt_id = appt["id"]
    token = _token(appt["cancel_url"])
    date_str = day.date().isoformat()

    before = client.get(
        f"/api/availability?service_id={_service_id()}&date={date_str}"
    ).json()
    assert "11:00" not in before

    preview = client.get(
        f"/api/appointments/{appt_id}/cancel", params={"token": token}
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["appointment_id"] == appt_id
    assert body["service_name"] == "Corte"
    assert "customer_phone" not in body  # no expone datos de contacto

    # Abrir el enlace no mutó nada.
    assert _appointment(appt_id).status == models.STATUS_PENDING
    after_preview = client.get(
        f"/api/availability?service_id={_service_id()}&date={date_str}"
    ).json()
    assert "11:00" not in after_preview


def test_explicit_cancel_frees_slot_and_second_attempt_is_rejected():
    day = _next_open_day_at(11)
    appt = _book(11)
    appt_id = appt["id"]
    token = _token(appt["cancel_url"])
    date_str = day.date().isoformat()
    sid = _service_id()

    assert "11:00" not in client.get(
        f"/api/availability?service_id={sid}&date={date_str}"
    ).json()

    cancelled = client.post(
        f"/api/appointments/{appt_id}/cancel", json={"token": token}
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == models.STATUS_CANCELLED
    assert _appointment(appt_id).status == models.STATUS_CANCELLED

    # El motor existente ignora las canceladas: el horario vuelve a aparecer.
    assert "11:00" in client.get(
        f"/api/availability?service_id={sid}&date={date_str}"
    ).json()
    calendar = client.get(
        f"/api/availability/calendar?service_id={sid}&month={day.strftime('%Y-%m')}"
    ).json()
    day_info = {d["date"]: d for d in calendar["days"]}[date_str]
    assert day_info["available_count"] == 20

    repeated = client.post(
        f"/api/appointments/{appt_id}/cancel", json={"token": token}
    )
    assert repeated.status_code == 409
    assert "ya fue cancelada" in repeated.json()["detail"]
    preview = client.get(
        f"/api/appointments/{appt_id}/cancel", params={"token": token}
    )
    assert preview.status_code == 409


def test_token_of_another_appointment_does_not_work():
    first = _book(11)
    other = _book(12)

    first_token = _token(first["cancel_url"])
    assert client.post(
        f"/api/appointments/{other['id']}/cancel", json={"token": first_token}
    ).status_code == 404
    assert _appointment(other["id"]).status == models.STATUS_PENDING


def test_past_done_and_admin_cancelled_appointments_are_rejected():
    token = "t" * 43
    now = local_now()

    db = SessionLocal()
    try:
        past = models.Appointment(
            customer_name="Pasada",
            customer_phone="+56900000001",
            service_id=_service_id(),
            start_at=now - timedelta(days=1),
            end_at=now - timedelta(days=1) + timedelta(minutes=30),
            status=models.STATUS_PENDING,
            cancel_token_hash=hash_cancel_token(token),
        )
        done = models.Appointment(
            customer_name="Realizada",
            customer_phone="+56900000002",
            service_id=_service_id(),
            start_at=_next_open_day_at(15),
            end_at=_next_open_day_at(15) + timedelta(minutes=30),
            status=models.STATUS_DONE,
            cancel_token_hash=hash_cancel_token(token),
        )
        db.add_all([past, done])
        db.commit()
        db.refresh(past)
        db.refresh(done)
        past_id, done_id = past.id, done.id
    finally:
        db.close()

    past_response = client.post(
        f"/api/appointments/{past_id}/cancel", json={"token": token}
    )
    assert past_response.status_code == 409
    assert "ya pasó" in past_response.json()["detail"]
    assert _appointment(past_id).status == models.STATUS_PENDING

    done_response = client.post(
        f"/api/appointments/{done_id}/cancel", json={"token": token}
    )
    assert done_response.status_code == 409
    assert "ya fue realizada" in done_response.json()["detail"]
    assert _appointment(done_id).status == models.STATUS_DONE

    # Cancelada por el panel admin: el enlace ya no la vuelve a cancelar.
    appt = _book(16)
    admin_cancel = client.patch(
        f"/api/admin/appointments/{appt['id']}",
        headers={"X-Admin-Token": "test-token"},
        json={"status": models.STATUS_CANCELLED},
    )
    assert admin_cancel.status_code == 200
    admin_response = client.post(
        f"/api/appointments/{appt['id']}/cancel",
        json={"token": _token(appt["cancel_url"])},
    )
    assert admin_response.status_code == 409
    assert "ya fue cancelada" in admin_response.json()["detail"]
