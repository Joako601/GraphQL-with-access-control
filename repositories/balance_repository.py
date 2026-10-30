from database.database import get_connection

# ==================================================
# BALANCES (solo lectura: se calculan, no se guardan)
# ==================================================


def obtener_balances(company_id, inicio, fin, account_id=None):
    """Una fila por cuenta de la empresa con su saldo previo y los totales del período [inicio, fin)."""
    with get_connection() as connection:
        # Se parte de accounts y los filtros del movimiento van en el ON, no en el WHERE:
        # así una cuenta sin movimientos sigue apareciendo con ceros. No se une a account_concepts
        # porque transaction_type ya decide el signo y esa unión podría duplicar importes.
        sql = """
            SELECT
                a.id AS account_id,
                a.name AS account_name,
                a.is_active,
                COALESCE(SUM(CASE t.transaction_type WHEN 'INCOME' THEN t.amount ELSE -t.amount END)
                         FILTER (WHERE t.transaction_date < %(inicio)s), 0) AS opening_balance,
                COALESCE(SUM(t.amount)
                         FILTER (WHERE t.transaction_date >= %(inicio)s AND t.transaction_type = 'INCOME'), 0)
                    AS total_income,
                COALESCE(SUM(t.amount)
                         FILTER (WHERE t.transaction_date >= %(inicio)s AND t.transaction_type = 'EXPENSE'), 0)
                    AS total_expense
            FROM accounts a
            LEFT JOIN transactions t
                ON t.account_id = a.id
               AND t.is_active
               AND t.transaction_date < %(fin)s
            WHERE a.company_id = %(company_id)s
              AND (%(account_id)s::int IS NULL OR a.id = %(account_id)s::int)
            GROUP BY a.id
            ORDER BY a.id;
        """
        params = {"company_id": company_id, "inicio": inicio, "fin": fin, "account_id": account_id}
        return connection.execute(sql, params).fetchall()
