from repositories import company_repository as repo
from services.validators import AppError, parse_id, validar_email, validar_nombre, validar_rfc


def _validar_rfc_unico(tax_id, company_id=None):
    existente = repo.obtener_empresa_por_rfc(tax_id)
    if existente and existente["id"] != company_id:
        raise AppError(f"Ya existe una empresa con el RFC {tax_id}")


def obtener_empresa_o_error(company_id):
    empresa = repo.obtener_empresa(parse_id(company_id, "ID de empresa"))
    if empresa is None:
        raise AppError(f"La empresa con id {company_id} no existe")
    return empresa


def crear_empresa(data):
    name = validar_nombre(data.name)
    email = validar_email(data.email) if data.email else None
    tax_id = validar_rfc(data.tax_id) if data.tax_id else None
    if tax_id:
        _validar_rfc_unico(tax_id)
    return repo.crear_empresa(name, data.legal_name, tax_id, email, data.phone)


def listar_empresas(active_only):
    return repo.obtener_empresas(active_only)


def actualizar_empresa(data):
    empresa = obtener_empresa_o_error(data.id)


    campos = {}
    if data.name is not None:
        campos["name"] = validar_nombre(data.name)
    if data.legal_name is not None:
        campos["legal_name"] = data.legal_name
    if data.tax_id is not None:
        campos["tax_id"] = validar_rfc(data.tax_id)
        _validar_rfc_unico(campos["tax_id"], empresa["id"])
    if data.email is not None:
        campos["email"] = validar_email(data.email)
    if data.phone is not None:
        campos["phone"] = data.phone
    if data.is_active is not None:
        campos["is_active"] = data.is_active

    if not campos:
        raise AppError("No se envió ningún campo para actualizar")
    return repo.actualizar_empresa(empresa["id"], campos)


def desactivar_empresa(company_id):
    empresa = obtener_empresa_o_error(company_id)
    return repo.desactivar_empresa(empresa["id"])
