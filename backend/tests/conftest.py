"""Configuración común de pytest: base de datos aislada y modo demo de WhatsApp."""
import os

# Debe fijarse ANTES de importar app.*: la URL se lee al importar database.py.
os.environ["DATABASE_URL"] = "sqlite:////tmp/citafacil_test.db"
os.environ["ADMIN_TOKEN"] = "test-token"
# Garantiza que ningún test envíe WhatsApp reales, aunque el entorno tenga Twilio.
os.environ["TWILIO_ACCOUNT_SID"] = ""
os.environ["TWILIO_AUTH_TOKEN"] = ""
os.environ["TWILIO_WHATSAPP_FROM"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(models.Service(name="Corte", duration_min=30, price=8000, active=True))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
