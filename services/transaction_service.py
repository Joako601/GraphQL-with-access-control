import hashlib
import json

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


OPERACION_CREAR = "createTransaction"
LLAVE_MAXIMO = 100


def validar_llave(value):
    """La llave la genera el cliente (UUID u otro texto opaco); solo se exige que exista y quepa."""
    llave = (value or "").strip()
    if not llave:
        raise AppError("idempotencyKey es obligatoria: genera una llave por acción y reenvíala en cada reintento")
    if len(llave) > LLAVE_MAXIMO:
        raise AppError(f"idempotencyKey admite como máximo {LLAVE_MAXIMO} caracteres")
    return llave


def hash_del_cuerpo(account_id, concept_id, transaction_type, amount, transaction_date,
                    short_description, long_description):
    """SHA-256 del cuerpo ya normalizado: "100", "100.0" y "100.00" dan el mismo hash; otra cuenta u otro
    monto, no."""
    cuerpo = {
        "accountId": int(account_id),
        "conceptId": int(concept_id),
        "transactionType": transaction_type,
        "amount": f"{amount:.2f}",
        "transactionDate": transaction_date.isoformat() if transaction_date else None,
        "shortDescription": short_description,
        "longDescription": long_description,
    }
    texto = json.dumps(cuerpo, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _repetir(llave_guardada, request_hash):
    """Reintento: misma llave. Si el cuerpo coincide se devuelve el movimiento ya guardado (mismo id)."""
    if llave_guardada["request_hash"] != request_hash:
        raise AppError(
            "Esta idempotencyKey ya se usó con otros datos (cuenta, concepto, tipo, monto, fecha o descripción). "
            "Para un movimiento nuevo genera otra llave"
        )
    return repo.obtener_movimiento(llave_guardada["transaction_id"])


def crear_movimiento(data, actor):
    llave = validar_llave(data.idempotency_key)
    amount = validar_monto(data.amount)
    transaction_date = validar_fecha_con_zona(data.transaction_date)

    cuenta = obtener_cuenta_o_error(data.account_id)
    concepto = obtener_concepto_o_error(data.concept_id)

    exigir_permiso(actor, "transactions.write", cuenta["company_id"])
    if concepto["company_id"] != cuenta["company_id"]:
        raise AppError(f"El concepto «{concepto['name']}» no pertenece a la empresa de la cuenta")

    transaction_type = data.transaction_type.value
    short_description = texto_opcional(data.short_description)
    long_description = texto_opcional(data.long_description)
    request_hash = hash_del_cuerpo(cuenta["id"], concepto["id"], transaction_type, amount, transaction_date,
                                   short_description, long_description)

    # 1) ¿Ya existe la llave? Entonces es un reintento: no se valida ni se inserta otra vez. Va antes de las
    #    reglas de negocio para que el reintento devuelva lo mismo aunque, entre tanto, el concepto se haya quitado.
    guardada = repo.obtener_llave(cuenta["company_id"], OPERACION_CREAR, llave)
    if guardada:
        return _repetir(guardada, request_hash)

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

    if transaction_type != concepto["concept_type"]:
        raise AppError(
            f"El tipo de movimiento {transaction_type} no es compatible con el concepto "
            f"«{concepto['name']}», que es de tipo {concepto['concept_type']}"
        )

    # 2) Movimiento + llave en la misma transacción, un solo COMMIT.
    movimiento = repo.crear_movimiento(
        cuenta["company_id"],
        cuenta["id"],
        concepto["id"],
        transaction_type,
        amount,
        transaction_date,
        actor["user_id"],
        short_description,
        long_description,
        idempotency=(OPERACION_CREAR, llave, request_hash),
    )
    if movimiento is None:
        # 3) Dos peticiones con la misma llave llegaron a la vez: el índice único rechazó la segunda (ROLLBACK).
        #    Se lee la llave que guardó la primera y se responde con su movimiento.
        return _repetir(repo.obtener_llave(cuenta["company_id"], OPERACION_CREAR, llave), request_hash)
    return movimiento


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
