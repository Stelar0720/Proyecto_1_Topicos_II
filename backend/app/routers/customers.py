"""Endpoints de perfil y reserva autenticada de clientes."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..availability import is_slot_free
from ..cancellation import (
    appointment_with_cancel_url,
    hash_cancel_token,
    new_cancel_token,
)
from ..customer_auth import create_access_token, issue_challenge, require_customer, verify_challenge
from ..database import get_db
from ..notifications import send_whatsapp
from ..config import settings

router = APIRouter(prefix="/api", tags=["Clientes"])


@router.post("/customer-access/challenges", status_code=status.HTTP_202_ACCEPTED)
def request_challenge(payload: schemas.CustomerChallengeRequest, db: Session = Depends(get_db)):
    code = issue_challenge(db, payload.customer_phone)
    send_whatsapp(payload.customer_phone, f"Tu código de acceso a {settings.business_name} es: {code}. Vence pronto.")
    return {"detail": "Si el número puede recibir mensajes, enviamos un código de acceso."}


@router.post("/customer-access/tokens", response_model=schemas.CustomerTokenOut)
def verify_access(payload: schemas.CustomerChallengeVerify, db: Session = Depends(get_db)):
    customer = verify_challenge(db, payload.customer_phone, payload.code)
    return {"access_token": create_access_token(customer.id), "expires_in": settings.customer_access_token_minutes * 60}


@router.get("/me", response_model=schemas.CustomerProfileOut)
def get_me(customer: models.Customer = Depends(require_customer)):
    return customer


@router.put("/me", response_model=schemas.CustomerProfileOut)
def update_me(payload: schemas.CustomerProfileUpdate, customer: models.Customer = Depends(require_customer), db: Session = Depends(get_db)):
    return crud.update_customer(db, customer, payload.display_name)


@router.get("/me/appointments", response_model=list[schemas.AppointmentOut])
def my_upcoming_appointments(customer: models.Customer = Depends(require_customer), db: Session = Depends(get_db)):
    """Sólo devuelve próximas citas activas pertenecientes al cliente autenticado."""
    return crud.list_customer_upcoming_appointments(db, customer.id)


@router.post("/me/appointments", response_model=schemas.AppointmentOut, status_code=201)
def create_my_appointment(payload: schemas.CustomerAppointmentCreate, customer: models.Customer = Depends(require_customer), db: Session = Depends(get_db)):
    if len(customer.display_name.strip()) < 2:
        raise HTTPException(status_code=422, detail="Actualiza tu nombre antes de reservar.")
    service = crud.get_service(db, payload.service_id)
    if not service or not service.active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    if not is_slot_free(db, service, payload.start_at):
        raise HTTPException(status_code=409, detail="Ese horario ya no está disponible. Por favor elige otro.")
    token = new_cancel_token()
    appt = crud.create_customer_appointment(
        db,
        customer,
        payload,
        service,
        payload.start_at + timedelta(minutes=service.duration_min),
        cancel_token_hash=hash_cancel_token(token),
    )
    return appointment_with_cancel_url(appt, token)
