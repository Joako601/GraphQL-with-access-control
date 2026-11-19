from psycopg.errors import UniqueViolation

from database.database import get_connection

# ==================================================
# TRANSACTIONS
# ==================================================

COLUMNS = """id, account_id, concept_id, transaction_type, amount, transaction_date, captured_at,
    captured_by, short_description, long_description, is_active, created_at, updated_at"""

IDEMPOTENCY_INDEX = "idempotency_keys_unique"


# IDEMPOTENCIA: la llave vive en idempotency_keys (database_idempotencia.sql)
def obtener_llave(company_id, operation, idempotency_key):
    with get_connection() as connection:
        sql = """
            SELECT id, company_id, operation, idempotency_key, request_hash, transaction_id, created_at
            FROM idempotency_keys
            WHERE company_id = %s AND operation = %s AND idempotency_key = %s;
        """
        return connection.execute(sql, (company_id, operation, idempotency_key)).fetchone()


# CREATE
def crear_movimiento(company_id, account_id, concept_id, transaction_type, amount,
                     transaction_date, captured_by, short_description, long_description,
                     idempotency=None):
    """Inserta el movimiento y, si viene `idempotency`, también su llave en la MISMA transacción.

    `idempotency` = (operation, idempotency_key, request_hash). Devuelve la fila del movimiento, o None si el
    índice único rechazó la llave porque otra petición con la misma llave hizo COMMIT primero; en ese caso el
    `with` hace ROLLBACK y el movimiento recién insertado no queda en la base.
    """
    try:
        # psycopg: el bloque `with` es una transacción; COMMIT al salir sin error, ROLLBACK si hay excepción.
        with get_connection() as connection:
            sql = f"""
                INSERT INTO transactions (company_id, account_id, concept_id, transaction_type, amount,
                                          transaction_date, captured_by, short_description, long_description)
                VALUES (%s, %s, %s, %s, %s, COALESCE(%s, NOW()), %s, %s, %s)
                RETURNING {COLUMNS};
            """
            params = (company_id, account_id, concept_id, transaction_type, amount,
                      transaction_date, captured_by, short_description, long_description)
            movimiento = connection.execute(sql, params).fetchone()
            if idempotency is not None:
                operation, idempotency_key, request_hash = idempotency
                connection.execute(
                    """
                    INSERT INTO idempotency_keys
                        (company_id, operation, idempotency_key, request_hash, transaction_id)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (company_id, operation, idempotency_key, request_hash, movimiento["id"]),
                )
            return movimiento
    except UniqueViolation as error:
        if error.diag.constraint_name == IDEMPOTENCY_INDEX:
            return None
        raise


# RETRIEVE - VARIOS 
def obtener_movimientos(company_id, account_id=None, transaction_type=None, limit=50, offset=0):
    condiciones = ["t.is_active = TRUE", "t.company_id = %s"]
    params = [company_id]
    if account_id is not None:
        condiciones.append("t.account_id = %s")
        params.append(account_id)
    if transaction_type:
        condiciones.append("t.transaction_type = %s")
        params.append(transaction_type)
    columnas = ", ".join("t." + c.strip() for c in COLUMNS.split(","))
    with get_connection() as connection:
        sql = f"""
            SELECT {columnas}
            FROM transactions t
            WHERE {' AND '.join(condiciones)}
            ORDER BY t.transaction_date, t.id
            LIMIT %s OFFSET %s;
        """
        return connection.execute(sql, (*params, limit, offset)).fetchall()


# RETRIEVE - UNO
def obtener_movimiento(transaction_id):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS}, company_id FROM transactions WHERE id = %s;"
        return connection.execute(sql, (transaction_id,)).fetchone()


# DELETE 
def eliminar_movimiento(transaction_id):
    with get_connection() as connection:
        sql = f"""
            UPDATE transactions
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = %s
            RETURNING {COLUMNS};
        """
        return connection.execute(sql, (transaction_id,)).fetchone()
