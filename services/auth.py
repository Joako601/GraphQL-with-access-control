import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv

from repositories import user_repository
from services.validators import AppError

load_dotenv()

# El secreto vive solo en el ambiente: si estuviera en el código, cualquiera podría firmar un token ajeno.
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
JWT_ALGORITHM = "HS256"


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def crear_token(company_user_id, company_id):
    # Sin contraseña ni permisos: los permisos se leen en la base en cada petición.
    datos = {
        "companyUserId": company_user_id,
        "companyId": company_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(datos, JWT_SECRET, algorithm=JWT_ALGORITHM)


def leer_actor(info):
    """Devuelve la membresía firmada en Authorization: Bearer <token>."""
    encabezado = info.context["request"].headers.get("authorization", "")
    if not encabezado.startswith("Bearer "):
        raise AppError("Falta el token: envía Authorization: Bearer <token>")
    try:
        # Solo HS256: un token con "alg": "none" u otro algoritmo no pasa.
        datos = jwt.decode(encabezado.removeprefix("Bearer ").strip(), JWT_SECRET, algorithms=[JWT_ALGORITHM])
        company_user_id = int(datos["companyUserId"])
        company_id = int(datos["companyId"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise AppError("El token no es válido o ya venció")

    membresia = user_repository.obtener_company_user(company_user_id)
    if membresia is None or not membresia["is_active"]:
        raise AppError("La membresía no existe o no está activa")
    if membresia["company_id"] != company_id:
        raise AppError("El token no corresponde a esa empresa")
    return membresia
