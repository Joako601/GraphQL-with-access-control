from psycopg.errors import UniqueViolation

from repositories import account_concept_repository as repo
from services.account_service import obtener_cuenta_o_error, obtener_empresa_activa
from services.concept_service import obtener_concepto_o_error
from services.permission_service import exigir_permiso
from services.validators import AppError


def _cuenta_y_concepto(account_id, concept_id, actor_company_user_id, current_user_id):
    cuenta = obtener_cuenta_o_error(account_id)
    concepto = obtener_concepto_o_error(concept_id)
    exigir_permiso(actor_company_user_id, "concepts.write", current_user_id, cuenta["company_id"])
    if concepto["company_id"] != cuenta["company_id"]:
        raise AppError("La cuenta y el concepto pertenecen a empresas diferentes")
    return cuenta, concepto


def asignar_concepto(data, actor_company_user_id, current_user_id):
    cuenta, concepto = _cuenta_y_concepto(data.account_id, data.concept_id, actor_company_user_id, current_user_id)
    obtener_empresa_activa(cuenta["company_id"])
    if not cuenta["is_active"]:
        raise AppError(f"La cuenta «{cuenta['name']}» está inactiva")
    if not concepto["is_active"]:
        raise AppError(f"El concepto «{concepto['name']}» está inactivo")

    relacion = repo.obtener_relacion(cuenta["id"], concepto["id"])
    if relacion and relacion["is_active"]:
        raise AppError(f"El concepto «{concepto['name']}» ya está asignado a la cuenta «{cuenta['name']}»")
    if relacion:
        return repo.reactivar_relacion(relacion["id"])

    try:
        return repo.crear_relacion(cuenta["company_id"], cuenta["id"], concepto["id"])
    except UniqueViolation:
        raise AppError(f"El concepto «{concepto['name']}» ya está asignado a la cuenta «{cuenta['name']}»")


def retirar_concepto(account_id, concept_id, actor_company_user_id, current_user_id):
    cuenta, concepto = _cuenta_y_concepto(account_id, concept_id, actor_company_user_id, current_user_id)
    relacion = repo.obtener_relacion(cuenta["id"], concepto["id"])
    if not relacion or not relacion["is_active"]:
        raise AppError(f"El concepto «{concepto['name']}» no está asignado a la cuenta «{cuenta['name']}»")

    repo.desactivar_relacion(relacion["id"])
    return True


def listar_conceptos_de_cuenta(account_id, active_only, actor_company_user_id, current_user_id):
    cuenta = obtener_cuenta_o_error(account_id)
    exigir_permiso(actor_company_user_id, "concepts.read", current_user_id, cuenta["company_id"])
    return repo.obtener_relaciones_de_cuenta(cuenta["id"], active_only is not False)
