import re

from psycopg.errors import UniqueViolation

from database.seed_roles import DEFAULT_USER_ROLE
from repositories import role_repository as repo
from repositories import user_repository
from services.finance_validators import texto_opcional
from services.permission_service import exigir_permiso
from services.validators import AppError, parse_id, validar_nombre

ROLE_CODE_REGEX = re.compile(r"^[A-Z][A-Z0-9_]{1,49}$")
PERMISSION_CODE_REGEX = re.compile(r"^[a-z][a-z_]*(\.[a-z][a-z_]*)+$")
ADMIN_ROLE = "ADMINISTRADOR"


def obtener_rol_o_error(role_id):
    rol = repo.obtener_rol(parse_id(role_id, "ID de rol"))
    if rol is None:
        raise AppError(f"El rol con id {role_id} no existe")
    return rol


def listar_roles(active_only):
    return repo.obtener_roles(active_only)


def crear_rol(data, actor):
    code = (data.code or "").strip().upper()
    if not ROLE_CODE_REGEX.match(code):
        raise AppError("El código del rol debe usar mayúsculas, dígitos o guion bajo, por ejemplo AUDITOR")
    name = validar_nombre(data.name)
    exigir_permiso(actor, "roles.write")

    if repo.obtener_rol_por_codigo(code):
        raise AppError(f"Ya existe un rol con el código {code}")
    try:
        return repo.crear_rol(code, name, texto_opcional(data.description))
    except UniqueViolation:
        raise AppError(f"Ya existe un rol con el código {code}")


def desactivar_rol(role_id, actor):
    rol = obtener_rol_o_error(role_id)
    exigir_permiso(actor, "roles.write")
    if rol["code"] == ADMIN_ROLE:
        raise AppError("El rol ADMINISTRADOR no se puede desactivar")
    if not rol["is_active"]:
        raise AppError(f"El rol {rol['code']} ya está desactivado")
    return repo.desactivar_rol(rol["id"])


def obtener_permiso_o_error(permission_id):
    permiso = repo.obtener_permiso(parse_id(permission_id, "ID de permiso"))
    if permiso is None:
        raise AppError(f"El permiso con id {permission_id} no existe")
    return permiso


def listar_permisos(active_only):
    return repo.obtener_permisos(active_only)


RESOURCE_PREFIXES = {
    "COMPANY_USERS": "company.users.",
    "ACCOUNTS": "accounts.",
    "CONCEPTS": "concepts.",
    "TRANSACTIONS": "transactions.",
    "ROLES": "roles.",
}


def catalogo_permisos(resource, actor):
    exigir_permiso(actor, "roles.read")
    key = getattr(resource, "value", resource)
    prefix = RESOURCE_PREFIXES.get(key) if key is not None else None
    if key is not None and prefix is None:
        raise AppError("Recurso de permisos inválido")
    return repo.obtener_catalogo_permisos(prefix)


def _validar_propuesta(data):
    role_id = parse_id(data.role_id, "ID de rol")
    permission_ids = [parse_id(value, "ID de permiso") for value in data.permission_ids]
    if len(permission_ids) != len(set(permission_ids)):
        raise AppError("La lista contiene IDs de permiso repetidos")
    role, current, desired = repo.obtener_configuracion_rol(role_id, permission_ids)
    if role is None:
        raise AppError(f"El rol con id {role_id} no existe")
    if not role["is_active"]:
        raise AppError(f"El rol {role['code']} está desactivado")
    if role["code"] == ADMIN_ROLE:
        raise AppError("No se puede reemplazar la lista de permisos de ADMINISTRADOR")
    if len(desired) != len(permission_ids):
        found = {row["id"] for row in desired}
        missing = next(value for value in permission_ids if value not in found)
        raise AppError(f"El permiso con id {missing} no existe")
    inactive = next((row for row in desired if not row["is_active"]), None)
    if inactive:
        raise AppError(f"El permiso {inactive['code']} está desactivado")
    current_ids = {row["id"] for row in current}
    desired_ids = {row["id"] for row in desired}
    unchanged = [row for row in current if row["id"] in desired_ids]
    return {
        "role": role,
        "current": current,
        "desired": desired,
        "to_activate": [row for row in desired if row["id"] not in current_ids],
        "to_deactivate": [row for row in current if row["id"] not in desired_ids],
        "unchanged": unchanged,
        "final_count": len(desired),
    }


def previsualizar_permisos_rol(data, actor):
    exigir_permiso(actor, "roles.read")
    return _validar_propuesta(data)


def establecer_permisos_rol(data, actor):
    exigir_permiso(actor, "roles.write")
    plan = _validar_propuesta(data)
    if plan["to_activate"] or plan["to_deactivate"]:
        repo.aplicar_configuracion_rol(plan["role"]["id"], plan["desired"], plan["current"])
    return {
        "role": plan["role"],
        "activated": plan["to_activate"],
        "deactivated": plan["to_deactivate"],
        "unchanged": plan["unchanged"],
        "final_count": plan["final_count"],
        "changed": bool(plan["to_activate"] or plan["to_deactivate"]),
    }


def crear_permiso(data, actor):
    code = (data.code or "").strip().lower()
    if not PERMISSION_CODE_REGEX.match(code):
        raise AppError("El código del permiso se escribe recurso.accion, por ejemplo reports.read")
    name = validar_nombre(data.name)
    exigir_permiso(actor, "roles.write")

    if repo.obtener_permiso_por_codigo(code):
        raise AppError(f"Ya existe un permiso con el código {code}")
    try:
        return repo.crear_permiso(code, name, texto_opcional(data.description))
    except UniqueViolation:
        raise AppError(f"Ya existe un permiso con el código {code}")


def listar_permisos_de_rol(role_id):
    rol = obtener_rol_o_error(role_id)
    return repo.obtener_permisos_de_rol(rol["id"])


def asignar_permiso_a_rol(data, actor):
    rol = obtener_rol_o_error(data.role_id)
    permiso = obtener_permiso_o_error(data.permission_id)
    exigir_permiso(actor, "roles.write")
    if not rol["is_active"]:
        raise AppError(f"El rol {rol['code']} está desactivado")
    if not permiso["is_active"]:
        raise AppError(f"El permiso {permiso['code']} está desactivado")

    relacion = repo.obtener_relacion_rol_permiso(rol["id"], permiso["id"])
    if relacion and relacion["is_active"]:
        raise AppError(f"El rol {rol['code']} ya tiene el permiso {permiso['code']}")
    if relacion:
        return repo.cambiar_estado_relacion_rol_permiso(relacion["id"], True)
    try:
        return repo.crear_relacion_rol_permiso(rol["id"], permiso["id"])
    except UniqueViolation:
        raise AppError(f"El rol {rol['code']} ya tiene el permiso {permiso['code']}")


def quitar_permiso_de_rol(role_id, permission_id, actor):
    rol = obtener_rol_o_error(role_id)
    permiso = obtener_permiso_o_error(permission_id)
    exigir_permiso(actor, "roles.write")
    if rol["code"] == ADMIN_ROLE and permiso["code"] == "roles.write":
        raise AppError("No se puede quitar roles.write al rol ADMINISTRADOR: nadie podría volver a configurar el acceso")

    relacion = repo.obtener_relacion_rol_permiso(rol["id"], permiso["id"])
    if not relacion or not relacion["is_active"]:
        raise AppError(f"El rol {rol['code']} no tiene el permiso {permiso['code']}")
    repo.cambiar_estado_relacion_rol_permiso(relacion["id"], False)
    return True


def obtener_rol_por_codigo_o_error(code):
    rol = repo.obtener_rol_por_codigo(code)
    if rol is None or not rol["is_active"]:
        raise AppError(f"El rol {code} no existe o está desactivado")
    return rol


def asignar_rol(data, actor):
    membresia = user_repository.obtener_company_user(parse_id(data.company_user_id, "ID de membresía"))
    if membresia is None:
        raise AppError(f"La membresía con id {data.company_user_id} no existe")
    rol = obtener_rol_o_error(data.role_id)

    exigir_permiso(actor, "roles.write", membresia["company_id"])

    if not membresia["is_active"]:
        raise AppError("La membresía está inactiva")
    if not rol["is_active"]:
        raise AppError(f"El rol {rol['code']} está desactivado")
    if membresia["is_admin"] and rol["code"] != ADMIN_ROLE:
        raise AppError("El administrador principal conserva el rol ADMINISTRADOR")
    if not membresia["is_admin"] and rol["code"] == ADMIN_ROLE:
        raise AppError("El rol ADMINISTRADOR es solo del administrador principal de la empresa")

    actual = repo.obtener_rol_activo_de_membresia(membresia["id"])
    if actual and actual["role_id"] == rol["id"]:
        raise AppError(f"La membresía ya tiene el rol {rol['code']}")
    return repo.asignar_rol(membresia["id"], rol["id"])


def rol_inicial(role_id=None):
    if role_id is None:
        return obtener_rol_por_codigo_o_error(DEFAULT_USER_ROLE)
    rol = obtener_rol_o_error(role_id)
    if not rol["is_active"]:
        raise AppError(f"El rol {rol['code']} está desactivado")
    if rol["code"] == ADMIN_ROLE:
        raise AppError("El rol ADMINISTRADOR es del administrador principal, que nace con createCompanyAdmin")
    return rol
