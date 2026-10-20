"""Operaciones de base de datos (Create/Read/Update/Delete)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from . import models, schemas


# ---------- Servicios ----------
def list_services(db: Session, only_active: bool = True) -> list[models.Service]:
    q = db.query(models.Service)
    if only_active:
        q = q.filter(models.Service.active.is_(True))
    return q.order_by(models.Service.id).all()


def get_service(db: Session, service_id: int) -> Optional[models.Service]:
    return db.query(models.Service).filter(models.Service.id == service_id).first()


def create_service(db: Session, data: schemas.ServiceCreate) -> models.Service:
    obj = models.Service(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_service(db: Session, service: models.Service, data: schemas.ServiceUpdate) -> models.Service:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(service, key, value)
    db.commit()
    db.refresh(service)
    return service


def delete_service(db: Session, service: models.Service) -> None:
    db.delete(service)
    db.commit()


# ---------- Citas ----------
def create_appointment(
    db: Session,
    data: schemas.AppointmentCreate,
    service: models.Service,
    end_at: datetime,
    cancel_token_hash: Optional[str] = None,
) -> models.Appointment:
    obj = models.Appointment(
        customer_name=data.customer_name.strip(),
        customer_phone=data.customer_phone,
        service_id=service.id,
        start_at=data.start_at,
        end_at=end_at,
        notes=(data.notes or "").strip(),
        status=models.STATUS_PENDING,
        cancel_token_hash=cancel_token_hash,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_appointments(
    db: Session, status: Optional[str] = None, day: Optional[date] = None
) -> list[models.Appointment]:
    q = db.query(models.Appointment)
    if status:
        q = q.filter(models.Appointment.status == status)
    if day:
        q = q.filter(
            models.Appointment.start_at >= datetime.combine(day, time.min),
            models.Appointment.start_at <= datetime.combine(day, time.max),
        )
    return q.order_by(models.Appointment.start_at).all()


def get_appointment(db: Session, appt_id: int) -> Optional[models.Appointment]:
    return db.query(models.Appointment).filter(models.Appointment.id == appt_id).first()


def set_status(db: Session, appt: models.Appointment, status: str) -> models.Appointment:
    appt.status = status
    db.commit()
    db.refresh(appt)
    return appt


def delete_appointment(db: Session, appt: models.Appointment) -> None:
    db.delete(appt)
    db.commit()


# ---------- Clientes identificados ----------
def get_customer_by_phone(db: Session, phone: str) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.phone == phone).first()


def get_customer(db: Session, customer_id: str) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()


def get_or_create_customer(db: Session, phone: str) -> models.Customer:
    customer = get_customer_by_phone(db, phone)
    if customer:
        return customer
    customer = models.Customer(id=str(uuid.uuid4()), phone=phone)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, customer: models.Customer, display_name: str) -> models.Customer:
    customer.display_name = display_name.strip()
    db.commit()
    db.refresh(customer)
    return customer


def create_customer_appointment(
    db: Session,
    customer: models.Customer,
    data: schemas.CustomerAppointmentCreate,
    service: models.Service,
    end_at: datetime,
    cancel_token_hash: Optional[str] = None,
) -> models.Appointment:
    obj = models.Appointment(customer_id=customer.id, customer_name=customer.display_name, customer_phone=customer.phone,
                             service_id=service.id, start_at=data.start_at, end_at=end_at,
                             notes=(data.notes or "").strip(), status=models.STATUS_PENDING,
                             cancel_token_hash=cancel_token_hash)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_customer_upcoming_appointments(db: Session, customer_id: str) -> list[models.Appointment]:
    from .utils import local_now
    return (db.query(models.Appointment)
            .filter(models.Appointment.customer_id == customer_id,
                    models.Appointment.start_at >= local_now(),
                    models.Appointment.status.in_([models.STATUS_PENDING, models.STATUS_CONFIRMED]))
            .order_by(models.Appointment.start_at).all())


def stats(db: Session) -> dict:
    from .utils import local_now

    def count(status: str) -> int:
        return db.query(models.Appointment).filter(models.Appointment.status == status).count()

    upcoming = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.start_at >= local_now(),
            models.Appointment.status.in_([models.STATUS_PENDING, models.STATUS_CONFIRMED]),
        )
        .count()
    )
    return {
        "total": db.query(models.Appointment).count(),
        "pending": count(models.STATUS_PENDING),
        "confirmed": count(models.STATUS_CONFIRMED),
        "cancelled": count(models.STATUS_CANCELLED),
        "done": count(models.STATUS_DONE),
        "upcoming": upcoming,
    }
