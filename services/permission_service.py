from repositories import role_repository, user_repository
from services.validators import AppError, parse_id


def exigir_permiso(actor_company_user_id, codigo, current_user_id, company_id=None):
    membresia = user_repository.obtener_company_user(parse_id(actor_company_user_id, "actorCompanyUserId"))
    if membresia is None:
        raise AppError(f"La membresía con id {actor_company_user_id} no existe")
    if membresia["user_id"] != current_user_id:
        raise AppError("La membresía indicada en actorCompanyUserId no pertenece al usuario autenticado")
    if company_id is not None and membresia["company_id"] != company_id:
        raise AppError("La membresía indicada en actorCompanyUserId no pertenece a esta empresa")
    if not membresia["is_active"]:
        raise AppError("La membresía está inactiva")
    usuario = user_repository.obtener_usuario(current_user_id)
    if not usuario or not usuario["is_active"]:
        raise AppError("El usuario está inactivo")

    asignacion = role_repository.obtener_rol_activo_de_membresia(membresia["id"])
    if asignacion is None:
        raise AppError("La membresía no tiene un rol activo")
    rol = role_repository.obtener_rol(asignacion["role_id"])
    if not rol["is_active"]:
        raise AppError(f"El rol {rol['code']} está desactivado")

    if not role_repository.rol_tiene_permiso(rol["id"], codigo):
        raise AppError(f"Permiso denegado: el rol {rol['code']} no tiene el permiso {codigo}")
    return membresia
