# Unidad III, Actividad 2 — Idempotencia y dashboard administrativo

Planeación: Actividad #13 · Tema 2.1 Gestión y visualización de usuarios, cuentas y conceptos · Semana del 16 al 20 de
noviembre de 2026.

## Equipo

| Integrante |
|---|
| Joaquín Uriona |
| Mateo Tec |
| Ariff Medina |
| Fernando Castro |

## Cómo se entra a la administración (resumen)

1. Levantar el backend y los datos (desde la raíz del repositorio):

   ```bash
   cp .env.example .env            # poner JWT_SECRET y contraseñas (PowerShell: Copy-Item)
   docker compose up -d --build
   python pruebas/unidad3_actividad2_datos.py     # empresa y usuarios del equipo (idempotente)
   ```

2. Levantar el cliente: `cd dashboard && cp .env.example .env && npm install && npm run dev` → <http://localhost:5173>.
3. Iniciar sesión (el mismo login de la actividad 1) y en el menú lateral elegir **Administración → Usuarios,
   Cuentas o Conceptos**. **Resumen** sigue siendo el dashboard financiero de la actividad 1. En celular el menú
   queda arriba, en una fila.

**Rol con el que probamos la escritura:** `ADMINISTRADOR` (Joaquín, escribe usuarios, cuentas y conceptos) y
`CONTADOR` (Mateo, escribe cuentas y conceptos). La lectura sin botones de alta se probó con `CONSULTA` (Fernando) y
el acceso denegado con `CAPTURISTA` (Ariff, no tiene `company.users.read`).

Contraseña de todos: `secreto123` (solo datos de laboratorio).

| Correo | Rol | Usuarios | Cuentas | Conceptos |
|---|---|---|---|---|
| `joaquin.uriona@equipo.test` | ADMINISTRADOR (principal) | lee y escribe | lee y escribe | lee y escribe |
| `mateo.tec@equipo.test` | CONTADOR | solo lee | lee y escribe | lee y escribe |
| `ariff.medina@equipo.test` | CAPTURISTA | acceso denegado | solo lee | solo lee |
| `fernando.castro@equipo.test` | CONSULTA | solo lee | solo lee | solo lee |

> El PDF habla de MySQL. Nuestro proyecto usa **PostgreSQL 16** desde el Parcial I (docker compose); la tabla, el
> índice único y la transacción son los mismos conceptos. Donde el PDF dice "MySQL", aquí es PostgreSQL.

---

## Parte 1. `createTransaction` idempotente

### Qué cambió

| Pieza | Archivo | Qué hace |
|---|---|---|
| Tabla de llaves | [`database_idempotencia.sql`](../../database_idempotencia.sql) | `idempotency_keys(company_id, operation, idempotency_key, request_hash, transaction_id)` con **índice único** `(company_id, operation, idempotency_key)`. La crea docker en un volumen nuevo (`04_…sql`) y la API al arrancar (`database/seed_roles.py`) en un volumen existente. |
| Entrada | [`models/finance_types.py`](../../models/finance_types.py) | `CreateTransactionInput.idempotencyKey: String!` (obligatoria). |
| Reglas | [`services/transaction_service.py`](../../services/transaction_service.py) | Valida la llave, calcula el SHA-256 del cuerpo normalizado y busca la llave **antes** de las reglas de negocio. |
| Transacción | [`repositories/transaction_repository.py`](../../repositories/transaction_repository.py) | `INSERT` del movimiento + `INSERT` de la llave en la **misma conexión**, un solo `COMMIT`. |

### Flujo (figura 7 del PDF, con nuestro código)

```
Cliente                 API (resolver = middleware)                         PostgreSQL
  │ createTransaction      │                                                    │
  │ idempotencyKey: X ────▶│ exigir_permiso(transactions.write)                │
  │                        │ SELECT llave X ──────────────────────────────────▶│ no está
  │                        │ reglas de negocio (concepto asignado, tipo, …)     │
  │                        │ BEGIN; INSERT transactions; INSERT idempotency_keys│
  │                        │ COMMIT ───────────────────────────────────────────▶│ movimiento 42
  │◀──── movimiento 42 ────│                                                    │
  │ REINTENTO, misma X ───▶│ SELECT llave X ──────────────────────────────────▶│ ya está → 42
  │◀── el mismo 42 ────────│ (sin otro INSERT; mismo hash ⇒ misma respuesta)    │
```

- **Misma llave, mismos datos** → se devuelve el movimiento guardado (mismo `id`), sin otro `INSERT`.
- **Misma llave, otros datos** (otro monto, cuenta, concepto, tipo, fecha o descripción) → error
  `Esta idempotencyKey ya se usó con otros datos…`; no se reutiliza ni se inserta.
- **Llave nueva** → otro movimiento, aunque el monto sea igual (dos rentas de 100 son válidas).
- **Dos envíos simultáneos** con la misma llave: los dos pasan el `SELECT`, pero el índice único rechaza la segunda
  llave; esa transacción hace `ROLLBACK` (su movimiento no queda) y se responde con el movimiento de la primera.
- **Si el `COMMIT` falla** no queda ni el gasto ni la llave; si pasa y se pierde la respuesta, el reintento encuentra
  la llave.
- La llave se busca antes de las reglas de negocio: si entre el envío y el reintento se quitó el concepto de la
  cuenta, el reintento igual devuelve el movimiento original en vez de un error.
- El permiso (`transactions.write`) sí se revisa antes: sin permiso no se lee ni se guarda la llave.
- No sustituye al rate limiting: mil llaves distintas siguen siendo mil movimientos.
- Las lecturas (`accounts`, `companyUsers`, `generalBalance`) no insertan filas: se pueden repetir.
- Como `idempotencyKey` ahora es obligatoria, los ejemplos de actividades anteriores que llaman `createTransaction`
  sin llave (`docs/Actividad5/operaciones.graphql`, `docs/Actividad7/operaciones.graphql`, `docs/Actividad6/README.md`)
  necesitan agregarla. Los scripts que siguen en uso (`pruebas/actividad6.py`, `actividad7.py`, `actividad7_datos.py`)
  y `consultas.graphql` ya la envían.
- No usamos Redis: la memoria de la llave y el dinero se confirman juntos en la misma base.

### Comprobación (sección 6 del PDF)

| # | Caso | Resultado |
|---|---|---|
| 1 | GraphiQL: `createTransaction` dos veces con la misma `idempotencyKey` | mismo `id` — [19](evidencias/19-graphiql-idempotencia-envio-1.png), [20](evidencias/20-graphiql-idempotencia-envio-2-misma-llave.png) |
| 2 | La misma mutación con otra llave | otro `id` — [21](evidencias/21-graphiql-otra-llave-otro-movimiento.png) |
| 3 | En la base hay una sola fila para la primera llave | [`sql_idempotencia.txt`](evidencias/sql_idempotencia.txt) |
| + | Misma llave con otro monto, 5 envíos simultáneos, lectura repetida | [`salida_idempotencia.txt`](evidencias/salida_idempotencia.txt) |

```bash
python pruebas/unidad3_actividad2_idempotencia.py          # contra la API real (6 casos)
python -m unittest pruebas.test_unidad3_idempotencia -v    # reglas con mocks, incluida la carrera
```

Ejemplo para GraphiQL (`http://localhost:8004/graphql`, encabezado `Authorization: Bearer <token de Ariff>`):

```graphql
mutation RegistrarEgreso($input: CreateTransactionInput!) {
  createTransaction(input: $input) { id amount transactionType account { name } concept { name } }
}
```

```json
{ "input": { "idempotencyKey": "renta-nov-001", "accountId": "1", "conceptId": "3",
             "transactionType": "EXPENSE", "amount": "100.00", "shortDescription": "Renta de noviembre" } }
```

---

## Parte 2. Dashboard administrativo

### De qué consulta sale cada tabla

Cada tabla es una query, cada botón Guardar una mutation, con `Authorization: Bearer`. Después de una mutación
correcta la tabla **se vuelve a consultar**; no se agregan filas a mano. Las consultas están en
[`dashboard/src/lib/admin.ts`](../../dashboard/src/lib/admin.ts).

| Pantalla | Lectura | Altas / bajas | Permiso de lectura · escritura |
|---|---|---|---|
| Encabezado y botones | `me { companyId company { name } role { name } permissions }` | — | token válido |
| Usuarios | `companyUsers(companyId) { isAdmin isActive joinedAt user { name email } role { name } }` | `createCompanyUser`, `deactivateCompanyUser` | `company.users.read` · `company.users.write` |
| Cuentas | `accounts(companyId) { name accountType bankName maskedClabe cardLastDigits isActive }` | `createAccount` | `accounts.read` · `accounts.write` |
| Conceptos · catálogo | `concepts(companyId) { name conceptType shortDescription isActive }` | `createConcept` | `concepts.read` · `concepts.write` |
| Conceptos · de una cuenta | `accounts` (selector) + `accountConcepts(accountId, activeOnly: true) { concept { name conceptType } }` | `assignConceptToAccount`, `removeConceptFromAccount` | `concepts.read` · `concepts.write` |

Columnas ↔ campos: Nombre `user.name`, Correo `user.email`, Rol `role.name` (de la membresía, Parcial II; "Sin rol"
si no tiene), Administrador `isAdmin`, Estado `isActive`, Ingreso `joinedAt`; Tipo de cuenta con la etiqueta del
catálogo (CASH → Efectivo, DEBIT → Débito, CREDIT → Crédito, SAVINGS → Ahorro, INVESTMENT → Inversión,
WALLET → Monedero, OTHER → Otro); Referencia `maskedClabe` (`****1234`) o `****` + `cardLastDigits`; Tipo de concepto
INCOME → Ingreso, EXPENSE → Egreso.

### Lo que agregamos al backend (y por qué)

- **`me`** ([`schema/schema.py`](../../schema/schema.py), `services/user_service.sesion_actual`): devuelve la
  membresía del token, su empresa, su rol y los códigos de permiso. Sin ella el cliente no podía saber qué botones
  dibujar (un CAPTURISTA no puede leer `companyUsers` para buscar su propio rol). No pide permisos: solo describe la
  propia sesión. El cliente ya no lee la empresa del JWT para esta sección.
- **`Account.maskedClabe`** ([`models/finance_types.py`](../../models/finance_types.py)): `****` + últimos 4 dígitos.
  La tabla nunca pide los 18 dígitos. El enmascarado es de presentación: el campo `clabe` completo sigue existiendo en
  el esquema del Parcial I para quien tenga `accounts.read` (no lo quitamos para no romper consultas anteriores).
- **`deactivateCompanyUser`** ahora rechaza una membresía que ya está inactiva.
- No se agregaron tablas para la parte 2: todo lo demás ya existía desde los parciales I y II.

### Reglas de la pantalla

- **Una pregunta por pantalla:** Usuarios "¿Quién pertenece a la empresa?", Cuentas "¿Dónde está el dinero?",
  Conceptos "¿Por qué se mueve el dinero y en qué cuenta se permite?".
- **La acción principal se ve:** *Nuevo usuario*, *Nueva cuenta*, *Nuevo concepto* y *Asignar concepto* son botones
  visibles, no un menú de tres puntos. Sin el permiso `*.write` **no se dibujan** (y el API los rechazaría igual).
- **Conteos de Usuarios** (activos, administrador principal, inactivos) salen de la misma lista de `companyUsers`,
  sin otra consulta y sin etiqueta MXN. Si hubiera más de un administrador se marca en ámbar, no se oculta.
- **Búsqueda y filtros** (nombre/correo, Todos/Activos/Inactivos, tipo de cuenta, Ingreso/Egreso, solo activos) son
  filtros de la lista ya cargada.
- **Estado vacío:** "La empresa no tiene cuentas registradas", "La cuenta X todavía no tiene conceptos asignados", etc.
- **Activo e inactivo** se distinguen con texto y color.
- **Errores del API en la pantalla:** correo duplicado y concepto ya asignado aparecen en el formulario; un rol sin
  lectura ve "Acceso denegado" con el mensaje del servidor. El selector de *Concepto a asignar* lista también los ya
  asignados (marcados "ya asignado") para que el duplicado lo rechace el servidor, no el navegador.
- **Baja lógica:** *Desactivar* explica que la persona deja de operar y que la fila y su historial se conservan; pone
  `isActive = false`, no borra filas. *Quitar* desactiva la relación cuenta–concepto; el concepto sigue en el
  catálogo y los movimientos anteriores no cambian.
- **Contraseña:** solo existe en el formulario de alta (`type="password"`) y viaja en la mutación; ninguna consulta
  la pide, la respuesta no la devuelve y el formulario se limpia al guardar.
- **Sesión:** el encabezado muestra la empresa y *Cerrar sesión* (borra el token y vuelve al login). Si el token falta,
  venció o la membresía se desactivó, cualquier consulta regresa al login; no queda una tabla a medias.
- El alta de usuario **no pide `isAdmin`**: entra con rol Consulta. El administrador principal nace con
  `createCompanyAdmin` (Parcial I) y un segundo administrador lo rechaza el servidor (`La empresa ya tiene un
  administrador principal`, índice único `one_admin_per_company`).

### Boceto

Cambió respecto a las figuras 10 y 11: el formulario de alta se abre **a todo el ancho, encima de la tabla**, en vez
de una columna a la derecha. Con la columna lateral la tabla de Usuarios (7 columnas) quedaba recortada a 1440 px.
En Conceptos se conserva la figura 12 (catálogo a la izquierda, cuenta a la derecha). Debajo de 768 px las tablas de
Usuarios y Cuentas se muestran como tarjetas.

```
┌ Menú ─────────┐┌ Dashboard administrativo · <Empresa> ·  Rol ──────── [Cerrar sesión] ┐
│ FINANCIERO    ││ Usuarios                                          [Nuevo usuario]  │
│  Resumen      ││ ¿Quién pertenece a la empresa?                                    │
│ ADMINISTRACIÓN││ [Activos 4] [Administrador principal 1] [Inactivos 1]             │
│ ▸ Usuarios    ││ ┌ Nuevo usuario (al pulsar el botón) ─────────────────────────┐   │
│   Cuentas     ││ │ Nombre      Correo      Contraseña          [Guardar]       │   │
│   Conceptos   ││ └─────────────────────────────────────────────────────────────┘   │
│               ││ [Buscar…]                         [Todos][Activos][Inactivos]     │
│               ││ Nombre │ Correo │ Rol │ Administrador │ Estado │ Ingreso │ Acción │
│               ││ Los datos salen de companyUsers                                   │
└───────────────┘└───────────────────────────────────────────────────────────────────┘
```

### Evidencias (datos del equipo, PostgreSQL de docker compose)

Generadas con `python pruebas/evidencias_unidad3_actividad2.py` (Playwright sobre el dashboard real y GraphiQL).

| # | Captura | Comprobación del PDF |
|---|---|---|
| 01 | [Usuarios](evidencias/01-usuarios.png) | 1–2: entrar a la administración; la tabla coincide con `companyUsers` |
| 02 | [Usuario creado](evidencias/02-usuario-creado.png) | 3: alta de usuario, aparece en la tabla |
| 03 | [Error: correo duplicado](evidencias/03-error-correo-duplicado.png) | 3: el correo duplicado se rechaza en pantalla |
| 04 | [Confirmar desactivación](evidencias/04-desactivar-confirmacion.png) | 4: texto de baja lógica |
| 05 | [Usuario inactivo](evidencias/05-usuario-inactivo.png) | 4: la fila sigue, con estado inactivo |
| 06 | [Cuentas](evidencias/06-cuentas.png) | tabla de cuentas, CLABE enmascarada |
| 07 | [Cuenta creada](evidencias/07-cuenta-creada.png) | 5: alta de cuenta |
| 08 | [Conceptos](evidencias/08-conceptos.png) | catálogo + conceptos de la cuenta Banco |
| 09 | [Concepto asignado](evidencias/09-concepto-asignado.png) | 6: concepto de egreso asignado a la cuenta nueva |
| 10 | [Error: concepto ya asignado](evidencias/10-error-concepto-ya-asignado.png) | 6: asignarlo otra vez muestra el duplicado |
| 11 | [Concepto quitado](evidencias/11-concepto-quitado-sigue-en-catalogo.png) | 7: sigue en el catálogo, ya no en la cuenta |
| 12–14 | [Usuarios](evidencias/12-consulta-usuarios-sin-botones.png), [Cuentas](evidencias/13-consulta-cuentas-sin-botones.png), [Conceptos](evidencias/14-consulta-conceptos-sin-botones.png) como CONSULTA | 8: ve las tablas, no ve botones de alta |
| 15 | [CAPTURISTA en Usuarios](evidencias/15-capturista-usuarios-acceso-denegado.png) | sin `company.users.read`: acceso denegado |
| 16 | [Menú en el dashboard financiero](evidencias/16-menu-dashboard-financiero.png) | el menú distingue financiero y administrativo |
| 17 | [Cerrar sesión](evidencias/17-cerrar-sesion-vuelve-al-login.png) | cerrar sesión vuelve al login |
| 18 | [Celular (390 px)](evidencias/18-responsive-usuarios.png) | menú arriba, filas como tarjetas |
| 19–21 | GraphiQL | idempotencia (parte 1) |

Para revisar en la base que el alta y la baja persisten:

```bash
docker compose exec postgres psql -U postgres -d sistema_financiero -c \
  "SELECT u.name, u.email, cu.is_admin, cu.is_active FROM company_users cu JOIN users u ON u.id = cu.user_id WHERE cu.company_id = 1;"
```

### Pruebas

```bash
python -m unittest pruebas.test_unidad3_idempotencia pruebas.test_actividad7_balances pruebas.test_unidad3_cors -v
python pruebas/unidad3_actividad2_idempotencia.py
cd dashboard && npm test && npm run lint && npm run build
```

### Criterios

| Criterio | Dónde se ve |
|---|---|
| `createTransaction` con la misma llave no inserta un segundo movimiento; otra llave sí | capturas 19–21, `sql_idempotencia.txt` |
| La llave y el movimiento se confirman en la misma transacción | `transaction_repository.crear_movimiento` (un `with get_connection()`) |
| El menú distingue el dashboard financiero del administrativo; cerrar sesión funciona | capturas 16–17 |
| Usuarios, cuentas y conceptos se leen del API de la empresa de la sesión | `me.companyId` → `companyUsers`/`accounts`/`concepts` |
| Alta de usuario, cuenta, concepto y asignación persisten | capturas 02, 07, 09 + consulta SQL |
| La baja es lógica: la fila queda inactiva | capturas 05 y 11 |
| Quien no tiene el permiso de escritura no ve la acción de alta | capturas 12–14 |
| La contraseña no aparece en ninguna tabla | capturas 01–05 |
| Los campos de la pantalla corresponden al esquema | tabla "De qué consulta sale cada tabla" |
