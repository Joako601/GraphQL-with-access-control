import re


class AppError(Exception):
    """Error de negocio: su mensaje se muestra tal cual al cliente GraphQL."""


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


def parse_id(value, nombre="ID"):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise AppError(f"{nombre} inválido: {value}")


def validar_nombre(name):
    if name is None or not name.strip():
        raise AppError("El nombre es obligatorio")
    return name.strip()


def validar_email(email):
    email = (email or "").strip().lower()
    if not EMAIL_REGEX.match(email):
        raise AppError(f"El correo electrónico no tiene un formato válido: {email}")
    return email


def validar_rfc(tax_id):
    tax_id = tax_id.strip().upper()
    # RFC en México: 12 caracteres (persona moral) o 13 (persona física)
    if len(tax_id) not in (12, 13):
        raise AppError("El RFC debe tener 12 o 13 caracteres")
    return tax_id


def validar_password(password):
    if password is None or len(password) < 8:
        raise AppError("La contraseña debe tener al menos 8 caracteres")
    return password
