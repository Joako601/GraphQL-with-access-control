from database.database import get_connection

# ==================================================
# ACCOUNT_CONCEPTS 
# ==================================================

COLUMNS = "id, account_id, concept_id, is_active, created_at"


def obtener_relacion(account_id, concept_id):
   
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM account_concepts WHERE account_id = %s AND concept_id = %s;"
        return connection.execute(sql, (account_id, concept_id)).fetchone()


def crear_relacion(company_id, account_id, concept_id):
    with get_connection() as connection:
        sql = f"""
            INSERT INTO account_concepts (company_id, account_id, concept_id)
            VALUES (%s, %s, %s)
            RETURNING {COLUMNS};
        """
        return connection.execute(sql, (company_id, account_id, concept_id)).fetchone()


def reactivar_relacion(relation_id):
    with get_connection() as connection:
        sql = f"""
            UPDATE account_concepts
            SET is_active = TRUE
            WHERE id = %s
            RETURNING {COLUMNS};
        """
        return connection.execute(sql, (relation_id,)).fetchone()


def desactivar_relacion(relation_id):
    with get_connection() as connection:
        sql = f"""
            UPDATE account_concepts
            SET is_active = FALSE
            WHERE id = %s
            RETURNING {COLUMNS};
        """
        return connection.execute(sql, (relation_id,)).fetchone()


def obtener_relaciones_de_cuenta(account_id, active_only=True):
    with get_connection() as connection:
        sql = f"SELECT {COLUMNS} FROM account_concepts WHERE account_id = %s"
        if active_only:
            sql += " AND is_active = TRUE"
        return connection.execute(sql + " ORDER BY id;", (account_id,)).fetchall()
