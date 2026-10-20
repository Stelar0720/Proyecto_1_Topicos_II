"""Lógica de disponibilidad: genera horarios libres y evita el doble-booking."""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from . import models
from .config import settings
from .utils import local_now

DAY_STATUS_AVAILABLE = "available"
DAY_STATUS_FULL = "full"
DAY_STATUS_CLOSED = "closed"
DAY_STATUS_PAST = "past"


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """True si dos intervalos [inicio, fin) se solapan."""
    return a_start < b_end and b_start < a_end


def _booked_between(
    db: Session, start_at: datetime, end_at: datetime
) -> list[models.Appointment]:
    """Citas activas que comienzan en [start_at, end_at)."""
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.status != models.STATUS_CANCELLED,
            models.Appointment.start_at >= start_at,
            models.Appointment.start_at < end_at,
        )
        .all()
    )


def _booked_that_day(db: Session, day: date) -> list[models.Appointment]:
    day_start = datetime.combine(day, time.min)
    next_day = datetime.combine(day + timedelta(days=1), time.min)
    return _booked_between(db, day_start, next_day)


def _free_slots(
    service: models.Service,
    day: date,
    booked: list[models.Appointment],
    now: datetime,
) -> list[str]:
    """Aplica las reglas del negocio a un día concreto.

    Única implementación del motor de horarios: la usan tanto la disponibilidad
    de un día como el calendario mensual, para no crear dos fuentes de verdad.
    """
    if day.weekday() in settings.closed_weekdays_set:
        return []

    duration = timedelta(minutes=service.duration_min)
    open_dt = datetime.combine(day, time(hour=settings.open_hour))
    close_dt = datetime.combine(day, time(hour=settings.close_hour))

    slots: list[str] = []
    cursor = open_dt
    step = timedelta(minutes=settings.slot_interval_minutes)
    while cursor + duration <= close_dt:
        slot_end = cursor + duration
        if cursor <= now:  # no ofrecer horas ya pasadas
            cursor += step
            continue
        conflict = any(_overlaps(cursor, slot_end, b.start_at, b.end_at) for b in booked)
        if not conflict:
            slots.append(cursor.strftime("%H:%M"))
        cursor += step
    return slots


def generate_slots(db: Session, service: models.Service, day: date) -> list[str]:
    """Horas 'HH:MM' disponibles para un servicio en un día dado."""
    return _free_slots(service, day, _booked_that_day(db, day), local_now())


def generate_calendar(
    db: Session, service: models.Service, year: int, month: int
) -> list[dict]:
    """Estado de cada día de un mes para un servicio.

    Precedencia de estados: ``past`` > ``closed`` > ``available`` > ``full``.
    Un día pasado se informa como pasado aunque además fuese día cerrado.
    """
    first_day = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    last_day = date(year, month, days_in_month)
    month_start = datetime.combine(first_day, time.min)
    month_end = datetime.combine(last_day + timedelta(days=1), time.min)

    booked = _booked_between(db, month_start, month_end)
    now = local_now()
    today = now.date()

    calendar_days: list[dict] = []
    for day_number in range(1, days_in_month + 1):
        day = date(year, month, day_number)
        if day < today:
            status, available_count = DAY_STATUS_PAST, 0
        elif day.weekday() in settings.closed_weekdays_set:
            status, available_count = DAY_STATUS_CLOSED, 0
        else:
            slots = _free_slots(service, day, booked, now)
            status = DAY_STATUS_AVAILABLE if slots else DAY_STATUS_FULL
            available_count = len(slots)
        calendar_days.append(
            {
                "date": day.isoformat(),
                "status": status,
                "available_count": available_count,
            }
        )
    return calendar_days


def is_slot_free(db: Session, service: models.Service, start_at: datetime) -> bool:
    """Valida que un inicio concreto esté dentro de horario y libre."""
    if start_at.weekday() in settings.closed_weekdays_set:
        return False

    end_at = start_at + timedelta(minutes=service.duration_min)
    open_dt = datetime.combine(start_at.date(), time(hour=settings.open_hour))
    close_dt = datetime.combine(start_at.date(), time(hour=settings.close_hour))
    if start_at < open_dt or end_at > close_dt:
        return False
    if start_at <= local_now():
        return False

    booked = _booked_that_day(db, start_at.date())
    return not any(_overlaps(start_at, end_at, b.start_at, b.end_at) for b in booked)
