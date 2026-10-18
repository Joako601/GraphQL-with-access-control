# Investigación: permisos configurables con GraphQL

## 1. Identidad, autorización y configuración

Autenticar es comprobar quién hace la petición: en un sistema real se valida una credencial, por ejemplo una contraseña durante el inicio de sesión, y luego un token firmado. Autorizar es decidir si esa identidad puede realizar una acción concreta con un recurso. Configurar permisos es administrar la lista de acciones asociada a un rol. En el Sistema General de Ingresos, cambiar el rol CAPTURISTA para incluir `accounts.write` modifica lo que ese puesto puede hacer; no identifica a la persona que envió la mutación.

`actorCompanyUserId` es solo un valor enviado por el cliente. Cualquier cliente capaz de llamar GraphQL puede escribir el ID de otra membresía; por sí mismo no prueba que quien llama sea esa persona. Es útil para este laboratorio porque reutiliza el mecanismo de autorización existente, pero una implementación de producción debe derivar la identidad de contexto autenticado que el servidor validó y comprobar autorización en la lógica de negocio. GraphQL recomienda delegar las decisiones de autorización a esa capa [1]. Aplicado aquí, las nuevas consultas requieren `roles.read` y la mutación requiere `roles.write`, y ambas validan el actor antes de acceder a la configuración.

## 2. Variables, alias y fragmentos

Las variables mantienen separada la operación de los datos del caso, así que la misma consulta con nombre se puede ejecutar con otra membresía o lista de permisos sin editar el documento. Los alias permiten consultar campos iguales con argumentos distintos en una sola petición y reconocer cada resultado. Un fragmento reúne los campos que se desean mostrar de un permiso y evita duplicar la selección. Por ejemplo, `ExplorarCatalogo` abajo usa `$actor`, alias `cuentas`/`movimientos` y el fragmento `DatosPermiso`. Guardar juntos el documento y JSON de variables permite reproducir la petición y comparar respuestas. GraphQL documenta variables, alias y fragmentos como partes de las operaciones [2].

## 3. Validación de contrato y reglas de negocio

El esquema valida forma y tipos: un enum solo acepta los valores publicados, un input tipado rechaza campos incompatibles y `ID!` evita que el valor sea nulo. Esto no demuestra que el ID exista, que corresponda a un permiso activo, que el rol esté activo o que no se repita un ID con otra representación textual. Esas reglas dependen de los datos y deben validarse en Python contra la base antes de escribir. También son reglas del ejercicio rechazar cambios al rol ADMINISTRADOR y preservar relaciones únicas.

`[ID!]!` significa que la lista no puede ser nula y sus elementos no pueden ser nulos. No exige que tenga elementos: `[]` es una lista válida. Por eso la capa de servicio debe aceptar la lista vacía para roles distintos de ADMINISTRADOR y desactivar todas sus concesiones activas. Strawberry construye el esquema a partir de tipos Python, distingue tipos de entrada y permite modelar operaciones con inputs [3]. Aquí usamos un input para que `roleId` y `permissionIds` formen una unidad clara, pero la consulta de catálogo y la mutación todavía aplican reglas del dominio en la lógica Python.

## 4. Atomicidad e idempotencia

Atomicidad significa que la actualización se confirma completa o no deja cambios persistidos. Para `setRolePermissions`, activar las relaciones deseadas y desactivar las demás deben compartir la misma transacción. Idempotencia describe el efecto de repetir una petición: aplicar dos veces la misma lista deja el mismo estado; en la segunda respuesta `changed` debe ser falso y no deben crearse relaciones duplicadas. Una operación no se vuelve atómica por ser idempotente, ni al revés.

Enviar varias mutaciones en un documento no garantiza rollback conjunto: GraphQL ejecuta campos de mutación serialmente, pero cada resolver puede abrir/confirmar su propia transacción. Si la segunda falla, la primera podría ya estar confirmada. La solución del proyecto es una sola mutación que calcula el plan y confirma todas las escrituras en una transacción. La previsualización comparte la validación/cálculo, pero no escribe. Strawberry documenta que las mutaciones producen efectos en el servidor y cómo se definen sus argumentos y resultados [4]; la frontera transaccional sigue siendo responsabilidad de la aplicación y la base de datos.

## Fuentes consultadas

1. GraphQL, “Authorization”, https://www.graphql.org/learn/authorization/ — consulta: 17-10-2026.
2. GraphQL, “Queries”, https://graphql.org/learn/queries/ — consulta: 17-10-2026.
3. Strawberry GraphQL, “Schema basics”, https://strawberry.rocks/docs/general/schema-basics — consulta: 17-10-2026.
4. Strawberry GraphQL, “Mutations”, https://strawberry.rocks/docs/general/mutations — consulta: 17-10-2026.
