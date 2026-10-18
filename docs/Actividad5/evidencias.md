# Registro de evidencias E01-E10

**Estado: ejecutadas en laboratorio local PostgreSQL/Docker.** Cada archivo JSON conserva las respuestas GraphQL y/o SQL observadas, sin credenciales, tokens ni hashes. `resumen.json` consolida los diez casos. Los IDs pertenecen solo a esta base local.

| Caso | Resultado observado | Evidencia |
|---|---|---|
| E01 | Cuatro roles, diez permisos; CAPTURISTA tiene S0 y cuatro relaciones activas. IDs reales de Ana, roles, permisos y relaciones incluidos. | [E01.json](evidencias/E01.json) |
| E02 | Dos permisos en cada alias, diez sin filtro; `PAYMENTS` devuelve error de validacion del enum. | [E02.json](evidencias/E02.json) |
| E03 | S1: una activacion, cero bajas, cuatro sin cambio, total cinco. Snapshots SQL anterior/posterior iguales. | [E03.json](evidencias/E03.json) |
| E04 | Primera aplicacion `changed=true`; repeticion `changed=false`; IDs de parejas estables y cero duplicados. | [E04.json](evidencias/E04.json) |
| E05 | `accounts.write` se desactiva y reactiva conservando la relacion ID 31; permiso del catalogo sigue activo. | [E05.json](evidencias/E05.json) |
| E06 | Siete variantes invalidas rechazadas tanto en preview como en apply; snapshots de relaciones iguales. Incluye IDs duplicados como texto y numero. | [E06.json](evidencias/E06.json) |
| E07 | Test controlado falla despues de la primera escritura y antes del commit; unittest verifica rollback desde una conexion nueva. Resultado: OK. | [E07.json](evidencias/E07.json) |
| E08 | `[]` deja cero relaciones activas antes y despues de reiniciar la API; las filas se conservan y el catalogo sigue en 4 roles/10 permisos. | [E08.json](evidencias/E08.json) |
| E09 | Se restaura S0; la matriz de los cuatro roles coincide con la inicial y no hay parejas duplicadas. | [E09.json](evidencias/E09.json) |
| E10 | Lectura inicial de cuentas, alta de cuenta/concepto, asociacion y registro de movimiento INCOME por 1500.00; lectura posterior muestra la cuenta. | [E10.json](evidencias/E10.json) |

Las consultas/mutaciones estan en `operaciones.graphql`; las variables utilizadas estan en `variables/`. E06 incluye las preparaciones temporales de estado inactivo, restauradas tras cada variante. No se incluyen capturas del escritorio; las evidencias son respuestas JSON y comprobaciones SQL reproducibles.
