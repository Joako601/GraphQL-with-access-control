from psycopg.errors import UniqueViolation

from repositories import account_repository as repo
from services.company_service import obtener_empresa_o_error
from services.finance_validators import texto_opcional, validar_digitos
from services.permission_service import exigir_permiso
from services.validators import AppError, parse_id, validar_nombre



# ACCESO A LOS DATOS DE UNA EMPRESA


def obtener_empresa_activa(company_id):
    empresa = obtener_empresa_o_error(company_id)
    if not empresa["is_active"]:
        raise AppError("La empresa está inactiva")
    return empresa



# CUENTAS


def obtener_cuenta_o_error(account_id):
    cuenta = repo.obtener_cuenta(parse_id(account_id, "ID de cuenta"))
    if cuenta is None:
        raise AppError(f"La cuenta con id {account_id} no existe")
    return cuenta


def crear_cuenta(data, actor_company_user_id, current_user_id):
    empresa = obtener_empresa_activa(data.company_id)
    exigir_permiso(actor_company_user_id, "accounts.write", current_user_id, empresa["id"])

    name = validar_nombre(data.name)
    account_number = validar_digitos(data.account_number, 4, 20, "El número de cuenta")
    clabe = validar_digitos(data.clabe, 18, 18, "La CLABE")
    card_last_digits = validar_digitos(data.card_last_digits, 4, 4, "Los últimos dígitos de la tarjeta")

   
    if repo.obtener_cuenta_por_nombre(empresa["id"], name):
        raise AppError(f"Ya existe una cuenta llamada «{name}» en esta empresa")
    if clabe and repo.obtener_cuenta_por_clabe(clabe):
        raise AppError(f"Ya existe una cuenta registrada con la CLABE {clabe}")

    try:
        return repo.crear_cuenta(
            empresa["id"],
            data.account_type.value,
            name,
            texto_opcional(data.bank_name),
            account_number,
            clabe,
            card_last_digits,
            texto_opcional(data.short_description),
            texto_opcional(data.long_description),
        )
    except UniqueViolation:
       
        raise AppError(f"Ya existe una cuenta con el nombre «{name}» o con esa CLABE")


def listar_cuentas(company_id, account_type, active_only, actor_company_user_id, current_user_id):
    empresa = obtener_empresa_o_error(company_id)
    exigir_permiso(actor_company_user_id, "accounts.read", current_user_id, empresa["id"])
    tipo = account_type.value if account_type else None
    return repo.obtener_cuentas(empresa["id"], tipo, active_only)
