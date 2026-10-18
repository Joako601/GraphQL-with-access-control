# Registro de evidencias E01–E10

**Estado:** plantillas preparadas; ejecución en base/API y capturas pendientes. No se atribuyen resultados esperados como resultados observados. Guarda capturas legibles en `evidencias/` con nombres `E01.png` … `E10.png` y no incluyas credenciales, tokens ni hashes.

En cada caso completa: **precondición**, **operación y variables**, **resultado esperado**, **resultado obtenido** (copiar respuesta real), **SQL/test**, **archivo de captura**.

| Caso | Regla y verificación requerida | Estado |
|---|---|---|
| E01 | Cuatro roles, diez permisos; CAPTURISTA con S0 y cuatro relaciones activas. Respuesta de catálogos y SQL con IDs/parejas. | Pendiente de ejecutar |
| E02 | `ExplorarCatalogo`: dos alias y fragmento, diez permisos sin filtro; `PAYMENTS` debe producir error de enum. | Pendiente de ejecutar |
| E03 | Previsualizar S1 frente a S0: una alta, cero bajas, cuatro sin cambio, total cinco; comparar SQL previo y posterior sin cambio de filas. | Pendiente de ejecutar |
| E04 | Aplicar S1, repetir. Esperado: `changed=true`, después `false`; cero cambios en repetición y sin parejas duplicadas. | Pendiente de ejecutar |
| E05 | Aplicar S0, luego S1. `accounts.write` se desactiva/reactiva y conserva el mismo ID de relación. | Pendiente de ejecutar |
| E06 | Para cada variante (rol inexistente/inactivo, ADMINISTRADOR, permiso inexistente mezclado, permiso inactivo, permiso repetido), probar preview y apply; guardar error y comparación SQL antes/después. | Pendiente de ejecutar |
| E07 | Test controlado que falla después de `flush` y antes de commit; verificar persistencia desde sesión nueva. Registrar comando, prueba y salida. | Pendiente: requiere test de rollback y DB |
| E08 | Aplicar `[]` al rol permitido; comprobar cero relaciones activas antes y después de reiniciar API, conservando filas. | Pendiente de ejecutar |
| E09 | Restaurar S0 y comparar los cuatro roles por códigos con `configuracion_inicial.json`; duplicados: cero filas. | Pendiente de ejecutar |
| E10 | Ejecutar lectura existente de cuentas y registrar movimiento válido con empresa/cuenta/concepto/monto del laboratorio. | Pendiente de ejecutar |

## Captura de cada caso

- **E01:** completar respuesta y salida SQL aquí: `[pegar resultado real]`.
- **E02:** respuesta de alias/fragmento y error del enum: `[pegar resultado real]`.
- **E03:** respuesta de preview y SQL comparativo: `[pegar resultado real]`.
- **E04–E10:** agregar respuesta, salida SQL o test indicada en la tabla. Para fallos de validación, mostrar tanto el error como el estado persistido sin cambios.

No hay archivos de imagen en esta entrega porque no se ejecutó la instancia. La matriz final describe el estado que debe restaurarse para entrega, no una aseveración de que la base de laboratorio haya sido probada.
