from psycopg.errors import UniqueViolation

from repositories import concept_repository as repo
from services.account_service import obtener_empresa_activa
from services.company_service import obtener_empresa_o_error
from services.finance_validators import texto_opcional
from services.permission_service import exigir_permiso
from services.validators import AppError, parse_id, validar_nombre


def obtener_concepto_o_error(concept_id):
    concepto = repo.obtener_concepto(parse_id(concept_id, "ID de concepto"))
    if concepto is None:
        raise AppError(f"El concepto con id {concept_id} no existe")
    return concepto


def crear_concepto(data, actor):
    empresa = obtener_empresa_activa(data.company_id)
    exigir_permiso(actor, "concepts.write", empresa["id"])

    name = validar_nombre(data.name)
    if repo.obtener_concepto_por_nombre(empresa["id"], name):
        raise AppError(f"Ya existe un concepto llamado «{name}» en esta empresa")

    try:
        return repo.crear_concepto(
            empresa["id"],
            data.concept_type.value,
            name,
            texto_opcional(data.short_description),
            texto_opcional(data.long_description),
        )
    except UniqueViolation:
        raise AppError(f"Ya existe un concepto llamado «{name}» en esta empresa")


def listar_conceptos(company_id, concept_type, active_only, actor):
    empresa = obtener_empresa_o_error(company_id)
    exigir_permiso(actor, "concepts.read", empresa["id"])
    tipo = concept_type.value if concept_type else None
    return repo.obtener_conceptos(empresa["id"], tipo, active_only)
