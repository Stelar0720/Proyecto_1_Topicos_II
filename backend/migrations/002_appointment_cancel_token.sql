-- HU-04: token privado de cancelación. Sólo se guarda el hash SHA-256.
ALTER TABLE appointments ADD COLUMN cancel_token_hash VARCHAR(64);
