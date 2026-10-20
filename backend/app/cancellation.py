"""Tokens privados de cancelación y reglas de cancelación de citas.

El token se genera con ``secrets`` (32 bytes), se envía una sola vez en el
enlace y en la base de datos sólo queda su SHA-256. El ID de la cita por sí
solo no permite cancelar: siempre se exige el token correcto.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from . import models, schemas
from .config import settings
from .utils import local_now

CANCEL_TOKEN_BYTES = 32


def new_cancel_token() -> str:
    """Token aleatorio e impredecible, apto para URL."""
    return secrets.token_urlsafe(CANCEL_TOKEN_BYTES)


def hash_cancel_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_matches(appointment: models.Appointment, token: str) -> bool:
    """Comparación en tiempo constante contra el hash almacenado."""
    if not appointment.cancel_token_hash or not token:
        return False
    return hmac.compare_digest(
        appointment.cancel_token_hash, hash_cancel_token(token)
    )


def cancel_url(appointment_id: int, token: str) -> str:
    """Enlace al frontend de confirmación (nunca cancela por sí solo)."""
    path = "cancel.html?" + urlencode({"id": appointment_id, "token": token})
    base = settings.frontend_url.strip().rstrip("/")
    return f"{base}/{path}" if base else path


def cancellation_error(
    appointment: models.Appointment, now: Optional[datetime] = None
) -> Optional[str]:
    """Motivo por el que la cita no puede cancelarse, o ``None`` si puede.

    Reglas documentadas en docs/PR_HU_04.md:
    - Ya cancelada: no se vuelve a modificar.
    - Realizada (``done``): no se cancela.
    - Cita pasada (inicio <= ahora): no se cancela, aunque siga pendiente.
    """
    if appointment.status == models.STATUS_CANCELLED:
        return "Esta cita ya fue cancelada."
    if appointment.status == models.STATUS_DONE:
        return "Esta cita ya fue realizada y no puede cancelarse."
    if appointment.start_at <= (now or local_now()):
        return "No se puede cancelar una cita que ya pasó."
    return None


def appointment_with_cancel_url(
    appointment: models.Appointment, token: str
) -> schemas.AppointmentOut:
    """Salida de creación: incluye el enlace privado una única vez."""
    out = schemas.AppointmentOut.model_validate(appointment)
    out.cancel_url = cancel_url(appointment.id, token)
    return out
