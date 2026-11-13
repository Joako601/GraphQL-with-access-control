"""Unidad III, Actividad 1: CORS para el dashboard (sin base de datos).

Solo se usa la consulta {__typename}, que no toca PostgreSQL; TestClient sin `with` no ejecuta el lifespan.
    python -m unittest pruebas.test_unidad3_cors -v
"""
import os
import unittest

os.environ.setdefault("JWT_SECRET", "solo-para-pruebas")  # services.auth lo exige al importarse
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)
PREFLIGHT = {"Access-Control-Request-Method": "POST",
             "Access-Control-Request-Headers": "authorization,content-type"}


class CorsTest(unittest.TestCase):
    def test_preflight_del_dashboard_permite_bearer(self):
        r = client.options("/graphql", headers={"Origin": "http://localhost:5173", **PREFLIGHT})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["access-control-allow-origin"], "http://localhost:5173")
        self.assertIn("authorization", r.headers["access-control-allow-headers"].lower())

    def test_post_del_dashboard_lleva_encabezado_cors(self):
        r = client.post("/graphql", json={"query": "{ __typename }"}, headers={"Origin": "http://localhost:5173"})
        self.assertEqual(r.json(), {"data": {"__typename": "Query"}})
        self.assertEqual(r.headers["access-control-allow-origin"], "http://localhost:5173")

    def test_origen_no_listado_no_recibe_permiso(self):
        r = client.options("/graphql", headers={"Origin": "http://evil.test", **PREFLIGHT})
        self.assertNotIn("access-control-allow-origin", r.headers)


if __name__ == "__main__":
    unittest.main()
