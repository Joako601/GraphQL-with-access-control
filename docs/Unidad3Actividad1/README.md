# Unidad III, Actividad 1 — Dashboard financiero

Cliente web que inicia sesión con la mutación `login` del backend del equipo y muestra los indicadores de
`generalBalance` con `Authorization: Bearer <token>`. El backend sigue siendo la única fuente de cálculo: el
dashboard no suma ni resta importes, solo les da formato.

## Integrantes

Tomados del historial del repositorio (el equipo debe confirmar la lista y el rol de cada quien antes de entregar):

| Integrante | GitHub | Rol en esta actividad |
|---|---|---|
| Joaquín Uriona | @Joako601 | _por confirmar_ |
| Mateo Martin | @mateomartin21 | _por confirmar_ |
| Fernando Castro Hernández | @Fernando-Castro-Hernandez | _por confirmar_ |
| Ariff Medina | @ariff-adivor | _por confirmar_ |

## Opción de cliente elegida y por qué

**Vite + React + TypeScript** (opción 2 del PDF), con Tailwind v4 y componentes shadcn/ui, en la carpeta `dashboard/`.

- Los estados de la pantalla (cargando, datos, acceso denegado, error, sin movimientos) se modelan como tipos y
  TypeScript obliga a cubrirlos todos; con HTML + `fetch` habría que hacerlo a mano.
- La lógica sensible (formato de importes sin `float`, validación de fechas, clasificación de errores, lectura del
  token) está en funciones puras con pruebas Vitest.
- GraphiQL (`http://localhost:8004/graphql`) sigue siendo la herramienta de prueba; el dashboard es la vista de negocio.

## Arquitectura

```
Navegador (localhost:5173)                     Docker
┌──────────────────────────┐   POST /graphql   ┌───────────────────────────┐    ┌──────────────┐
│ dashboard/ (Vite+React)  │ ────────────────▶ │ API FastAPI + Strawberry  │──▶ │ PostgreSQL 16│
│  login → sessionStorage  │  Bearer <token>   │ 127.0.0.1:8004 → :8000    │    │ :5434 → :5432│
│  generalBalance, company │ ◀──────────────── │ CORS: CORS_ORIGINS        │    └──────────────┘
└──────────────────────────┘    JSON           └───────────────────────────┘
```

1. `login(input: {email, password}) { token tokenType user { id name email } }` → se guardan token y usuario en
   `sessionStorage` (se borran al cerrar la pestaña; nunca en el código ni en el repositorio).
2. `generalBalance(fromDate, toDate)` con `Authorization: Bearer`. El dashboard **no** envía `companyId` ni
   `actorCompanyUserId`: la empresa sale del token en el backend (`services/balance_service.py`).
3. Nombre de la empresa: el esquema no tiene consulta `me`. El dashboard lee `companyId` del payload del JWT (lo firmó
   el backend en `services/auth.py`) y llama a la consulta pública `company(id)` solo para mostrar `name` en el
   encabezado. La firma se verifica en el backend en cada `generalBalance`.
4. Errores: el backend responde HTTP 200 con `errors[0].message` y sin `extensions.code`. El cliente clasifica el
   mensaje (`dashboard/src/lib/graphql.ts`):

| Mensaje del backend | Estado en el dashboard |
|---|---|
| `Falta el token…`, `El token no es válido o ya venció`, `La membresía no existe…`, `El usuario está inactivo` | Vuelve al login: "Tu sesión expiró o el token no es válido" |
| `Permiso denegado: el rol … no tiene el permiso accounts.read` (o `transactions.read`) | "Acceso denegado", sin números |
| `fromDate no puede ser posterior a toDate`, variable `Date` inválida | Alerta "No se pudo consultar el período" |
| `Correo o contraseña incorrectos` (en `login`) | Mensaje en el formulario |

Además, el dashboard valida `fromDate <= toDate` antes de llamar al API.

### Cambios en el backend

- `main.py`: `CORSMiddleware` con los orígenes de `CORS_ORIGINS` (por defecto `http://localhost:5173`); solo
  `GET`/`POST` y los encabezados `Authorization` y `Content-Type`.
- `docker-compose.yml` y `.env.example`: variable `CORS_ORIGINS` (compose usa `http://localhost:5173,http://127.0.0.1:5173` si `.env` no la define).
- `.dockerignore`: excluye `dashboard/` de la imagen del API.
- `pruebas/unidad3_actividad1_datos.py`: datos de demo con correos fijos (idempotente) y comprobación contra la
  tabla calculada a mano.
- `pruebas/test_unidad3_cors.py`: pruebas del CORS.

No se agregaron tablas, columnas ni consultas: `login`, `generalBalance` y `company` ya existían.

## Cómo levantar el proyecto

Requisitos: Docker Desktop, Node 20+ (probado con Node 24) y Python 3.11+ (solo para el script de datos).

### 1. `.env` del backend

PowerShell:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # pega el resultado en JWT_SECRET
```

Git Bash:

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # pega el resultado en JWT_SECRET
```

Cambia también `POSTGRES_PASSWORD` y `PGADMIN_PASSWORD`. `CORS_ORIGINS` ya trae el origen del dashboard.

### 2. PostgreSQL + API (Docker)

Igual en PowerShell y Git Bash, desde la raíz del repositorio:

```
docker compose up -d --build
docker compose ps
```

- API / GraphiQL: `http://localhost:8004/graphql` (`APP_PORT`)
- PostgreSQL: `localhost:5434` (`POSTGRES_HOST_PORT`) · pgAdmin: `http://localhost:5054`

### 3. Datos de demostración

```
python pruebas/unidad3_actividad1_datos.py
```

Crea "Empresa Demo Dashboard" una sola vez (si ya existe no hace nada) y compara el `generalBalance` real con la
tabla calculada a mano. Salida esperada: `coincide con la tabla a mano` y `SinLectura -> Permiso denegado…`.

### 4. Dashboard

PowerShell:

```powershell
cd dashboard
Copy-Item .env.example .env      # VITE_API_URL=http://localhost:8004/graphql
npm install
npm run dev                      # http://localhost:5173
```

Git Bash:

```bash
cd dashboard
cp .env.example .env
npm install
npm run dev
```

Sin `.env`, el dashboard usa `http://localhost:8004/graphql`. Si cambias `APP_PORT`, cambia `VITE_API_URL`.

### Pruebas

```
python -m unittest pruebas.test_actividad7_balances pruebas.test_unidad3_cors -v   # requiere requirements.txt + httpx
cd dashboard && npm test && npm run lint && npm run build
```

## Usuarios de prueba

Contraseña de todos: `secreto123` (solo datos de laboratorio).

| Correo | Rol | Qué ve |
|---|---|---|
| `ana.demo@empresa.test` | ADMINISTRADOR | Dashboard completo |
| `pedro.demo@empresa.test` | CONSULTA | Dashboard completo (solo lectura) |
| `sinlectura.demo@empresa.test` | DEMO_SIN_LECTURA (solo `concepts.read`) | "Acceso denegado" |

## Período de demostración y valores esperados

Período por defecto: **2026-10-26 a 2026-10-30** (el mismo de la Actividad 7). Movimientos (12:00 UTC):
Banco +1,000.00 el 25 (apertura), +3,000.00 el 26, −1,200.00 el 27, −1,000.00 el 28; Caja +500.00 el 26, −700.00 el 29;
Ahorro sin movimientos.

Los totales coinciden con la sección 3.7 del PDF. El desglose por cuenta es distinto al de la figura 2 del PDF
porque se usan los datos de la Actividad 7; esta es la tabla equivalente calculada a mano:

| Cuenta | Saldo inicial | Ingresos | Egresos | Profit | Saldo final | En rojo |
|---|---:|---:|---:|---:|---:|---|
| Banco | 1,000.00 | 3,000.00 | 2,200.00 | 800.00 | 1,800.00 | No |
| Caja | 0.00 | 500.00 | 700.00 | −200.00 | −200.00 | **Sí** |
| Ahorro | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | No |
| **General** | **1,000.00** | **3,500.00** | **2,900.00** | **600.00** | **1,600.00** | **No** · `accountsInRed = 1` |

Cambio de fechas para la demo: **2026-10-28 a 2026-10-28** → saldo inicial 3,300.00, ingresos 0.00, egresos
1,000.00, profit −1,000.00, saldo final 2,300.00, cuentas en rojo 0 (Caja aún tiene 500.00 ese día).

## Indicador ↔ campo GraphQL

| Pantalla | Campo |
|---|---|
| Encabezado: empresa / moneda / período | `company(id).name` / `generalBalance.currency` / `fromDate`, `toDate` |
| Saldo inicial | `openingBalance` |
| Ingresos | `totalIncome` |
| Egresos | `totalExpense` |
| Profit | `profit` |
| Saldo final | `closingBalance` |
| ¿General en rojo? | `isInRed` |
| Cuentas en rojo (número) | `accountsInRed` |
| Detalle por cuenta | `accounts { accountName isActive openingBalance totalIncome totalExpense profit closingBalance isInRed }` |

Los importes llegan como texto (`"1600.00"`) y se formatean sin convertirlos a número (`dashboard/src/lib/format.ts`).

## Entregables

- Boceto: [`wireframe.svg`](wireframe.svg) / [`wireframe.png`](wireframe.png)
- Evidencias: [`evidencias.md`](evidencias.md)
- Guion de la demo: [`guion-demo.md`](guion-demo.md)
- Código del cliente: [`../../dashboard/`](../../dashboard/)
