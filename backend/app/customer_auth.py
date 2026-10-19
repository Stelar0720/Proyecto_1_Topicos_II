"""Verificación por código de un solo uso y tokens breves para clientes."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import timedelta

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, models
from .config import settings
from .database import get_db
from .utils import local_now


def _hash_code(code: str) -> str:
    return hmac.new(settings.customer_auth_secret.encode(), code.encode(), hashlib.sha256).hexdigest()


def issue_challenge(db: Session, phone: str) -> str:
    """Crea un reto y devuelve el código sólo para que el emisor de WhatsApp lo use."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    row = models.CustomerAccessChallenge(
        id=str(uuid.uuid4()), phone=phone, code_hash=_hash_code(code),
        expires_at=local_now() + timedelta(minutes=settings.customer_access_code_minutes),
    )
    db.add(row)
    db.commit()
    return code


def verify_challenge(db: Session, phone: str, code: str) -> models.Customer:
    row = (db.query(models.CustomerAccessChallenge)
           .filter(models.CustomerAccessChallenge.phone == phone,
                   models.CustomerAccessChallenge.consumed_at.is_(None))
           .order_by(models.CustomerAccessChallenge.created_at.desc()).first())
    if not row or row.expires_at < local_now() or row.attempts >= 5:
        raise HTTPException(status_code=401, detail="Código inválido o vencido.")
    row.attempts += 1
    if not hmac.compare_digest(row.code_hash, _hash_code(code)):
        db.commit()
        raise HTTPException(status_code=401, detail="Código inválido o vencido.")
    row.consumed_at = local_now()
    db.commit()
    return crud.get_or_create_customer(db, phone)


def create_access_token(customer_id: str) -> str:
    expires = int((local_now() + timedelta(minutes=settings.customer_access_token_minutes)).timestamp())
    payload = f"{customer_id}.{expires}"
    signature = hmac.new(settings.customer_auth_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def require_customer(authorization: str = Header(...), db: Session = Depends(get_db)) -> models.Customer:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de cliente inválido.")
    try:
        customer_id, expiry, signature = authorization[7:].split(".")
        payload = f"{customer_id}.{expiry}"
        expected = hmac.new(settings.customer_auth_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected) or int(expiry) < int(local_now().timestamp()):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de cliente inválido.")
    customer = crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de cliente inválido.")
    return customer
