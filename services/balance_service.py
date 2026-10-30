from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from repositories import balance_repository as repo
from services.permission_service import exigir_permiso
from services.validators import AppError, parse_id

CENTAVO = Decimal("0.01")
CERO = Decimal("0.00")
# El proyecto no guarda moneda: todos los importes del laboratorio son MXN.
MONEDA = "MXN"


def limites_del_periodo(from_date, to_date):
    """Días completos en UTC: inicio incluido y fin = medianoche del día siguiente a toDate, excluido."""
    if from_date > to_date:
        raise AppError("fromDate no puede ser posterior a toDate")
    inicio = datetime.combine(from_date, time.min, timezone.utc)
    fin = datetime.combine(to_date + timedelta(days=1), time.min, timezone.utc)
    return inicio, fin


def calcular_cuenta(row):
    opening = Decimal(row["opening_balance"]).quantize(CENTAVO)
    income = Decimal(row["total_income"]).quantize(CENTAVO)
    expense = Decimal(row["total_expense"]).quantize(CENTAVO)
    profit = income - expense
    closing = opening + profit
    return {
        "account_id": row["account_id"],
        "account_name": row["account_name"],
        "is_active": row["is_active"],
        "opening_balance": opening,
        "total_income": income,
        "total_expense": expense,
        "profit": profit,
        "closing_balance": closing,
        # Cero no es estar en rojo; profit negativo tampoco basta.
        "is_in_red": closing < 0,
    }


def _empresa_con_lectura(actor):
    # La empresa sale del token, nunca de un argumento: así no se puede pedir el balance de otra.
    exigir_permiso(actor, "accounts.read")
    exigir_permiso(actor, "transactions.read")
    return actor["company_id"]


def balance_de_cuenta(account_id, from_date, to_date, actor):
    company_id = _empresa_con_lectura(actor)
    inicio, fin = limites_del_periodo(from_date, to_date)
    filas = repo.obtener_balances(company_id, inicio, fin, parse_id(account_id, "ID de cuenta"))
    if not filas:
        # Mismo mensaje para inexistente y ajena: no revela qué IDs existen en otras empresas.
        raise AppError("Cuenta no disponible")
    return calcular_cuenta(filas[0])


def balance_general(from_date, to_date, actor):
    company_id = _empresa_con_lectura(actor)
    inicio, fin = limites_del_periodo(from_date, to_date)
    cuentas = [calcular_cuenta(row) for row in repo.obtener_balances(company_id, inicio, fin)]

    def total(campo):
        return sum((cuenta[campo] for cuenta in cuentas), CERO)

    closing = total("closing_balance")
    return {
        "company_id": company_id,
        "currency": MONEDA,
        "from_date": from_date,
        "to_date": to_date,
        "opening_balance": total("opening_balance"),
        "total_income": total("total_income"),
        "total_expense": total("total_expense"),
        "profit": total("profit"),
        "closing_balance": closing,
        "is_in_red": closing < 0,
        "accounts_in_red": sum(1 for cuenta in cuentas if cuenta["is_in_red"]),
        "accounts": cuentas,
    }
