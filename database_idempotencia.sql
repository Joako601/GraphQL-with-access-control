-- Unidad III, Actividad 2: llaves de idempotencia de createTransaction.
-- La llave y el movimiento se insertan en la misma transacción (un solo COMMIT): si el COMMIT falla no queda
-- ni el movimiento ni la llave; si pasa y se pierde la respuesta, el reintento encuentra la llave.
-- El script es idempotente (IF NOT EXISTS): lo ejecuta docker en un volumen nuevo y la API al arrancar.

CREATE TABLE IF NOT EXISTS idempotency_keys (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(id),
    operation VARCHAR(50) NOT NULL,
    idempotency_key VARCHAR(100) NOT NULL,
    -- SHA-256 del cuerpo normalizado: la misma llave con otro monto u otra cuenta se rechaza.
    request_hash CHAR(64) NOT NULL,
    transaction_id INT NOT NULL REFERENCES transactions(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice único de empresa, operación y llave: el reintento choca aquí y no inserta otro movimiento.
CREATE UNIQUE INDEX IF NOT EXISTS idempotency_keys_unique
    ON idempotency_keys (company_id, operation, idempotency_key);
