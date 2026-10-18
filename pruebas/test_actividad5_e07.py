"""E07: a failed permission-list update must leave persisted rows unchanged."""

import uuid
import unittest
from unittest.mock import patch

from database.database import get_connection
from repositories import role_repository


class ControlledFailure(RuntimeError):
    pass


class FailAfterFirstExecute:
    """Raise after SQL was sent but before the surrounding connection commits."""

    def __init__(self, connection):
        self.connection = connection
        self.execute_count = 0

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback):
        return self.connection.__exit__(exc_type, exc, traceback)

    def execute(self, query, params=None):
        result = self.connection.execute(query, params)
        self.execute_count += 1
        if self.execute_count == 1:
            raise ControlledFailure("E07: injected after the first pending write")
        return result


class RolePermissionsRollbackTest(unittest.TestCase):
    def setUp(self):
        suffix = uuid.uuid4().hex[:12]
        self.role_code = f"E07_{suffix.upper()}"
        self.permission_codes = [f"e07test.{suffix}.read", f"e07test.{suffix}.write"]
        with get_connection() as connection:
            role = connection.execute(
                "INSERT INTO roles (code, name) VALUES (%s, %s) RETURNING id;",
                (self.role_code, "E07 rollback test"),
            ).fetchone()
            self.role_id = role["id"]
            self.permission_ids = []
            for code in self.permission_codes:
                row = connection.execute(
                    "INSERT INTO permissions (code, name) VALUES (%s, %s) RETURNING id;",
                    (code, code),
                ).fetchone()
                self.permission_ids.append(row["id"])
            connection.execute(
                "INSERT INTO role_permissions (role_id, permission_id, is_active) VALUES (%s, %s, TRUE);",
                (self.role_id, self.permission_ids[0]),
            )
            connection.execute(
                "INSERT INTO role_permissions (role_id, permission_id, is_active) VALUES (%s, %s, FALSE);",
                (self.role_id, self.permission_ids[1]),
            )

    def tearDown(self):
        with get_connection() as connection:
            connection.execute("DELETE FROM role_permissions WHERE role_id = %s;", (self.role_id,))
            connection.execute("DELETE FROM roles WHERE id = %s;", (self.role_id,))
            connection.execute("DELETE FROM permissions WHERE id = ANY(%s);", (self.permission_ids,))

    def _persisted_states(self):
        with get_connection() as connection:
            return connection.execute(
                """SELECT p.code, rp.is_active
                   FROM role_permissions rp
                   JOIN permissions p ON p.id = rp.permission_id
                   WHERE rp.role_id = %s
                   ORDER BY p.code;""",
                (self.role_id,),
            ).fetchall()

    def test_failure_after_first_write_rolls_back_every_relationship_change(self):
        before = self._persisted_states()
        original_get_connection = role_repository.get_connection

        def failing_connection():
            return FailAfterFirstExecute(original_get_connection())

        with patch.object(role_repository, "get_connection", side_effect=failing_connection):
            with self.assertRaisesRegex(ControlledFailure, "first pending write"):
                role_repository.aplicar_configuracion_rol(
                    self.role_id,
                    [{"id": self.permission_ids[1]}],
                    [{"id": self.permission_ids[0]}],
                )

        # A fresh connection proves the uncommitted insert/reactivation did not persist.
        self.assertEqual(self._persisted_states(), before)


if __name__ == "__main__":
    unittest.main()
