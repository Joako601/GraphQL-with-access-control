from database.database import get_connection

# ==================================================
# COMPANIES
# ==================================================

COLUMNS = "id, name, legal_name, tax_id, email, phone, is_active, created_at, updated_at"


# CREATE
def crear_empresa(name, legal_name, tax_id, email, phone):
    with get_connection() as connection:
        sql = f"""
            INSERT INTO companies (name, legal_name, tax_id, email, phone)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING {COLUMNS};
        """
        return connection.execute(sql, (name, legal_name, tax_id, email, phone)).fetchone()


# RETRIEVE - TODAS
def obtener_empresas(active_only):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM companies"
        if active_only:
            sql += " WHERE is_active = TRUE"
        return connection.execute(sql + " ORDER BY id;").fetchall()


# RETRIEVE - UNA
def obtener_empresa(company_id):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM companies WHERE id = %s;"
        return connection.execute(sql, (company_id,)).fetchone()


def obtener_empresa_por_rfc(tax_id):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM companies WHERE tax_id = %s;"
        return connection.execute(sql, (tax_id,)).fetchone()


# UPDATE
def actualizar_empresa(company_id, campos):
   
    asignaciones = ", ".join(f"{columna} = %s" for columna in campos)
    with get_connection() as connection:
        sql = f"""
            UPDATE companies
            SET {asignaciones}, updated_at = NOW()
            WHERE id = %s
            RETURNING {COLUMNS};
        """
        return connection.execute(sql, (*campos.values(), company_id)).fetchone()


# DELETE 
def desactivar_empresa(company_id):
    with get_connection() as connection:
        sql = f"""
            UPDATE companies
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = %s
            RETURNING {COLUMNS};
        """
        return connection.execute(sql, (company_id,)).fetchone()
