# Entregables de Unidad II, Actividad 5

Esta carpeta contiene la investigación, matrices derivadas del seed, operaciones GraphQL, variables de ejemplo, SQL de inspección y la bitácora de evidencias.

## Ejecutar el proyecto

Desde la raíz `GraphQL-with-access-control`:

1. Copia `.env.example` a `.env` y cambia las claves locales de ejemplo. No publiques `.env`.
2. Ejecuta `docker compose up -d --build`. El servicio GraphQL queda en `http://localhost:8004/graphql`; PostgreSQL escucha en el host en el puerto indicado por `POSTGRES_HOST_PORT` (por defecto 5434).
3. Usa GraphiQL o un cliente GraphQL y selecciona el nombre de operación deseado en `operaciones.graphql`. Completa los marcadores de `variables/*.json` con IDs consultados en ese entorno mediante las consultas finales de `comprobaciones.sql` o la consulta GraphQL `roles`/`permissions`. Los IDs no son portables entre bases.
4. Ejecuta las comprobaciones SQL con `psql` contra la base local, por ejemplo `psql -h localhost -p 5434 -U postgres -d sistema_financiero -f docs/Actividad5/comprobaciones.sql` (ajusta host, puerto, usuario y base a tu `.env`).

El repositorio usa PostgreSQL/psycopg; las instrucciones generales de la actividad mencionan MySQL, pero las consultas de esta entrega están adaptadas al esquema real. El seed de `database/seed_roles.py` define cuatro roles y diez permisos. `configuracion_inicial.json` y `configuracion_final.json` representan el estado esperado por códigos, no constituyen una captura del estado de una instancia.

## Operaciones y variables

| Operación | Variables |
|---|---|
| `ExplorarCatalogo` / `CatalogoCompleto` | `variables/E01_catalogo.json` |
| `RevisarConfiguracion` proponiendo S1 | `variables/E03_S1.json` |
| `RevisarConfiguracion` / `AplicarConfiguracion` proponiendo S0 | `variables/E03_S0.json` |

Para aplicar S1, reutiliza el JSON S1 con `AplicarConfiguracion`; para la repetición exacta vuelve a enviar la misma operación y variables. Los valores `REEMPLAZAR_...` y `ID_...` son marcadores deliberados: deben sustituirse con los IDs devueltos por esa base. Usa Ana como actor de laboratorio y comprueba que tenga `roles.read`/`roles.write` según la operación.

## Límites de la evidencia disponible

No se generaron IDs de laboratorio, salidas SQL, respuestas de API ni capturas sin ejecutar una instancia de base de datos y completar los datos de laboratorio. `evidencias.md` conserva por ello plantillas honestas para E01–E10. Completa “resultado obtenido” y adjunta capturas después de ejecutar; no presentes los resultados esperados como observados. La actividad requiere además una prueba E07 de rollback y continuidad E10 con datos válidos; la bitácora señala esos resultados como pendientes de ejecución.

Integrantes y aportaciones: **pendiente de completar por el equipo**.
