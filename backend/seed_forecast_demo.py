"""Datos SINTÉTICOS para demostrar el gráfico de previsión (HU-03).

IMPORTANTE: este script NO carga historial real. Las citas que crea llevan
`notes = "[SINTÉTICO HU-03]"` y deben usarse sólo en entornos de demostración.
No las presentes como historial del negocio.

Uso:
    python seed_forecast_demo.py            # inserta 8 semanas de historial sintético
    python seed_forecast_demo.py --clear    # elimina sólo las filas sintéticas
"""
from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta

from app import models
from app.database import Base, SessionLocal, engine
from app.utils import local_now

MARKER = "[SINTÉTICO HU-03]"
# Demanda sintética por día de la semana (0=lunes … 6=domingo). Domingo es
# cerrado por configuración, así que no se generan citas ese día.
PATTERN = {0: 2, 1: 1, 2: 2, 3: 1, 4: 3, 5: 3, 6: 0}
STATUS_CYCLE = (
    models.STATUS_DONE,
    models.STATUS_DONE,
    models.STATUS_CONFIRMED,
    models.STATUS_PENDING,
)


def clear(db) -> int:
    rows = db.query(models.Appointment).filter(
        models.Appointment.notes == MARKER
    ).delete(synchronize_session=False)
    db.commit()
    return rows


def seed(db, weeks: int = 8) -> int:
    service = db.query(models.Service).filter_by(name="Corte").first()
    if not service:
        service = models.Service(name="Corte", duration_min=30, price=8000, active=True)
        db.add(service)
        db.commit()
        db.refresh(service)

    today = local_now().date()
    created = 0
    for offset in range(1, weeks * 7 + 1):
        day = today - timedelta(days=offset)
        demand = PATTERN[day.weekday()]
        for slot in range(demand):
            start = datetime.combine(day, time(hour=10 + slot))
            db.add(
                models.Appointment(
                    customer_name="Datos sintéticos",
                    customer_phone="+56900000000",
                    service_id=service.id,
                    start_at=start,
                    end_at=start + timedelta(minutes=30),
                    status=STATUS_CYCLE[(offset + slot) % len(STATUS_CYCLE)],
                    notes=MARKER,
                    created_at=start - timedelta(days=3),
                )
            )
            created += 1
        # Una cancelación ocasional para comprobar que NO cuenta como demanda.
        if day.weekday() == 4:
            start = datetime.combine(day, time(hour=17))
            db.add(
                models.Appointment(
                    customer_name="Datos sintéticos",
                    customer_phone="+56900000000",
                    service_id=service.id,
                    start_at=start,
                    end_at=start + timedelta(minutes=30),
                    status=models.STATUS_CANCELLED,
                    notes=MARKER,
                    created_at=start - timedelta(days=3),
                )
            )
            created += 1
    db.commit()
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera historial SINTÉTICO para HU-03.")
    parser.add_argument("--clear", action="store_true", help="Borra sólo las filas sintéticas.")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.clear:
            print(f"Filas sintéticas eliminadas: {clear(db)}")
        else:
            print("ADVERTENCIA: se insertarán citas SINTÉTICAS (no son historial real).")
            print(f"Filas creadas: {seed(db)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
