from decimal import Decimal, InvalidOperation

from services.validators import AppError


MONTO_MAXIMO = Decimal("999999999999.99")


def texto_opcional(value):
    """Quita espacios exteriores y convierte el texto vacío en None."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def validar_digitos(value, minimo, maximo, campo):
    """Valida un campo opcional formado solo por dígitos (CLABE, número de cuenta, últimos dígitos)."""
    value = texto_opcional(value)
    if value is None:
        return None
    if not value.isdigit() or not minimo <= len(value) <= maximo:
        if minimo == maximo:
            raise AppError(f"{campo} debe tener exactamente {minimo} dígitos")
        raise AppError(f"{campo} debe tener entre {minimo} y {maximo} dígitos")
    return value


def validar_monto(amount):
    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        raise AppError(f"El monto no es un número válido: {amount}")
    if not amount.is_finite() or amount <= 0:
        raise AppError("El monto del movimiento debe ser mayor que cero")
    if amount.as_tuple().exponent < -2:
        raise AppError("El monto admite como máximo dos decimales")
    if amount > MONTO_MAXIMO:
        raise AppError("El monto excede el máximo permitido de 999,999,999,999.99")
    return amount


def validar_fecha_con_zona(value):
    
    if value is not None and value.tzinfo is None:
        raise AppError("La fecha del movimiento debe incluir la zona horaria, por ejemplo 2026-09-01T10:00:00-06:00")
    return value


def validar_paginacion(limit, offset):
    limit = 50 if limit is None else limit
    offset = 0 if offset is None else offset
    if not 1 <= limit <= 100:
        raise AppError("El límite debe estar entre 1 y 100")
    if offset < 0:
        raise AppError("El desplazamiento (offset) no puede ser negativo")
    return limit, offset
