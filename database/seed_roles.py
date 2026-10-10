from pathlib import Path

from database.database import get_connection


DDL_PATH = Path(__file__).resolve().parent.parent / "database_roles.sql"

ROLES = [
    ("ADMINISTRADOR", "Administrador", "El administrador principal de la empresa"),
    ("CONTADOR", "Contador", "Quien arma cuentas y conceptos"),
    ("CAPTURISTA", "Capturista", "Quien registra movimientos"),
    ("CONSULTA", "Consulta", "Quien solo lee"),
]

PERMISSIONS = [
    ("company.users.read", "Ver usuarios", "Ver las membresías de la empresa"),
    ("company.users.write", "Administrar usuarios", "Crear usuarios y desactivar membresías"),
    ("accounts.read", "Ver cuentas", "Consultar cuentas"),
    ("accounts.write", "Crear cuentas", "Crear cuentas"),
    ("concepts.read", "Ver conceptos", "Consultar conceptos"),
    ("concepts.write", "Administrar conceptos", "Crear conceptos y asignarlos a una cuenta"),
    ("transactions.read", "Ver movimientos", "Consultar movimientos"),
    ("transactions.write", "Registrar movimientos", "Registrar un ingreso o un egreso"),
    ("roles.read", "Ver roles", "Ver roles y la matriz de permisos"),
    ("roles.write", "Administrar roles",
     "Asignar o quitar permisos de un rol, y asignar un rol a una membresía"),
]

ROLE_PERMISSIONS = {
    "ADMINISTRADOR": [code for code, _, _ in PERMISSIONS],
    "CONTADOR": [
        "company.users.read",
        "accounts.read", "accounts.write",
        "concepts.read", "concepts.write",
        "transactions.read", "transactions.write",
        "roles.read",
    ],
    "CAPTURISTA": [
        "accounts.read",
        "concepts.read",
        "transactions.read", "transactions.write",
    ],
    "CONSULTA": [
        "company.users.read",
        "accounts.read",
        "concepts.read",
        "transactions.read",
    ],
}

DEFAULT_USER_ROLE = "CONSULTA"


def _contar(connection, tabla):
    return connection.execute(f"SELECT COUNT(*) AS total FROM {tabla};").fetchone()["total"]


def inicializar_roles_y_permisos():
    with get_connection() as connection:
        connection.execute(DDL_PATH.read_text(encoding="utf-8"))

        if _contar(connection, "roles") == 0:
            for code, name, description in ROLES:
                connection.execute(
                    "INSERT INTO roles (code, name, description) VALUES (%s, %s, %s);",
                    (code, name, description),
                )

        if _contar(connection, "permissions") == 0:
            for code, name, description in PERMISSIONS:
                connection.execute(
                    "INSERT INTO permissions (code, name, description) VALUES (%s, %s, %s);",
                    (code, name, description),
                )

        for role_code, permission_codes in ROLE_PERMISSIONS.items():
            role = connection.execute("SELECT id FROM roles WHERE code = %s;", (role_code,)).fetchone()
            if role is None:
                continue
            tiene = connection.execute(
                "SELECT 1 FROM role_permissions WHERE role_id = %s LIMIT 1;", (role["id"],)
            ).fetchone()
            if tiene:
                continue
            connection.execute(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT %s, id FROM permissions WHERE code = ANY(%s);
                """,
                (role["id"], permission_codes),
            )

        connection.execute(
            """
            INSERT INTO company_user_roles (company_user_id, role_id)
            SELECT cu.id, r.id
            FROM company_users cu
            JOIN roles r ON r.code = CASE WHEN cu.is_admin THEN 'ADMINISTRADOR' ELSE %s END
            WHERE NOT EXISTS (
                SELECT 1 FROM company_user_roles cur
                WHERE cur.company_user_id = cu.id AND cur.is_active
            );
            """,
            (DEFAULT_USER_ROLE,),
        )
