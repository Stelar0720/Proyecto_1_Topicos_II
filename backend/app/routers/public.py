"""Endpoints públicos: config, servicios, disponibilidad y creación de reservas."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..availability import generate_calendar, generate_slots, is_slot_free
from ..cancellation import (
    appointment_with_cancel_url,
    cancel_url,
    cancellation_error,
    hash_cancel_token,
    new_cancel_token,
    token_matches,
)
from ..config import settings
from ..database import get_db
from ..notifications import confirmation_message, send_whatsapp

router = APIRouter(prefix="/api", tags=["Público"])


@router.get("/config", response_model=schemas.ConfigOut, summary="Configuración del negocio")
def get_config():
    return schemas.ConfigOut(
        business_name=settings.business_name,
        timezone=settings.business_timezone,
        currency=settings.currency,
        open_hour=settings.open_hour,
        close_hour=settings.close_hour,
        slot_interval_minutes=settings.slot_interval_minutes,
        closed_weekdays=sorted(settings.closed_weekdays_set),
    )


@router.get("/services", response_model=list[schemas.ServiceOut], summary="Servicios activos")
def get_services(db: Session = Depends(get_db)):
    return crud.list_services(db, only_active=True)


@router.get(
    "/availability/calendar",
    response_model=schemas.AvailabilityCalendarOut,
    summary="Calendario mensual de disponibilidad",
)
def get_availability_calendar(
    service_id: int = Query(..., description="ID del servicio"),
    month: str = Query(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Mes en formato YYYY-MM",
    ),
    db: Session = Depends(get_db),
):
    """Estado de cada día del mes para el servicio y su duración.

    ``available`` tiene cupos, ``full`` no tiene cupos, ``closed`` es día no
    laboral y ``past`` es anterior a hoy. La regla se calcula con el mismo motor
    que ``GET /api/availability``.
    """
    service = crud.get_service(db, service_id)
    if not service or not service.active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    year, month_number = (int(part) for part in month.split("-"))
    try:
        days = generate_calendar(db, service, year, month_number)
    except ValueError:
        raise HTTPException(status_code=400, detail="Mes inválido.")
    return {
        "service_id": service.id,
        "duration_min": service.duration_min,
        "month": month,
        "days": days,
    }


@router.get("/availability", response_model=list[str], summary="Horarios disponibles")
def get_availability(
    service_id: int = Query(..., description="ID del servicio"),
    day: date = Query(..., alias="date", description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    service = crud.get_service(db, service_id)
    if not service or not service.active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    return generate_slots(db, service, day)


@router.post(
    "/appointments",
    response_model=schemas.AppointmentOut,
    status_code=201,
    summary="Crear una reserva",
)
def create_appointment(payload: schemas.AppointmentCreate, db: Session = Depends(get_db)):
    service = crud.get_service(db, payload.service_id)
    if not service or not service.active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    if not is_slot_free(db, service, payload.start_at):
        raise HTTPException(
            status_code=409,
            detail="Ese horario ya no está disponible. Por favor elige otro.",
        )
    end_at = payload.start_at + timedelta(minutes=service.duration_min)
    token = new_cancel_token()
    appt = crud.create_appointment(
        db, payload, service, end_at, cancel_token_hash=hash_cancel_token(token)
    )
    link = cancel_url(appt.id, token)

    # Confirmación por WhatsApp (real si Twilio está configurado; simulada si no)
    body = confirmation_message(
        settings.business_name, appt.customer_name, service.name, appt.start_at, link
    )
    send_whatsapp(appt.customer_phone, body)
    return appointment_with_cancel_url(appt, token)


INVALID_CANCEL_LINK = "Enlace de cancelación inválido."


@router.get(
    "/appointments/{appt_id}/cancel",
    response_model=schemas.CancelPreviewOut,
    summary="Previsualizar la cancelación (no cancela)",
)
def preview_cancellation(
    appt_id: int,
    token: str = Query(..., description="Token privado del enlace de cancelación"),
    db: Session = Depends(get_db),
):
    """Valida el enlace y devuelve la cita. Abrir el enlace nunca cancela."""
    appt = crud.get_appointment(db, appt_id)
    if not appt or not token_matches(appt, token):
        raise HTTPException(status_code=404, detail=INVALID_CANCEL_LINK)
    denial = cancellation_error(appt)
    if denial:
        raise HTTPException(status_code=409, detail=denial)
    return {
        "appointment_id": appt.id,
        "customer_name": appt.customer_name,
        "service_name": appt.service.name if appt.service else "Servicio",
        "start_at": appt.start_at,
        "status": appt.status,
    }


@router.post(
    "/appointments/{appt_id}/cancel",
    response_model=schemas.AppointmentOut,
    summary="Cancelar una cita con el token privado",
)
def cancel_appointment(
    appt_id: int,
    payload: schemas.CancelRequest,
    db: Session = Depends(get_db),
):
    """Cancelación explícita: exige token y confirmación por POST."""
    appt = crud.get_appointment(db, appt_id)
    if not appt or not token_matches(appt, payload.token):
        raise HTTPException(status_code=404, detail=INVALID_CANCEL_LINK)
    denial = cancellation_error(appt)
    if denial:
        raise HTTPException(status_code=409, detail=denial)
    # El motor de disponibilidad ignora las citas canceladas, así que el
    # horario queda liberado sin tocar sus reglas.
    return crud.set_status(db, appt, models.STATUS_CANCELLED)
