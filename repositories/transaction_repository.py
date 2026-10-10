from database.database import get_connection

# ==================================================
# TRANSACTIONS 
# ==================================================

COLUMNS = """id, account_id, concept_id, transaction_type, amount, transaction_date, captured_at,
    captured_by, short_description, long_description, is_active, created_at, updated_at"""


# CREATE
def crear_movimiento(company_id, account_id, concept_id, transaction_type, amount,
                     transaction_date, captured_by, short_description, long_description):
    with get_connection() as connection:
      
        sql = f"""
            INSERT INTO transactions (company_id, account_id, concept_id, transaction_type, amount,
                                      transaction_date, captured_by, short_description, long_description)
            VALUES (%s, %s, %s, %s, %s, COALESCE(%s, NOW()), %s, %s, %s)
            RETURNING {COLUMNS};
        """
        params = (company_id, account_id, concept_id, transaction_type, amount,
                  transaction_date, captured_by, short_description, long_description)
        return connection.execute(sql, params).fetchone()


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


# Balance = SUM(INCOME) - SUM(EXPENSE) de los movimientos activos
def obtener_saldo(account_id):
    with get_connection() as connection:
        sql = """
            SELECT
                COALESCE(SUM(amount) FILTER (WHERE transaction_type = 'INCOME'), 0.00) AS total_income,
                COALESCE(SUM(amount) FILTER (WHERE transaction_type = 'EXPENSE'), 0.00) AS total_expense,
                COUNT(*) AS transaction_count
            FROM transactions
            WHERE account_id = %s AND is_active = TRUE;
        """
        return connection.execute(sql, (account_id,)).fetchone()
