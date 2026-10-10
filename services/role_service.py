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


def _membresia_del_actor(actor_company_user_id):
    membresia = user_repository.obtener_company_user(parse_id(actor_company_user_id, "actorCompanyUserId"))
    if membresia is None:
        raise AppError(f"La membresía con id {actor_company_user_id} no existe")
    return membresia


def _exigir_roles_write(actor_company_user_id, current_user_id):
    membresia = _membresia_del_actor(actor_company_user_id)
    exigir_permiso(membresia["id"], "roles.write", current_user_id, membresia["company_id"])


def obtener_rol_o_error(role_id):
    rol = repo.obtener_rol(parse_id(role_id, "ID de rol"))
    if rol is None:
        raise AppError(f"El rol con id {role_id} no existe")
    return rol


def listar_roles(active_only):
    return repo.obtener_roles(active_only)


def crear_rol(data, actor_company_user_id, current_user_id):
    code = (data.code or "").strip().upper()
    if not ROLE_CODE_REGEX.match(code):
        raise AppError("El código del rol debe usar mayúsculas, dígitos o guion bajo, por ejemplo AUDITOR")
    name = validar_nombre(data.name)
    _exigir_roles_write(actor_company_user_id, current_user_id)

    if repo.obtener_rol_por_codigo(code):
        raise AppError(f"Ya existe un rol con el código {code}")
    try:
        return repo.crear_rol(code, name, texto_opcional(data.description))
    except UniqueViolation:
        raise AppError(f"Ya existe un rol con el código {code}")


def desactivar_rol(role_id, actor_company_user_id, current_user_id):
    rol = obtener_rol_o_error(role_id)
    _exigir_roles_write(actor_company_user_id, current_user_id)
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


def crear_permiso(data, actor_company_user_id, current_user_id):
    code = (data.code or "").strip().lower()
    if not PERMISSION_CODE_REGEX.match(code):
        raise AppError("El código del permiso se escribe recurso.accion, por ejemplo reports.read")
    name = validar_nombre(data.name)
    _exigir_roles_write(actor_company_user_id, current_user_id)

    if repo.obtener_permiso_por_codigo(code):
        raise AppError(f"Ya existe un permiso con el código {code}")
    try:
        return repo.crear_permiso(code, name, texto_opcional(data.description))
    except UniqueViolation:
        raise AppError(f"Ya existe un permiso con el código {code}")


def listar_permisos_de_rol(role_id):
    rol = obtener_rol_o_error(role_id)
    return repo.obtener_permisos_de_rol(rol["id"])


def asignar_permiso_a_rol(data, actor_company_user_id, current_user_id):
    rol = obtener_rol_o_error(data.role_id)
    permiso = obtener_permiso_o_error(data.permission_id)
    _exigir_roles_write(actor_company_user_id, current_user_id)
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


def quitar_permiso_de_rol(role_id, permission_id, actor_company_user_id, current_user_id):
    rol = obtener_rol_o_error(role_id)
    permiso = obtener_permiso_o_error(permission_id)
    _exigir_roles_write(actor_company_user_id, current_user_id)
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


def asignar_rol(data, actor_company_user_id, current_user_id):
    membresia = user_repository.obtener_company_user(parse_id(data.company_user_id, "ID de membresía"))
    if membresia is None:
        raise AppError(f"La membresía con id {data.company_user_id} no existe")
    rol = obtener_rol_o_error(data.role_id)

    exigir_permiso(actor_company_user_id, "roles.write", current_user_id, membresia["company_id"])

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
