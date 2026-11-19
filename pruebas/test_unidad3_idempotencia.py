"""Unidad III, Actividad 2: reglas de idempotencia de createTransaction (sin base de datos).

El repositorio se sustituye con mocks; la comprobación contra PostgreSQL está en unidad3_actividad2_idempotencia.py.
    python -m unittest pruebas.test_unidad3_idempotencia -v
"""
import os
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("JWT_SECRET", "solo-para-pruebas")  # services.auth lo exige al importarse

from models.finance_types import TransactionType  # noqa: E402
from services import transaction_service as svc  # noqa: E402
from services.validators import AppError  # noqa: E402

ACTOR = {"id": 3, "company_id": 1, "user_id": 3}
CUENTA = {"id": 10, "company_id": 1, "name": "Banco", "is_active": True}
CONCEPTO = {"id": 20, "company_id": 1, "name": "Renta", "is_active": True, "concept_type": "EXPENSE"}
MOVIMIENTO = {"id": 42, "company_id": 1}


def entrada(llave="llave-x", monto="100.00", **extra):
    datos = dict(idempotency_key=llave, account_id="10", concept_id="20", transaction_type=TransactionType.EXPENSE,
                 amount=Decimal(monto), transaction_date=None, short_description="Renta", long_description=None)
    datos.update(extra)
    return SimpleNamespace(**datos)


def hash_de(monto="100.00"):
    return svc.hash_del_cuerpo(10, 20, "EXPENSE", Decimal(monto), None, "Renta", None)


@patch.object(svc, "exigir_permiso", lambda *a, **k: ACTOR)
@patch.object(svc, "obtener_empresa_activa", lambda *a: {"id": 1, "is_active": True})
@patch.object(svc, "obtener_cuenta_o_error", lambda *a: CUENTA)
@patch.object(svc, "obtener_concepto_o_error", lambda *a: CONCEPTO)
@patch.object(svc.account_concept_repository, "obtener_relacion", lambda *a: {"is_active": True})
class CrearMovimientoTest(unittest.TestCase):

    @patch.object(svc.repo, "crear_movimiento", return_value=MOVIMIENTO)
    @patch.object(svc.repo, "obtener_llave", return_value=None)
    def test_primera_peticion_inserta_movimiento_y_llave_juntos(self, _llave, crear):
        self.assertEqual(svc.crear_movimiento(entrada(), ACTOR), MOVIMIENTO)
        crear.assert_called_once()
        self.assertEqual(crear.call_args.kwargs["idempotency"], ("createTransaction", "llave-x", hash_de()))

    @patch.object(svc.repo, "obtener_movimiento", return_value=MOVIMIENTO)
    @patch.object(svc.repo, "crear_movimiento")
    @patch.object(svc.repo, "obtener_llave")
    def test_reintento_con_la_misma_llave_devuelve_el_mismo_id_sin_insert(self, llave, crear, _mov):
        llave.return_value = {"request_hash": hash_de(), "transaction_id": 42}
        self.assertEqual(svc.crear_movimiento(entrada(), ACTOR)["id"], 42)
        crear.assert_not_called()

    @patch.object(svc.repo, "crear_movimiento")
    @patch.object(svc.repo, "obtener_llave")
    def test_misma_llave_con_otro_monto_se_rechaza(self, llave, crear):
        llave.return_value = {"request_hash": hash_de("100.00"), "transaction_id": 42}
        with self.assertRaisesRegex(AppError, "ya se usó con otros datos"):
            svc.crear_movimiento(entrada(monto="999.00"), ACTOR)
        crear.assert_not_called()

    @patch.object(svc.repo, "obtener_movimiento", return_value=MOVIMIENTO)
    @patch.object(svc.repo, "crear_movimiento", return_value=None)
    @patch.object(svc.repo, "obtener_llave")
    def test_carrera_el_indice_unico_gana_y_se_devuelve_el_guardado(self, llave, _crear, _mov):
        # Primera lectura: aún no está. El INSERT choca con el índice (None). Segunda lectura: la de la otra petición.
        llave.side_effect = [None, {"request_hash": hash_de(), "transaction_id": 42}]
        self.assertEqual(svc.crear_movimiento(entrada(), ACTOR)["id"], 42)

    @patch.object(svc.repo, "obtener_movimiento", return_value=MOVIMIENTO)
    @patch.object(svc.repo, "obtener_llave")
    def test_reintento_responde_aunque_el_concepto_ya_no_este_asignado(self, llave, _mov):
        llave.return_value = {"request_hash": hash_de(), "transaction_id": 42}
        with patch.object(svc.account_concept_repository, "obtener_relacion", return_value=None):
            self.assertEqual(svc.crear_movimiento(entrada(), ACTOR)["id"], 42)

    def test_llave_vacia_o_larga_se_rechaza(self):
        for llave in ("", "   ", None, "x" * 101):
            with self.assertRaisesRegex(AppError, "idempotencyKey"):
                svc.crear_movimiento(entrada(llave=llave), ACTOR)


class HashTest(unittest.TestCase):
    def test_montos_equivalentes_dan_el_mismo_hash(self):
        self.assertEqual(hash_de("100"), hash_de("100.00"))

    def test_otro_monto_otra_cuenta_u_otra_descripcion_cambian_el_hash(self):
        base = hash_de()
        self.assertNotEqual(base, hash_de("100.01"))
        self.assertNotEqual(base, svc.hash_del_cuerpo(11, 20, "EXPENSE", Decimal("100"), None, "Renta", None))
        self.assertNotEqual(base, svc.hash_del_cuerpo(10, 20, "EXPENSE", Decimal("100"), None, "Otra", None))


if __name__ == "__main__":
    unittest.main()
