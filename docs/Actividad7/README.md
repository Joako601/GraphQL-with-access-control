# Unidad II, Actividad 7 — Balances por cuenta y balance general

## Integrantes

Tomados del historial del repositorio (el equipo debe confirmar la lista antes de entregar):

- Joaquín Uriona (@Joako601)
- Mateo Martin (@mateomartin21)
- Fernando Castro Hernández (@Fernando-Castro-Hernandez)
- Ariff Medina (@ariff-adivor)

## Qué se agregó

| Pieza | Archivo |
|---|---|
| Tipos `AccountBalance` y `GeneralBalance` | `models/balance_types.py` |
| Consultas `accountBalance` y `generalBalance` | `schema/finance_schema.py` |
| Reglas del cálculo (período, Decimal, rojos, permisos) | `services/balance_service.py` |
| Agregación SQL (una consulta, `LEFT JOIN` desde `accounts`) | `repositories/balance_repository.py` |
| `transactionDate` se normaliza a UTC | `services/finance_validators.py` |

El `accountBalance(accountId)` anterior (saldo histórico sin fechas) se reemplazó por el del contrato.
`createTransaction` ya aceptaba `transactionDate` opcional y `Transaction` ya exponía `transactionDate` y
`capturedAt`; si se omite la fecha se usa `NOW()` y `capturedAt` siempre lo pone el servidor.

**Base de datos:** el proyecto usa PostgreSQL (no MySQL). `amount` es `NUMERIC(14, 2)` y las fechas son
`TIMESTAMPTZ`, que se guardan en UTC. No se creó tabla ni columna de balance: se calcula en cada consulta.
El índice `transactions_account_idx (account_id, transaction_date DESC)` ya existía, así que no hay migración.

## Reglas implementadas

- Período: `fromDate` y `toDate` son `Date` y cuentan como días completos en UTC.
  Inicio `fromDate 00:00:00Z` incluido; fin `toDate + 1 día 00:00:00Z` excluido. `fromDate > toDate` es error.
- Saldo inicial = ingresos − egresos con `transaction_date < inicio`. Nunca se recibe del cliente.
- Solo cuentan movimientos con `is_active = TRUE`. Las cuentas desactivadas siguen apareciendo con `isActive: false`.
- Los filtros del movimiento van en el `ON` del `LEFT JOIN`: una cuenta sin movimientos aparece con `0.00`.
- No se une con `account_concepts`: `transaction_type` decide el signo y esa unión podría duplicar importes.
- Todo es `Decimal` cuantizado a centavos; los importes salen como `"1800.00"`. Moneda fija: `MXN`.
- Ambas consultas validan el token, exigen `accounts.read` y `transactions.read`, y toman la empresa del token.
  Cuenta ajena e inexistente responden igual: `Cuenta no disponible`.

## Saldo inicial, profit, saldo final y números rojos (Banco y Caja, 26 al 30 de octubre)

- **Banco** empieza el período con **1,000.00** (el ingreso de apertura del 25). En el período entran 3,000.00 y
  salen 2,200.00, así que su **profit es 800.00**, pero su **saldo final es 1,800.00**: la diferencia es el dinero
  que ya tenía. Si se consulta solo el 28, el profit es −1,000.00 y aun así el saldo final es 1,800.00: un día
  negativo no pone la cuenta en rojo.
- **Caja** empieza en **0.00**, recibe 500.00 y paga 700.00: profit **−200.00** y saldo final **−200.00**. Como el
  saldo final es menor que cero, **está en números rojos**.
- El general suma 1,600.00 (positivo, `isInRed: false`), pero `accountsInRed: 1` revela que Caja está en rojo.
  Por eso se devuelven los dos datos. Un saldo de exactamente 0.00 (Ahorro) no es rojo.

## Cómo ejecutar

1. Copia `.env.example` a `.env` y reemplaza los valores de ejemplo (incluido `JWT_SECRET`).
2. `docker compose up -d --build` — GraphiQL en `http://localhost:8004/graphql`.
3. Pruebas unitarias (sin base): `python -m unittest pruebas.test_actividad7_balances -v`
4. Preparar datos y ejecutar B01–B15 contra la API: `python pruebas/actividad7.py`
5. Evidencias en PDF con capturas de GraphiQL. Usa un `.venv` en la raíz (ya ignorado por Git): en Windows,
   un venv con ruta muy larga deja Playwright incompleto (`No module named playwright.sync_api`).
   `python -m venv .venv`, `.venv\Scripts\pip install playwright==1.64.0`, `.venv\Scripts\python -m playwright install chromium`:
   ```
   python -m unittest pruebas.test_actividad7_balances -v 2> docs/Actividad7/evidencias/salida_unittest.txt
   .venv\Scripts\python pruebas/evidencias_actividad7.py
   ```

Los pasos 4 y 5 ejecutan los mismos casos; el 5 además corre cada consulta en GraphiQL, guarda una captura por
operación con los nombres del equipo y arma `Evidencias Unidad II Actividad 7 - Balances.pdf` en la raíz del repositorio.

El paso 4 usa `pruebas/actividad7_datos.py` para crear cinco empresas nuevas con un sufijo aleatorio
(A: Banco/Caja/Ahorro con los movimientos del PDF; B: empresa ajena; C: sin cuentas; D y E: casos que modifican
datos). Como cada ejecución usa empresas nuevas, la tabla de referencia nunca se altera y no hay que restaurar
la base. B14 retira `transactions.read` de un rol de prueba propio y lo devuelve al terminar; los roles del sistema
no se tocan. B08 desactiva la cuenta con SQL porque no hay mutación para ello (ver `laboratorio.sql`).

La salida queda en `evidencias/resultados.json`, `evidencias/capturas/` y `evidencias/salida_unittest.txt`;
los IDs de la última corrida se escriben en `variables/` para usarlos con `operaciones.graphql` en GraphiQL
(inicia sesión con `ana.<sufijo>@empresa.test` / `secreto123`; el sufijo está en `resultados.json`).

Las evidencias B01–B15 (resultado obtenido, regla comprobada y capturas) están en
`Evidencias Unidad II Actividad 7 - Balances.pdf` (raíz del repositorio). No se publican `.env`, contraseñas reales ni tokens vigentes:
en las capturas el token aparece recortado.
