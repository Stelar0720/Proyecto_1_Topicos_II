"""Migraciones pequeñas e idempotentes para instalaciones existentes.

El proyecto no usaba Alembic. Esta migración preserva las citas existentes y
permite desplegar HU-01 sin recrear la base de datos.
"""
from sqlalchemy import inspect, text


def apply_schema_migrations(engine) -> None:
    inspector = inspect(engine)
    if "appointments" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("appointments")}
    if "customer_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE appointments ADD COLUMN customer_id VARCHAR(36)"))
