import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv

from services.validators import AppError

load_dotenv()

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
JWT_ALGORITHM = "HS256"


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def crear_token(user_id):
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def usuario_actual(info):
    """Obtiene el id del usuario a partir del header Authorization: Bearer <token>."""
    header = info.context["request"].headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise AppError("No autenticado: falta el header Authorization: Bearer <token>")
    try:
        payload = jwt.decode(header[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AppError("El token ha expirado, inicia sesión de nuevo")
    except jwt.InvalidTokenError:
        raise AppError("Token inválido")
    return int(payload["sub"])
