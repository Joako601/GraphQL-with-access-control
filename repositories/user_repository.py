from database.database import get_connection

# ==================================================
# USERS Y COMPANY_USERS
# ==================================================

USER_COLUMNS = "id, name, email, email_verified, is_active, created_at, updated_at"
CU_COLUMNS = "id, company_id, user_id, is_admin, is_active, joined_at"


def obtener_usuario(user_id):
    with get_connection() as connection:
        sql = f"SELECT {USER_COLUMNS} FROM users WHERE id = %s;"
        return connection.execute(sql, (user_id,)).fetchone()


def obtener_usuario_por_email(email):
   
    with get_connection() as connection:
        sql = f"SELECT {USER_COLUMNS}, password_hash FROM users WHERE email = %s;"
        return connection.execute(sql, (email,)).fetchone()


def existe_admin(company_id):
    with get_connection() as connection:
        sql = "SELECT 1 FROM company_users WHERE company_id = %s AND is_admin = TRUE;"
        return connection.execute(sql, (company_id,)).fetchone() is not None


def crear_usuario_en_empresa(company_id, name, email, password_hash, is_admin, role_id):
    with get_connection() as connection:
        user = connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id;",
            (name, email, password_hash),
        ).fetchone()
        sql = f"""
            INSERT INTO company_users (company_id, user_id, is_admin)
            VALUES (%s, %s, %s)
            RETURNING {CU_COLUMNS};
        """
        company_user = connection.execute(sql, (company_id, user["id"], is_admin)).fetchone()
        connection.execute(
            "INSERT INTO company_user_roles (company_user_id, role_id) VALUES (%s, %s);",
            (company_user["id"], role_id),
        )
        return company_user


def obtener_membresia(company_id, user_id):
    with get_connection() as connection:
        sql = f"SELECT {CU_COLUMNS} FROM company_users WHERE company_id = %s AND user_id = %s;"
        return connection.execute(sql, (company_id, user_id)).fetchone()


def obtener_company_user(company_user_id):
    with get_connection() as connection:
        sql = f"SELECT {CU_COLUMNS} FROM company_users WHERE id = %s;"
        return connection.execute(sql, (company_user_id,)).fetchone()


def obtener_usuarios_de_empresa(company_id):
    with get_connection() as connection:
        sql = f"SELECT {CU_COLUMNS} FROM company_users WHERE company_id = %s ORDER BY id;"
        return connection.execute(sql, (company_id,)).fetchall()


def desactivar_company_user(company_user_id):
    with get_connection() as connection:
        sql = f"""
            UPDATE company_users
            SET is_active = FALSE
            WHERE id = %s
            RETURNING {CU_COLUMNS};
        """
        return connection.execute(sql, (company_user_id,)).fetchone()
