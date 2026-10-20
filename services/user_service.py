from repositories import user_repository as repo
from services import role_service
from services.auth import crear_token, hash_password, verificar_password
from services.company_service import obtener_empresa_o_error
from services.permission_service import exigir_permiso
from services.validators import AppError, parse_id, validar_email, validar_nombre, validar_password


def _registrar(empresa, data, is_admin, rol):
    if not empresa["is_active"]:
        raise AppError("La empresa está inactiva")

    name = validar_nombre(data.name)
    email = validar_email(data.email)
    password = validar_password(data.password)

    if repo.obtener_usuario_por_email(email):
        raise AppError(f"El correo {email} ya está registrado")

    return repo.crear_usuario_en_empresa(
        empresa["id"], name, email, hash_password(password), is_admin, rol["id"]
    )


def crear_admin(data):
    empresa = obtener_empresa_o_error(data.company_id)
    if repo.existe_admin(empresa["id"]):
        raise AppError("La empresa ya tiene un administrador principal")
    return _registrar(empresa, data, True, role_service.obtener_rol_por_codigo_o_error(role_service.ADMIN_ROLE))


def crear_usuario(data, actor):
    empresa = obtener_empresa_o_error(data.company_id)
    exigir_permiso(actor, "company.users.write", empresa["id"])
    return _registrar(empresa, data, False, role_service.rol_inicial(data.role_id))


def listar_usuarios(company_id, actor):
    empresa = obtener_empresa_o_error(company_id)
    exigir_permiso(actor, "company.users.read", empresa["id"])
    return repo.obtener_usuarios_de_empresa(empresa["id"])


def desactivar_usuario(company_user_id, actor):
    company_user = repo.obtener_company_user(parse_id(company_user_id))
    if company_user is None:
        raise AppError(f"El usuario de empresa con id {company_user_id} no existe")
    exigir_permiso(actor, "company.users.write", company_user["company_id"])
    if company_user["is_admin"]:
        raise AppError("No se puede desactivar al administrador principal")
    return repo.desactivar_company_user(company_user["id"])


def _membresia_para_login(user_id, company_id):
    membresias = [m for m in repo.obtener_membresias_de_usuario(user_id) if m["is_active"]]
    if company_id is not None:
        membresias = [m for m in membresias if m["company_id"] == parse_id(company_id, "companyId")]
    if not membresias:
        raise AppError("El usuario no tiene una membresía activa en esa empresa")
    if len(membresias) > 1:
        raise AppError("El usuario pertenece a varias empresas: indica companyId para elegir una")
    return membresias[0]


def login(data):
    user = repo.obtener_usuario_por_email((data.email or "").strip().lower())
    if not user or not verificar_password(data.password, user["password_hash"]):
        raise AppError("Correo o contraseña incorrectos")
    if not user["is_active"]:
        raise AppError("El usuario está inactivo")
    # companyId del token se copia de la fila de la membresía, nunca del cliente.
    membresia = _membresia_para_login(user["id"], data.company_id)
    token = crear_token(membresia["id"], membresia["company_id"])
    return {"token": token, "token_type": "bearer", "user": user}
