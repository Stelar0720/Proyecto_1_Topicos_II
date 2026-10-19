-- HU-01: preserva las citas existentes y añade vínculo opcional al perfil.
ALTER TABLE appointments ADD COLUMN customer_id VARCHAR(36);
CREATE INDEX IF NOT EXISTS ix_appointments_customer_id ON appointments (customer_id);
