from repositories import role_repository, user_repository
from services.validators import AppError


def exigir_permiso(actor, codigo, company_id=None, *, alternativo=None):
    """actor es la membresía que devolvió leer_actor; el rol se vuelve a leer en la base."""
    if company_id is not None and actor["company_id"] != company_id:
        raise AppError("El token no pertenece a esta empresa")
    usuario = user_repository.obtener_usuario(actor["user_id"])
    if not usuario or not usuario["is_active"]:
        raise AppError("El usuario está inactivo")

    asignacion = role_repository.obtener_rol_activo_de_membresia(actor["id"])
    if asignacion is None:
        raise AppError("La membresía no tiene un rol activo")
    rol = role_repository.obtener_rol(asignacion["role_id"])
    if not rol["is_active"]:
        raise AppError(f"El rol {rol['code']} está desactivado")

    if role_repository.rol_tiene_permiso(rol["id"], codigo):
        return actor
    if alternativo and role_repository.rol_tiene_permiso(rol["id"], alternativo):
        return actor
    raise AppError(f"Permiso denegado: el rol {rol['code']} no tiene el permiso {codigo}")
