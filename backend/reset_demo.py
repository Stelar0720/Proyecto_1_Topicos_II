"""Recrea exclusivamente la base SQLite local usada en la demostración."""
from __future__ import annotations

from app.database import Base, DATABASE_URL, engine
from app.routers.scores import Score  # noqa: F401 - registra game_scores en metadata
from seed import run as seed_base
from seed_forecast_demo import seed as seed_forecast
from app.database import SessionLocal


def main() -> None:
    if not DATABASE_URL.startswith("sqlite:///") or not DATABASE_URL.endswith("citafacil-demo.db"):
        raise SystemExit(
            "Por seguridad, reset_demo.py sólo opera sobre sqlite:///./citafacil-demo.db."
        )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_base()
    db = SessionLocal()
    try:
        created = seed_forecast(db)
    finally:
        db.close()
    print(f"Demo lista. Histórico sintético creado: {created} filas.")


if __name__ == "__main__":
    main()
