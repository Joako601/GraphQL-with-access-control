# dashboard — cliente del Sistema General de Ingresos

Vite + React + TypeScript + shadcn/ui. Inicia sesión con la mutación `login`, guarda token y usuario en
`sessionStorage` y tiene dos secciones en el mismo menú:

- **Dashboard financiero** (`#/financiero`, Unidad III · Actividad 1): `generalBalance` con `Authorization: Bearer`.
  No calcula importes: solo les da formato.
- **Dashboard administrativo** (`#/admin/usuarios`, `#/admin/cuentas`, `#/admin/conceptos`, Unidad III ·
  Actividad 2): membresías, cuentas y conceptos de la empresa de la sesión (`me`, `companyUsers`, `accounts`,
  `concepts`, `accountConcepts` y sus mutaciones).

```bash
cp .env.example .env   # VITE_API_URL=http://localhost:8004/graphql (PowerShell: Copy-Item)
npm install
npm run dev            # http://localhost:5173 (requiere el API de docker compose)
npm test               # Vitest
npm run lint           # oxlint
npm run build          # tsc + build en dist/
```

```
src/
  App.tsx                 sesión: login ↔ aplicación, menú (AppShell), cierre por token inválido
  components/login/       pantalla y formulario de inicio de sesión
  components/dashboard/   financiero: encabezado, período, tarjetas, riesgo, tabla; Sidebar con el menú
  components/admin/       administrativo: AdminPage (me), UsersModule, AccountsModule, ConceptsModule, parts
  components/ui/          componentes shadcn/ui
  hooks/                  useDashboardData (financiero), useApiQuery/useMutation (admin), useHashRoute
  lib/                    cliente GraphQL y errores, formato, período, sesión, admin (consultas), catalog, route
```

Puertos, usuarios de prueba y período de demo: [docs/Unidad3Actividad1/README.md](../docs/Unidad3Actividad1/README.md).
Administración, idempotencia y usuarios del equipo: [docs/Unidad3Actividad2/README.md](../docs/Unidad3Actividad2/README.md).
