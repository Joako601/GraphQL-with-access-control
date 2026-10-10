from database.database import get_connection

ROLE_COLUMNS = "id, code, name, description, is_active"
PERMISSION_COLUMNS = "id, code, name, description, is_active"
RP_COLUMNS = "id, role_id, permission_id, is_active"
CUR_COLUMNS = "id, company_user_id, role_id, is_active"


def crear_rol(code, name, description):
    with get_connection() as connection:
        sql = f"""
            INSERT INTO roles (code, name, description)
            VALUES (%s, %s, %s)
            RETURNING {ROLE_COLUMNS};
        """
        return connection.execute(sql, (code, name, description)).fetchone()


def obtener_roles(active_only=None):
    with get_connection() as connection:
        sql = f"SELECT {ROLE_COLUMNS} FROM roles"
        if active_only:
            sql += " WHERE is_active = TRUE"
        return connection.execute(sql + " ORDER BY id;").fetchall()


def obtener_rol(role_id):
    with get_connection() as connection:
        sql = f"SELECT {ROLE_COLUMNS} FROM roles WHERE id = %s;"
        return connection.execute(sql, (role_id,)).fetchone()


def obtener_rol_por_codigo(code):
    with get_connection() as connection:
        sql = f"SELECT {ROLE_COLUMNS} FROM roles WHERE code = %s;"
        return connection.execute(sql, (code,)).fetchone()


def desactivar_rol(role_id):
    with get_connection() as connection:
        sql = f"""
            UPDATE roles
            SET is_active = FALSE
            WHERE id = %s
            RETURNING {ROLE_COLUMNS};
        """
        return connection.execute(sql, (role_id,)).fetchone()


def crear_permiso(code, name, description):
    with get_connection() as connection:
        sql = f"""
            INSERT INTO permissions (code, name, description)
            VALUES (%s, %s, %s)
            RETURNING {PERMISSION_COLUMNS};
        """
        return connection.execute(sql, (code, name, description)).fetchone()


def obtener_permisos(active_only=None):
    with get_connection() as connection:
        sql = f"SELECT {PERMISSION_COLUMNS} FROM permissions"
        if active_only:
            sql += " WHERE is_active = TRUE"
        return connection.execute(sql + " ORDER BY id;").fetchall()


def obtener_permiso(permission_id):
    with get_connection() as connection:
        sql = f"SELECT {PERMISSION_COLUMNS} FROM permissions WHERE id = %s;"
        return connection.execute(sql, (permission_id,)).fetchone()


def obtener_permiso_por_codigo(code):
    with get_connection() as connection:
        sql = f"SELECT {PERMISSION_COLUMNS} FROM permissions WHERE code = %s;"
        return connection.execute(sql, (code,)).fetchone()


def obtener_relacion_rol_permiso(role_id, permission_id):
    with get_connection() as connection:
        sql = f"SELECT {RP_COLUMNS} FROM role_permissions WHERE role_id = %s AND permission_id = %s;"
        return connection.execute(sql, (role_id, permission_id)).fetchone()


def crear_relacion_rol_permiso(role_id, permission_id):
    with get_connection() as connection:
        sql = f"""
            INSERT INTO role_permissions (role_id, permission_id)
            VALUES (%s, %s)
            RETURNING {RP_COLUMNS};
        """
        return connection.execute(sql, (role_id, permission_id)).fetchone()


def cambiar_estado_relacion_rol_permiso(relation_id, is_active):
    with get_connection() as connection:
        sql = f"""
            UPDATE role_permissions
            SET is_active = %s
            WHERE id = %s
            RETURNING {RP_COLUMNS};
        """
        return connection.execute(sql, (is_active, relation_id)).fetchone()


def obtener_permisos_de_rol(role_id):
    columnas = ", ".join("rp." + c.strip() for c in RP_COLUMNS.split(","))
    with get_connection() as connection:
        sql = f"""
            SELECT {columnas}
            FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id
            WHERE rp.role_id = %s AND rp.is_active = TRUE AND p.is_active = TRUE
            ORDER BY p.id;
        """
        return connection.execute(sql, (role_id,)).fetchall()


def rol_tiene_permiso(role_id, code):
    with get_connection() as connection:
        sql = """
            SELECT 1
            FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id
            WHERE rp.role_id = %s
              AND rp.is_active = TRUE
              AND p.code = %s
              AND p.is_active = TRUE;
        """
        return connection.execute(sql, (role_id, code)).fetchone() is not None


def obtener_rol_activo_de_membresia(company_user_id):
    with get_connection() as connection:
        sql = f"""
            SELECT {CUR_COLUMNS}
            FROM company_user_roles
            WHERE company_user_id = %s AND is_active = TRUE;
        """
        return connection.execute(sql, (company_user_id,)).fetchone()


def asignar_rol(company_user_id, role_id):
    with get_connection() as connection:
        connection.execute(
            "UPDATE company_user_roles SET is_active = FALSE WHERE company_user_id = %s AND is_active = TRUE;",
            (company_user_id,),
        )
        sql = f"""
            INSERT INTO company_user_roles (company_user_id, role_id)
            VALUES (%s, %s)
            RETURNING {CUR_COLUMNS};
        """
        return connection.execute(sql, (company_user_id, role_id)).fetchone()
