# Entregables de Unidad II, Actividad 5

## Ejecucion y datos

El proyecto usa PostgreSQL con psycopg. Para iniciar la API y la base local, copia `.env.example` a `.env`, reemplaza sus valores de ejemplo y ejecuta `docker compose up -d --build`. GraphiQL queda en `http://localhost:8004/graphql` y PostgreSQL en el puerto `POSTGRES_HOST_PORT` (por defecto 5434).

Las operaciones reproducibles estan en `operaciones.graphql`; los archivos de `variables/` contienen los IDs obtenidos en el laboratorio registrado. Los IDs cambian entre bases; para regenerarlos, consulta `comprobaciones.sql`. No publiques `.env`.

## Operaciones y variables

| Caso | Operacion | Variables |
|---|---|---|
| E01-E02 | `RolesYPermisos`, `ExplorarCatalogo`, `CatalogoCompleto` | `E01_catalogo.json` |
| E02 invalido | `CatalogoEnumInvalido.graphql` | `E01_catalogo.json` |
| E03-E05, E09 | `RevisarConfiguracion`, `AplicarConfiguracion` | `E03_S0.json`, `E03_S1.json` |
| E06 | `RevisarConfiguracion`, `AplicarConfiguracion` | `E06_*.json`; incluye preparacion/restauracion temporal |
| E08 | `AplicarConfiguracion` con lista vacia | `E08_lista_vacia.json` |
| E10 | `ConsultarCuentasE10`, `CrearCuentaE10`, `CrearConceptoE10`, `AsociarConceptoE10`, `RegistrarMovimientoE10` | `E10_*.json` |

Selecciona un solo nombre de operacion cuando uses el documento compartido de GraphQL.

## Evidencia ejecutada

E01-E10 se ejecutaron en un PostgreSQL nuevo de Docker con datos ficticios. Las respuestas GraphQL, snapshots SQL, errores controlados y salida de unittest estan en `evidencias/E01.json` a `evidencias/E10.json`; `evidencias/resumen.json` reune los resultados. No se guardaron contrasenas, JWT ni hashes. E07 paso con `python -m unittest pruebas.test_actividad5_e07 -v`.

La matriz de codigos esta en `configuracion_inicial.json` y `configuracion_final.json`. El test de rollback verifica el estado persistido con una conexion nueva. Las operaciones de E10 crean y consultan cuenta, concepto, relacion y movimiento ficticios.

Integrantes y aportaciones: pendiente de completar por el equipo.
