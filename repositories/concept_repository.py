from database.database import get_connection

# ==================================================
# CONCEPTS
# ==================================================

COLUMNS = """id, company_id, concept_type, name, short_description, long_description,
    is_active, created_at, updated_at"""


# CREATE
def crear_concepto(company_id, concept_type, name, short_description, long_description):
    with get_connection() as connection:
        sql = f"""
            INSERT INTO concepts (company_id, concept_type, name, short_description, long_description)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING {COLUMNS};
        """
        params = (company_id, concept_type, name, short_description, long_description)
        return connection.execute(sql, params).fetchone()


# RETRIEVE - TODOS 
def obtener_conceptos(company_id, concept_type=None, active_only=None):
    condiciones = ["company_id = %s"]
    params = [company_id]
    if concept_type:
        condiciones.append("concept_type = %s")
        params.append(concept_type)
    if active_only:
        condiciones.append("is_active = TRUE")
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM concepts WHERE {' AND '.join(condiciones)} ORDER BY id;"
        return connection.execute(sql, params).fetchall()


# RETRIEVE - UNO
def obtener_concepto(concept_id):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM concepts WHERE id = %s;"
        return connection.execute(sql, (concept_id,)).fetchone()


def obtener_concepto_por_nombre(company_id, name):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM concepts WHERE company_id = %s AND LOWER(name) = LOWER(%s);"
        return connection.execute(sql, (company_id, name)).fetchone()
