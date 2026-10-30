-- Unidad II, Actividad 7 — SQL de laboratorio (PostgreSQL).
-- Ejecuta un bloque a la vez en psql dentro del contenedor, con los IDs como variables, por ejemplo:
--   docker exec -it unidad2-actividad4-postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -v empresa=1 -v cuenta=3 -v movimiento=7
-- Los IDs de la última ejecución están en docs/Actividad7/evidencias/resultados.json y docs/Actividad7/variables/.

-- Todas las fechas se guardan en TIMESTAMPTZ; las comparaciones de balance usan límites en UTC.
SET TIME ZONE 'UTC';

-- ---------- Comprobación manual de la tabla de referencia (26 al 30 de octubre) ----------
-- Calcula lo mismo que el servicio, pero escrito aparte para comparar a mano.
SELECT a.name,
       SUM(CASE WHEN t.transaction_date <  '2026-10-26' THEN CASE t.transaction_type WHEN 'INCOME' THEN t.amount ELSE -t.amount END ELSE 0 END) AS saldo_inicial,
       SUM(CASE WHEN t.transaction_date >= '2026-10-26' AND t.transaction_type = 'INCOME'  THEN t.amount ELSE 0 END) AS ingresos,
       SUM(CASE WHEN t.transaction_date >= '2026-10-26' AND t.transaction_type = 'EXPENSE' THEN t.amount ELSE 0 END) AS egresos
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id AND t.is_active AND t.transaction_date < '2026-10-31'
WHERE a.company_id = :empresa
GROUP BY a.id, a.name
ORDER BY a.id;

-- Consultar un balance no debe cambiar filas: compara antes y después de ejecutar las consultas GraphQL.
SELECT COUNT(*), MAX(updated_at) FROM transactions WHERE company_id = :empresa;

-- ---------- B07: desactivar un movimiento (también existe la mutación deleteTransaction) ----------
UPDATE transactions SET is_active = FALSE, updated_at = NOW() WHERE id = :movimiento;
-- Restaurar:
UPDATE transactions SET is_active = TRUE, updated_at = NOW() WHERE id = :movimiento;

-- ---------- B08: desactivar una cuenta (no existe mutación para hacerlo) ----------
UPDATE accounts SET is_active = FALSE, updated_at = NOW() WHERE id = :cuenta;
-- Restaurar:
UPDATE accounts SET is_active = TRUE, updated_at = NOW() WHERE id = :cuenta;

-- ---------- Índice que apoya las consultas por cuenta y fecha ----------
-- Ya existe desde database_finanzas.sql; no se agrega ninguno nuevo:
-- CREATE INDEX IF NOT EXISTS transactions_account_idx ON transactions (account_id, transaction_date DESC);
