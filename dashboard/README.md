# dashboard — cliente del dashboard financiero

Vite + React + TypeScript + shadcn/ui. Inicia sesión con la mutación `login`, guarda token y usuario en
`sessionStorage` y muestra `generalBalance` con `Authorization: Bearer`. No calcula importes: solo les da formato.

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
  App.tsx                 sesión: login ↔ dashboard, cierre por token inválido
  components/login/       pantalla y formulario de inicio de sesión
  components/dashboard/   encabezado, período, tarjetas, riesgo, tabla, estados
  components/ui/          componentes shadcn/ui
  hooks/useDashboardData  nombre de la empresa y generalBalance
  lib/                    cliente GraphQL y errores, formato, período, sesión
```

Puertos, usuarios de prueba y período de demo: [docs/Unidad3Actividad1/README.md](../docs/Unidad3Actividad1/README.md).
