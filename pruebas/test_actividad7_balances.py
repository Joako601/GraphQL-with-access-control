"""Actividad 7: reglas puras del balance (sin base de datos).

Los esperados están escritos a mano desde la tabla de referencia del PDF, no con el servicio.
    python -m unittest pruebas.test_actividad7_balances -v
"""
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from services import balance_service
from services.finance_validators import validar_fecha_con_zona
from services.validators import AppError

ACTOR = {"id": 1, "company_id": 7, "user_id": 1}


def fila(account_id, name, opening="0", income="0", expense="0", active=True):
    """Fila tal como la devuelve el repositorio (PostgreSQL puede regresar 0 sin escala)."""
    return {"account_id": account_id, "account_name": name, "is_active": active,
            "opening_balance": Decimal(opening), "total_income": Decimal(income),
            "total_expense": Decimal(expense)}


REFERENCIA = [fila(1, "Banco", "1000.00", "3000.00", "2200.00"),
              fila(2, "Caja", "0", "500.00", "700.00"),
              fila(3, "Ahorro")]


class PeriodoTest(unittest.TestCase):
    def test_dias_completos_en_utc_con_fin_excluido(self):
        inicio, fin = balance_service.limites_del_periodo(date(2026, 10, 26), date(2026, 10, 30))
        self.assertEqual(inicio, datetime(2026, 10, 26, tzinfo=timezone.utc))
        self.assertEqual(fin, datetime(2026, 10, 31, tzinfo=timezone.utc))

    def test_un_solo_dia_es_valido(self):
        inicio, fin = balance_service.limites_del_periodo(date(2026, 10, 28), date(2026, 10, 28))
        self.assertEqual(fin - inicio, datetime(2026, 1, 2) - datetime(2026, 1, 1))

    def test_from_posterior_a_to_se_rechaza(self):
        with self.assertRaises(AppError):
            balance_service.limites_del_periodo(date(2026, 10, 30), date(2026, 10, 26))

    def test_transaction_date_se_normaliza_a_utc(self):
        local = datetime.fromisoformat("2026-10-27T06:00:00-06:00")
        self.assertEqual(validar_fecha_con_zona(local), datetime(2026, 10, 27, 12, tzinfo=timezone.utc))


class CuentaTest(unittest.TestCase):
    def test_caja_profit_negativo_y_en_rojo(self):
        caja = balance_service.calcular_cuenta(REFERENCIA[1])
        self.assertEqual(str(caja["opening_balance"]), "0.00")
        self.assertEqual(str(caja["profit"]), "-200.00")
        self.assertEqual(str(caja["closing_balance"]), "-200.00")
        self.assertTrue(caja["is_in_red"])

    def test_profit_negativo_con_saldo_previo_no_es_rojo(self):
        banco_28 = balance_service.calcular_cuenta(fila(1, "Banco", "2800.00", "0", "1000.00"))
        self.assertEqual(str(banco_28["profit"]), "-1000.00")
        self.assertEqual(str(banco_28["closing_balance"]), "1800.00")
        self.assertFalse(banco_28["is_in_red"])

    def test_cero_no_es_rojo_y_centavos_exactos(self):
        centavos = balance_service.calcular_cuenta(fila(9, "Centavos", "0", "0.30", "0.30"))
        self.assertEqual(str(centavos["closing_balance"]), "0.00")
        self.assertFalse(centavos["is_in_red"])


class GeneralTest(unittest.TestCase):
    def test_tabla_de_referencia(self):
        with patch.object(balance_service.repo, "obtener_balances", return_value=REFERENCIA), \
             patch.object(balance_service, "exigir_permiso"):
            general = balance_service.balance_general(date(2026, 10, 26), date(2026, 10, 30), ACTOR)
        esperado = {"opening_balance": "1000.00", "total_income": "3500.00", "total_expense": "2900.00",
                    "profit": "600.00", "closing_balance": "1600.00"}
        self.assertEqual({k: str(general[k]) for k in esperado}, esperado)
        self.assertEqual((general["currency"], general["is_in_red"], general["accounts_in_red"]), ("MXN", False, 1))
        self.assertEqual([c["account_id"] for c in general["accounts"]], [1, 2, 3])

    def test_empresa_sin_cuentas(self):
        with patch.object(balance_service.repo, "obtener_balances", return_value=[]), \
             patch.object(balance_service, "exigir_permiso"):
            general = balance_service.balance_general(date(2026, 10, 26), date(2026, 10, 30), ACTOR)
        self.assertEqual(str(general["closing_balance"]), "0.00")
        self.assertEqual((general["accounts"], general["accounts_in_red"], general["is_in_red"]), ([], 0, False))

    def test_cuenta_ajena_o_inexistente_mismo_error(self):
        with patch.object(balance_service.repo, "obtener_balances", return_value=[]), \
             patch.object(balance_service, "exigir_permiso"):
            with self.assertRaisesRegex(AppError, "^Cuenta no disponible$"):
                balance_service.balance_de_cuenta("999", date(2026, 10, 26), date(2026, 10, 30), ACTOR)


if __name__ == "__main__":
    unittest.main()
