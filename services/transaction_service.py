from repositories import account_concept_repository
from repositories import transaction_repository as repo
from services.account_service import obtener_cuenta_o_error, obtener_empresa_activa
from services.concept_service import obtener_concepto_o_error
from services.finance_validators import (
    texto_opcional,
    validar_fecha_con_zona,
    validar_monto,
    validar_paginacion,
)
from services.permission_service import exigir_permiso
from services.validators import AppError, parse_id


def crear_movimiento(data, actor):
    amount = validar_monto(data.amount)
    transaction_date = validar_fecha_con_zona(data.transaction_date)

    cuenta = obtener_cuenta_o_error(data.account_id)
    concepto = obtener_concepto_o_error(data.concept_id)

    exigir_permiso(actor, "transactions.write", cuenta["company_id"])
    if concepto["company_id"] != cuenta["company_id"]:
        raise AppError(f"El concepto «{concepto['name']}» no pertenece a la empresa de la cuenta")

    obtener_empresa_activa(cuenta["company_id"])
    if not cuenta["is_active"]:
        raise AppError(f"La cuenta «{cuenta['name']}» está inactiva")
    if not concepto["is_active"]:
        raise AppError(f"El concepto «{concepto['name']}» está inactivo")

   
    relacion = account_concept_repository.obtener_relacion(cuenta["id"], concepto["id"])
    if not relacion or not relacion["is_active"]:
        raise AppError(
            f"El concepto «{concepto['name']}» no está permitido para la cuenta «{cuenta['name']}»"
        )

    transaction_type = data.transaction_type.value
    if transaction_type != concepto["concept_type"]:
        raise AppError(
            f"El tipo de movimiento {transaction_type} no es compatible con el concepto "
            f"«{concepto['name']}», que es de tipo {concepto['concept_type']}"
        )

    return repo.crear_movimiento(
        cuenta["company_id"],
        cuenta["id"],
        concepto["id"],
        transaction_type,
        amount,
        transaction_date,
        actor["user_id"],
        texto_opcional(data.short_description),
        texto_opcional(data.long_description),
    )


def listar_movimientos(account_id, transaction_type, limit, offset, actor):
    limit, offset = validar_paginacion(limit, offset)
    membresia = exigir_permiso(actor, "transactions.read")
    cuenta_id = None
    if account_id is not None:
        cuenta = obtener_cuenta_o_error(account_id)
        if cuenta["company_id"] != membresia["company_id"]:
            raise AppError("La cuenta no pertenece a la empresa de la membresía")
        cuenta_id = cuenta["id"]
    tipo = transaction_type.value if transaction_type else None

    return repo.obtener_movimientos(membresia["company_id"], cuenta_id, tipo, limit, offset)


def eliminar_movimiento(transaction_id, actor):
    movimiento = repo.obtener_movimiento(parse_id(transaction_id, "ID de movimiento"))
    if movimiento is None:
        raise AppError(f"El movimiento con id {transaction_id} no existe")
    exigir_permiso(actor, "transactions.write", movimiento["company_id"])
    if not movimiento["is_active"]:
        raise AppError(f"El movimiento con id {transaction_id} ya fue eliminado")
    return repo.eliminar_movimiento(movimiento["id"])
