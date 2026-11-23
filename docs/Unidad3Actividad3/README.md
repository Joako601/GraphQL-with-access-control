# Unidad III · Actividad 3

En el dashboard del Sistema General de Ingresos, abre **Administración → Roles y permisos**. La matriz lee el catálogo de PostgreSQL y muestra los permisos de los cuatro roles. Selecciona una celda, revisa **Vista previa** y pulsa **Guardar columna**. En **Usuarios**, elige un rol en la fila de la persona y pulsa **Guardar rol**.

## Ejecutar en Windows

Desde la raíz del proyecto, usa una base de laboratorio. Copia la configuración de ejemplo y sustituye las contraseñas de PostgreSQL y pgAdmin y el secreto JWT por valores locales.

```powershell
Copy-Item .env.example .env
docker compose up -d --build
python pruebas/unidad3_actividad2_datos.py
Set-Location dashboard
npm ci
npm run dev
```

El dashboard abre en http://localhost:5173 y GraphiQL en http://localhost:8004/graphql. Los usuarios siguientes se crean con la contraseña de laboratorio `secreto123`.

- **Joaquín**, `joaquin.uriona@equipo.test` (Administrador). Edita las columnas y asigna roles.
- **Ariff**, `ariff.medina@equipo.test` (Capturista). En **Cuentas**, el botón **Nueva cuenta** aparece cuando su rol recibe `accounts.write`.
- **Mateo**, `mateo.tec@equipo.test` (Contador). Ve la matriz en solo lectura.
- **Fernando**, `fernando.castro@equipo.test` (Consulta). Su membresía se puede reasignar a Capturista desde **Usuarios**.

Las lecturas de la matriz y las mutaciones usan `Authorization: Bearer`. El backend comprueba los permisos según el rol activo de la membresía. El proyecto usa PostgreSQL, como en las actividades anteriores.

## Verificar

Dentro de `dashboard/` ejecuta `npm test -- --pool=threads`, `npm run lint` y `npm run build`. Las [evidencias](evidencias.md) documentan el flujo completo. Para volver a generar las capturas en una base de laboratorio con la matriz inicial, instala Playwright y Chromium y ejecuta `python pruebas/evidencias_unidad3_actividad3.py` desde la raíz con el dashboard y el API en marcha.

[Repositorio base](https://github.com/Joako601/GraphQL-with-access-control)
