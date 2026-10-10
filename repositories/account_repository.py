from database.database import get_connection

# ==================================================
# ACCOUNTS
# ==================================================

COLUMNS = """id, company_id, account_type, name, bank_name, account_number, clabe,
    card_last_digits, short_description, long_description, is_active, created_at, updated_at"""


# CREATE
def crear_cuenta(company_id, account_type, name, bank_name, account_number, clabe,
                 card_last_digits, short_description, long_description):
    with get_connection() as connection:
        sql = f"""
            INSERT INTO accounts (company_id, account_type, name, bank_name, account_number, clabe,
                                  card_last_digits, short_description, long_description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {COLUMNS};
        """
        params = (company_id, account_type, name, bank_name, account_number, clabe,
                  card_last_digits, short_description, long_description)
        return connection.execute(sql, params).fetchone()


# RETRIEVE - TODAS 
def obtener_cuentas(company_id, account_type=None, active_only=None):
    condiciones = ["company_id = %s"]
    params = [company_id]
    if account_type:
        condiciones.append("account_type = %s")
        params.append(account_type)
    if active_only:
        condiciones.append("is_active = TRUE")
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM accounts WHERE {' AND '.join(condiciones)} ORDER BY id;"
        return connection.execute(sql, params).fetchall()


# RETRIEVE - UNA
def obtener_cuenta(account_id):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM accounts WHERE id = %s;"
        return connection.execute(sql, (account_id,)).fetchone()


def obtener_cuenta_por_nombre(company_id, name):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM accounts WHERE company_id = %s AND LOWER(name) = LOWER(%s);"
        return connection.execute(sql, (company_id, name)).fetchone()


def obtener_cuenta_por_clabe(clabe):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM accounts WHERE clabe = %s;"
        return connection.execute(sql, (clabe,)).fetchone()
