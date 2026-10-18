Tecnológico de Software · TSU en Desarrollo e Innovación de Software

# Unidad II · Actividad 5

### Configurar permisos con GraphQL

Fundamentos de Arquitectura de Software y Desarrollo Backend

### Tema 1. Gestión de roles y permisos · Subtema 1.3. Gestión de permisos por roles

Complemento de la **Actividad #8 de la planeación: Configuración de permisos para diferentes roles del** **sistema**.

El Sistema General de Ingresos ya tiene usuarios, empresas, cuentas, conceptos, movimientos y una matriz de permisos. En la actividad 4 agregaste y quitaste permisos de uno en uno. Ahora construirás una forma de revisar una configuración completa antes de guardarla y de aplicarla sin dejar cambios a medias.

Primero revisaremos cómo se diseñan los roles, qué relación tienen con la seguridad y en qué se distinguen autenticación y autorización. Después usarás nuevas herramientas de GraphQL para trabajar con el mismo proyecto en Python, Strawberry, SQLAlchemy y MySQL.

**Límite de esta actividad.** La programación se concentra en los catálogos y en la relación rol-permiso. La autenticación se aborda como fundamento conceptual. El tema 2, Control de acceso de usuarios, corresponde al 19 al 23 de octubre: en esta entrega no se implementan nuevas asignaciones de roles a usuarios, protección de rutas, middleware de autenticación ni validación de tokens. Se conserva lo que ya funciona del proyecto.

### Buenas prácticas de autenticación y autorización

Estas prácticas reducen el daño si alguien prueba contraseñas ajenas, envía un id que no le corresponde o deja un rol con más permisos de los acordados.

|Práctica|Qué ataque reduce|
|---|---|
|Guardar la contraseña solo como hash y no devolverla en GraphQL. El hash permite comprobar lo que la persona escribió sin conservar el texto.|Si copian la base, no se llevan las contraseñas en claro para entrar a este sistema o a otros donde se repita la misma clave.|
|No tratar como identidad el id que escribe el cliente. actorCompanyUserId sirve en el laboratorio. En producción, la identidad sale de un token que el servidor valida en cada petición.|Alguien abre GraphiQL, pone el id de Ana y cambia la lista de roles como si fuera ella.|
|Decidir el permiso en el servidor, dentro de cada operación, antes de guardar. Ocultar un botón en la pantalla no sustituye esa revisión.|Llaman setRolePermissions directo, aunque la pantalla no les muestre esa acción.|
|Incluir en el rol solo las acciones del puesto. Lo que no está en la lista activa no está concedido, aunque el permiso exista en el catálogo.|Un capturista modifica la configuración, o una consulta escribe movimientos, porque el permiso existía y nadie lo negó de forma explícita.|
|Comprobar que la cuenta, el concepto y la membresía pertenecen a la misma empresa antes de leer o de guardar.|Usan un id que sí existe, pero es de la empresa de al lado, y ven o modifican sus cuentas.|
|Confirmar el cambio de toda la lista en un solo commit. Si algo falla antes, revertir y dejar la configuración anterior.|Un error a la mitad deja el rol con algunos permisos nuevos y otros viejos, distinto de lo que se decidió.|
|No poner contraseñas, hashes completos ni tokens en capturas, repositorios, mensajes de error ni registros.|Esos datos quedan en un ZIP, en GitHub o en un log, y sirven para entrar después.|
|Limitar los intentos de login y dar al token una vigencia corta, enviado por un canal cifrado. 1. Un rol se diseña a partir del trabajo En las actividades 3 y 4 el rol ya agrupa permisos, y la persona recibe un rol dentro de la empresa. El paso nuevo es armar esa lista a partir del trabajo. 1. Describe qué hace el puesto. 2. Anota los recursos que toca: usuarios, cuentas, conceptos, movimientos o roles.|Prueban muchas contraseñas seguidas, o reutilizan un token copiado de una petición anterior.|

Fundamentos de Arquitectura de Software y Desarrollo Backend 1 / 15

Unidad II · Actividad 5 · Configurar permisos con GraphQL

3. Separa lectura y escritura. accounts.read y accounts.write siguen siendo dos permisos.
4. Registra un código estable, un nombre y una descripción. El capturista consulta cuentas y conceptos para registrar movimientos. Su lista inicial es accounts.read, concepts.read, transactions.read y transactions.write. No necesita roles.write para capturar un ingreso. El código nombra el puesto, no a la persona. CAPTURISTA se comparte. MARIA_ESPECIAL mezcla a María con el puesto. El catálogo sigue siendo el de la actividad 4: cambiar la lista de CAPTURISTA cambia a María y a José. En esta actividad no se crea una lista distinta por empresa.
## Seguridad al configurar

**Mínimo privilegio:** la lista incluye solo las acciones de ese trabajo. Leer una cuenta no incluye crearla.

**Denegación por defecto:** lo que no está en la lista activa no está concedido. La tabla guarda concesiones. Una relación inactiva retira una concesión. No hay una segunda lista de prohibiciones.

Si un fallo deja guardada solo la mitad de la lista, el rol ya no es el que se decidió. La actualización de esta actividad se confirma entera o no se confirma.

### 2. Autenticación y autorización responden preguntas distintas

Son tres preguntas distintas. Esta actividad programa la configuración. La autorización se reutiliza con exigir_permiso. La autenticación no se vuelve a implementar.

**Autenticar** es comprobar quién es. En login se revisa la contraseña. Un token solo acredita a esa persona si el servidor lo validó. Escribir un identificador no hace esa comprobación.

**Configurar permisos** es decidir qué acciones tiene un rol. Agregar accounts.write a CAPTURISTA cambia la lista del puesto. No dice quién está llamando en esta petición.

**Autorizar** es decidir si esta petición puede hacer esta acción. El servidor mira el rol de quien llama y busca el permiso. Haber iniciado sesión no concede todas las acciones. GraphQL describe la operación; la decisión vive en Python. Referencia: autorización en GraphQL ([https://graphql.org/learn/authorization/](https://graphql.org/learn/authorization/)).

Fundamentos de Arquitectura de Software y Desarrollo Backend 2 / 15

*Figura 1. Esta semana trabajamos en la configuración del rol. La conexión completa entre identidad autenticada y control de*

*acceso se desarrollará en el tema 2.*

|Concepto|Qué debes comprender ahora|Relación con el proyecto|
|---|---|---|
|Contraseña|Es una credencial secreta|No se entrega en capturas ni se guarda como texto legible|
|Hash de contraseña|Permite verificar una contraseña sin almacenar su texto original|Se conserva el mecanismo de login; el hash no se expone como campo público|
|Token o sesión|Puede acreditar una identidad cuando el servidor lo valida|Su sola presencia no demuestra que haya sido validado|
|Identificador|Señala un registro|Escribir el ID de Ana no demuestra que quien lo envía sea Ana|
|Matriz de permisos|Define las acciones de cada rol|Es el objeto de esta actividad|

Un hash convierte la contraseña en un valor fijo. Tres propiedades importan aquí. Es de un solo sentido: del valor guardado no se vuelve al texto. Es determinista: la misma entrada produce el mismo resultado, y por eso login puede comparar. Un cambio pequeño en la entrada cambia el resultado por completo.

*Figura 2. MySQL guarda el resultado del hash, no la contraseña. El ejemplo muestra solo el inicio de ese resultado.*

En login se calcula otra vez el hash de lo que la persona escribió y se compara con el valor guardado. No se descifra nada. Una sal es un extra distinto por persona: Ana y Luis pueden elegir secreto y quedar con dos valores distintos en la base. Esta actividad no pide otro login. Referencia: almacenamiento de contraseñas, OWASP ([https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)).

Fundamentos de Arquitectura de Software y Desarrollo Backend 3 / 15

*Figura 3. Verificar es comparar dos hashes. La sal evita que la misma contraseña se vea igual en dos filas.*

La función no tiene que aplicarse una sola vez. Puede aplicarse n veces: el resultado de una vuelta entra en la siguiente. Ese número forma parte del cálculo. Si al guardar se usaron 3 vueltas, al entrar hay que repetir esas mismas 3. El final vuelve a ser el mismo. Si al entrar solo se hace una vuelta, el valor no coincide con el que está guardado.

Fundamentos de Arquitectura de Software y Desarrollo Backend 4 / 15

*Figura 4. El ejemplo recorta cada resultado. n = 3 en los dos lados, así que el valor final es determinista: 19f4e0c2c36e…*

actorCompanyUserId sigue siendo el dato de laboratorio de la actividad 4: la membresía con la que se prueba en GraphiQL. El cliente puede escribir el id de Ana aunque quien esté frente a la pantalla sea otra persona. Por eso **no autentica**. Sirve para llamar a exigir_permiso y practicar la autorización. El token que impida elegir otra membresía queda para el tema 2.

### 3. La relación es una configuración persistente

role_permissions sigue siendo la tabla puente de la actividad 3. Se mantienen las reglas que ya implementaste: códigos únicos, una sola pareja (role_id, permission_id), reactivar esa fila y desactivar en lugar de borrar.

### Hay dos estados distintos:

· Permission.isActive dice si el permiso sigue en el catálogo. · RolePermission.isActive dice si ese permiso está concedido a ese rol.

Desactivar la relación de accounts.write con Capturista no apaga el permiso para Contador. Guardar la fila permite concederlo otra vez sin insertar un duplicado. No es una bitácora: no guarda quién cambió la lista ni cada fecha anterior. No se pide construir esa bitácora.

### Una lista vacía no significa que el rol todavía no se inicializó.

|Situación|Qué hay en MySQL|Qué hace el arranque|
|---|---|---|
|Primera vez|CAPTURISTA no tiene ninguna fila en role_permissions|Carga la matriz de la actividad 4|
|Después de aplicar []|El rol tiene filas y todas están inactivas|No vuelve a insertar esos permisos|

Si el arranque solo mira “cero relaciones activas” y recarga la matriz, al reiniciar el capturista recuperaría sus cuatro permisos. La prueba de la lista vacía fallaría.

Fundamentos de Arquitectura de Software y Desarrollo Backend 5 / 15

|4. Herramientas de GraphQL para consultar mejor Ya conoces query, mutation, tipos, argumentos y resolvers. Ahora usarás estos recursos en operaciones reproducibles:||
|---|---|
|Recurso|Para qué sirve aquí|
|Operación con nombre|Identificar una prueba, por ejemplo ExplorarCatalogo|
|Variables|Enviar IDs y listas como datos JSON separados del texto de la operación|
|Alias|Consultar dos grupos de permisos en una petición y distinguir sus resultados|
|Fragmento|Reutilizar la selección id, code y name|
|El alias cambia el nombre de una clave de respuesta, no crea otro campo en el servidor. En el ejemplo de la parte 3, el JSON trae cuentas y movimientos, no dos veces permissionCatalog. Un fragmento reutiliza campos: DatosPermiso y fragmentos ([https://graphql.org/learn/queries/](https://graphql.org/learn/queries/)). Enumeraciones y tipos de entrada Una enumeración COMPANY_USERS crea otros permisos. Strawberry permite declararlas con @strawberry.enum. Referencia: enumeraciones ([https://strawberry.rocks/docs/types/enums](https://strawberry.rocks/docs/types/enums)). Un input y su lista final de permisos; se declara con @strawberry.input. Referencia: tipos de entrada ([https://strawberry.rocks/docs/types/input-types](https://strawberry.rocks/docs/types/input-types)). En permissionIds: [ID!]!, la lista es obligatoria y sus elementos no pueden ser null. válida. ID no garantiza ninguna de esas reglas. Distinguir resultados y errores Revisa data y errors en cada respuesta. Un error de validación del documento puede impedir la ejecución; un error durante la ejecución puede producir datos parciales. Ver una respuesta HTTP no demuestra que se guardó la configuración. La evidencia debe relacionar respuesta y estado en MySQL. Referencia: respuestas de GraphQL ([https://graphql.org/learn/response/](https://graphql.org/learn/response/)). 5. Previsualizar una lista completa Antes agregabas un permiso por petición. Ahora enviarás omites uno que antes estaba activo, se retirará. Esta operación no significa “agrega estos permisos a los actuales”. Primero se comprueban los datos. Después se compara la lista deseada con los permisos que hoy están activos:|evita repetir id, code y name. No ejecuta reglas de seguridad. Referencia: consultas, variables, alias permite elegir entre valores definidos. Usaremos ACCOUNTS, CONCEPTS, TRANSACTIONS, y ROLES para filtrar el catálogo. El resolver traduce esos valores a los prefijos ya existentes; no agrupa los datos que recibe una operación. En esta actividad SetRolePermissionsInput contendrá el rol La lista vacía [] sí es La existencia de los IDs, su unicidad y el estado activo de los registros se comprueban en Python; el tipo todos los permisos que deben quedar activos. Si|
|Resultado|Cómo se reconoce|
|Por activar|Viene en la lista deseada y hoy no está activo|
|Por desactivar|Hoy está activo y no viene en la lista deseada|
|Sin cambio|Hoy está activo y también viene en la lista deseada|
|Total final|Cuántos permisos trae la lista deseada|

Fundamentos de Arquitectura de Software y Desarrollo Backend 6 / 15

Con el capturista en su lista inicial, los activos son accounts.read, concepts.read, transactions.read y transactions.write. Si la lista deseada es esa misma más accounts.write, el resultado es: por activar accounts.write, nada por desactivar, cuatro sin cambio y total 5.

*Figura 5. La previsualización detecta una activación, cero desactivaciones y cuatro permisos sin cambio. Todavía no modifica*

*ninguna fila.*

La previsualización será una query: solo lee y calcula. La aplicación será una mutation: cambia el estado. Los efectos de escritura corresponden a los campos raíz de mutación. Referencia: mutaciones de GraphQL ([https://graphql.org/learn/mutations/](https://graphql.org/learn/mutations/)).

La previsualización es una fotografía del momento. No reserva permisos ni garantiza que nadie cambie la configuración después. Al aplicar, el servidor debe volver a validar y calcular contra la base actual. En este laboratorio ejecutaremos los cambios de forma secuencial; no se pide resolver edición concurrente.

### 6. Atomicidad e idempotencia

**Atomicidad** significa que una actualización completa se confirma o se revierte como una sola unidad. Si se activan dos relaciones y se desactiva otra, las tres modificaciones pertenecen a una transacción. Un fallo antes de confirmar debe dejar la configuración anterior.

Fundamentos de Arquitectura de Software y Desarrollo Backend 7 / 15

*Figura 6. Un único punto de confirmación evita configuraciones parciales.*

SQLAlchemy permite delimitar una transacción y usar commit para confirmar o rollback para revertir. Reutiliza el manejo de sesiones del proyecto y evita hacer un commit dentro de cada vuelta del ciclo. Una petición GraphQL con varias mutaciones no proporciona, por sí sola, una transacción de base de datos para todas ellas. Referencia: transacciones en SQLAlchemy ([https://docs.sqlalchemy.org/en/20/orm/session_transaction.html](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)).

**Idempotencia** significa que repetir la misma solicitud deja el mismo estado final. Si Capturista ya tiene exactamente la lista enviada, repetir setRolePermissions no inserta filas ni cambia estados: devuelve changed: false.

Esto no obliga a cambiar assignPermissionToRole: esa operación individual conserva su regla de rechazar una pareja ya activa. Son contratos diferentes. La nueva operación establece una lista completa y permite repetirla sin duplicar relaciones.

### Actividad para entregar

Continúa el Sistema General de Ingresos de la actividad 4, con las herramientas que ya utiliza. Implementa **tres** **funcionalidades nuevas**: consultar el catálogo por recurso, previsualizar una configuración y aplicar la lista completa de un rol.

Al terminar deberás poder explicar los conceptos, ejecutar las operaciones desde GraphiQL y demostrar en MySQL que los resultados coinciden con lo solicitado.

## Parte 1. Investigación breve y preparación

Elabora investigacion.md, de aproximadamente 600 a 900 palabras. Responde con tus palabras y un ejemplo del Sistema General de Ingresos por apartado:

1. ¿Qué diferencia hay entre autenticación, autorización y configuración de permisos? ¿Por qué actorCompanyUserId no comprueba identidad?
Fundamentos de Arquitectura de Software y Desarrollo Backend 8 / 15

2. ¿Cómo ayudan variables, alias y fragmentos a preparar pruebas repetibles? Incluye una operación propia que los utilice.
3. ¿Qué valida un enum o un input de GraphQL y qué reglas deben seguir validándose en Python? Explica también por qué [ID!]! acepta [].
4. ¿Qué diferencia hay entre atomicidad e idempotencia? ¿Por qué enviar varias mutaciones en una petición no garantiza un rollback conjunto? Consulta al menos **tres páginas oficiales**, con una de GraphQL y una de Strawberry. Puedes partir de las referencias enlazadas en la explicación. En cada apartado identifica la fuente utilizada y agrega al final título, URL y fecha de consulta. Explica cómo aplicaste lo investigado; no entregues solo definiciones copiadas o de IA. Antes de programar, registra los cuatro roles y los diez permisos de la actividad 4. Guarda la configuración inicial en configuracion_inicial.json, con el código del rol y los códigos de sus permisos activos. Los otros tres roles van en el mismo archivo. Los id numéricos no van aquí: cambian de una base a otra. { "CAPTURISTA": [ "accounts.read", "concepts.read", "transactions.read", "transactions.write"] } Identifica en GraphQL o en MySQL los id reales de la membresía de Ana, del rol Capturista y de cada permiso. No supongas que son los mismos números en todas las bases.
## Parte 2. Contrato GraphQL

Agrega este contrato al esquema existente. Role y Permission ya existen: reutilízalos. El SDL (Schema Definition Language) es el texto del contrato: enums, inputs, tipos y campos. Describe lo que GraphQL debe mostrar. Los tipos y los resolvers se escriben en Strawberry.

```
enum PermissionResource {
COMPANY_USERS
ACCOUNTS
CONCEPTS
TRANSACTIONS
ROLES
}
input SetRolePermissionsInput {
roleId: ID!
permissionIds: [ID!]!
}
type RolePermissionPlan {
role: Role!
current: [Permission!]!
toActivate: [Permission!]!
toDeactivate: [Permission!]!
unchanged: [Permission!]!
finalCount: Int!
}
type RolePermissionUpdate {
role: Role!
activated: [Permission!]!
deactivated: [Permission!]!
unchanged: [Permission!]!
```
Fundamentos de Arquitectura de Software y Desarrollo Backend 9 / 15

```
finalCount: Int!
changed: Boolean!
}
extend type Query {
permissionCatalog(
actorCompanyUserId: ID!
resource: PermissionResource
): [Permission!]!
previewRolePermissions(
input: SetRolePermissionsInput!
actorCompanyUserId: ID!
): RolePermissionPlan
}
extend type Mutation {
setRolePermissions(
input: SetRolePermissionsInput!
actorCompanyUserId: ID!
): RolePermissionUpdate
}
```
Las listas de resultados se ordenan por Permission.code. En activated y deactivated se informan cambios de **relaciones**; no se modifica el estado del catálogo Permission. Los resultados de previsualizar y aplicar admiten null en su campo raíz para comunicar un error mediante errors, sin devolver un resultado de éxito inventado.

Reutiliza exigir_permiso con roles.read para las dos consultas nuevas y roles.write para la mutación. Usa a Ana como actor en las pruebas de configuración. Esta reutilización no requiere diseñar un nuevo mecanismo de control de acceso ni repetir las pruebas de cambio de puesto de la actividad 4.

### #### Funcionalidad A. Catálogo filtrado

permissionCatalog devuelve solo permisos activos. Si omites resource o envías null, devuelve todo el catálogo activo. Si envías un recurso, devuelve únicamente sus permisos:

|Enum|Prefijo del código|
|---|---|
|COMPANY_USERS|company.users.|
|ACCOUNTS|accounts.|
|CONCEPTS|concepts.|
|TRANSACTIONS|transactions.|
|ROLES|roles.|

El filtro se implementa en el resolver y consulta MySQL; no se arma una lista fija de resultados en Python. El mapeo de enum a prefijo sí puede ser constante. Conserva la consulta permissions anterior.

### #### Funcionalidad B. Previsualización

previewRolePermissions valida la propuesta y devuelve la configuración actual, las diferencias y el total final. No inserta, actualiza ni desactiva filas. Comparte el cálculo de diferencias con la mutación para evitar dos implementaciones que puedan dar resultados distintos.

### #### Funcionalidad C. Actualización completa

setRolePermissions valida de nuevo, calcula los cambios y establece exactamente la lista recibida:

1. Activa o reactiva las parejas deseadas que faltan.
2. Desactiva las parejas activas que ya no se desean.
3. Conserva las que no cambian.
Fundamentos de Arquitectura de Software y Desarrollo Backend 10 / 15

4. Confirma la operación completa una sola vez y devuelve el resumen. No llames en un ciclo a los resolvers anteriores si cada uno confirma su propio cambio. Extrae funciones auxiliares que trabajen con la misma sesión y deja la confirmación a cargo de la operación completa.
### Reglas obligatorias para previsualizar y aplicar:

· El rol debe existir y estar activo. · Cada ID deseado debe ser válido para el proyecto, existir y corresponder a un permiso activo. · Se rechazan IDs repetidos; no se eliminan duplicados en silencio. "3" y 3 son el mismo id. ["3", "3"] es una repetición y debe producir errors. · Si falla una regla, se informa el motivo en errors y no se cambia ninguna relación. · Para este laboratorio, ambas operaciones rechazan propuestas sobre ADMINISTRADOR. Es una regla del ejercicio para no dejar al administrador sin su lista. No es una regla automática de todos los roles. · [] es válido para los demás roles: desactiva todas sus relaciones activas. · Una pareja inactiva se reactiva con el mismo ID de relación. La base debe mantener la unicidad de (role_id, permission_id). · Una segunda aplicación idéntica devuelve changed: false, listas activated y deactivated vacías y el mismo finalCount. · El arranque no repone permisos retirados ni duplica el catálogo. Si ajustas la carga inicial, distingue la ausencia de inicialización de una configuración deliberadamente vacía.

Conserva los cuatro roles y los diez permisos. No necesitas crear permisos nuevos, modificar membresías ni agregar columnas a User. Si falta una restricción en una tabla existente, aplica una migración o un cambio de esquema documentado; create_all no actualiza por sí solo la estructura de tablas ya creadas. No borres cuentas ni movimientos para volver a empezar.

## Parte 3. Operaciones reproducibles

Incluye en operaciones.graphql las consultas y mutaciones con nombre. Guarda sus variables en archivos JSON separados y señala en el README cuál corresponde a cada operación.

Este ejemplo combina variable, alias y fragmento. Sustituye el identificador en el panel de variables de GraphiQL:

```
query ExplorarCatalogo($actor: ID!) {
cuentas: permissionCatalog(resource: ACCOUNTS, actorCompanyUserId: $actor) {
...DatosPermiso
}
movimientos: permissionCatalog(
resource: TRANSACTIONS
actorCompanyUserId: $actor
) {
...DatosPermiso
}
}
fragment DatosPermiso on Permission {
id
code
name
}
{
"actor": "ID_REAL_DE_LA_MEMBRESIA_DE_ANA"
}
```
### Para preparar una configuración:

Fundamentos de Arquitectura de Software y Desarrollo Backend 11 / 15

```
query RevisarConfiguracion($actor: ID!, $input: SetRolePermissionsInput!) {
previewRolePermissions(input: $input, actorCompanyUserId: $actor) {
role {
code
}
current {
code
}
toActivate {
code
}
toDeactivate {
code
}
unchanged {
code
}
finalCount
}
}
mutation AplicarConfiguracion($actor: ID!, $input: SetRolePermissionsInput!) {
setRolePermissions(input: $input, actorCompanyUserId: $actor) {
role {
code
}
activated {
code
}
deactivated {
code
}
unchanged {
code
}
finalCount
changed
}
}
{
"actor": "ID_REAL_DE_LA_MEMBRESIA_DE_ANA",
"input": {
"roleId": "ID_REAL_DE_CAPTURISTA",
"permissionIds": [
"ID_DE_ACCOUNTS_READ",
"ID_DE_CONCEPTS_READ",
"ID_DE_TRANSACTIONS_READ",
"ID_DE_TRANSACTIONS_WRITE",
"ID_DE_ACCOUNTS_WRITE"
]
}
}
```
Los textos ID_DE_... son marcadores que deben reemplazarse por IDs obtenidos de la base. Ejecuta RevisarConfiguracion y AplicarConfiguracion por separado, seleccionando el nombre de la operación. Guardar varias operaciones en un archivo no significa ejecutarlas juntas.

## Parte 4. Casos de prueba y evidencias

Usa estas dos listas durante las pruebas:

Fundamentos de Arquitectura de Software y Desarrollo Backend 12 / 15

· **S0:** los cuatro permisos iniciales de Capturista: accounts.read, concepts.read, transactions.read y transactions.write. · **S1:** S0 más accounts.write, para un total de cinco permisos.

Cada caso tendrá una sección en evidencias.md. Puedes reunir varias capturas en un caso cuando necesites mostrar antes y después. Las pruebas E01 a E10 son obligatorias; las variantes de E06 pueden aparecer en una tabla con sus respuestas.

|Caso|Qué ejecutar|Resultado esperado|Qué debe verse en la evidencia|
|---|---|---|---|
|E01. Punto de partida|Consultar roles, permisos y configuración inicial|Cuatro roles, diez permisos y Capturista en S0|Respuestas con códigos; archivo de configuración inicial; cuatro relaciones activas de Capturista|
|E02. Catálogo|Ejecutar ExplorarCatalogo, consultar sin filtro y probar el enum inexistente PAYMENTS|Dos permisos por grupo; diez sin filtro; error de validación para PAYMENTS|Operaciones, variables, alias de respuesta, fragmento, códigos devueltos y error del enum|
|E03. Previsualización|Proponer S1 cuando está guardada S0|Un permiso por activar, cero por desactivar, cuatro sin cambio y total cinco|Respuesta y consulta SQL antes/después idénticas, con IDs y estados de las relaciones|
|E04. Aplicación|Aplicar S1 y repetir exactamente la petición|Primera ejecución: changed: true. Segunda: changed: false, cero altas/bajas y total cinco|Ambas respuestas y mismas parejas e IDs en SQL; sin duplicados|
|E05. Desactivar y reactivar|Aplicar S0 y luego S1|accounts.write pasa a inactivo y después vuelve a activo|Mismo ID de relación en los tres momentos; el catálogo del permiso sigue activo|
|E06. Entradas inválidas|Probar cada variante descrita debajo, tanto en previsualización como en aplicación|Error descriptivo en todos los casos; configuración sin cambios|Entrada de cada variante, mensaje recibido y comparación SQL antes/después|
|E07. Reversión de un fallo|Ejecutar una prueba controlada que falle después de modificar relaciones y antes del commit|Se revierte todo; la base conserva la lista previa|Resultado del test, punto de fallo y consulta posterior desde una sesión nueva|
|E08. Lista vacía y reinicio|Aplicar [] a Capturista, detener y volver a arrancar el proceso de la API, y consultar otra vez|Cero relaciones activas antes y después del arranque; filas conservadas|Respuesta, arranque nuevo y SQL con relaciones inactivas; cuatro roles y diez permisos sin duplicados|
|E09. Restauración|Aplicar S0 y consultar los cuatro roles|Matriz activa igual a la configuración inicial|Comparación por códigos de los cuatro roles, consulta final y ausencia de parejas duplicadas|
|E10. Continuidad del proyecto|Ejecutar una consulta existente de cuentas y registrar un movimiento válido con los datos y mecanismos previos|Las operaciones anteriores siguen funcionando|Consulta, mutación y movimiento persistido, con cuenta, concepto, empresa y monto válidos|

**Variantes de E06:** ID de rol inexistente; rol inactivo; propuesta sobre ADMINISTRADOR; ID de permiso inexistente mezclado con IDs válidos; permiso inactivo; ID de permiso repetido. Para los estados inactivos usa datos de laboratorio y una preparación SQL documentada si el proyecto no ofrece esa operación. Restablece esos estados al terminar cada variante. No se pide crear nuevas mutaciones para esta preparación.

**Prueba E07:** implementa un test automatizado con unittest, incluido en Python, o con la herramienta que ya use el equipo. Puede provocar una excepción controlada después de un flush y antes de confirmar, usando un reemplazo temporal o _mock_ dentro del test. flush envía las modificaciones pendientes a la base, pero todavía no las confirma. No agregues un parámetro público para provocar fallos. Una entrada inválida rechazada antes de escribir demuestra validación, pero no demuestra por sí sola el rollback de escrituras pendientes. La prueba debe verificar el estado persistido desde una sesión nueva.

Para inspeccionar relaciones puedes adaptar esta consulta a los nombres reales del proyecto:

Fundamentos de Arquitectura de Software y Desarrollo Backend 13 / 15

|SELECT rp.id AS relacion_id, r.code AS rol, p.code AS permiso, rp.is_active AS relacion_activa, p.is_active AS permiso_activo FROM role_permissions rp JOIN roles r ON r.id = rp.role_id JOIN permissions p ON p.id = rp.permission_id ORDER BY r.code, p.code; Para comprobar duplicados: SELECT role_id, permission_id, COUNT(*) AS repeticiones FROM role_permissions GROUP BY role_id, permission_id HAVING COUNT(*) > 1; La segunda consulta debe devolver cero filas. Para comparar estados usa los IDs, códigos y estados de las relaciones; un conteo igual no demuestra que sean las mismas parejas. El archivo final representa las concesiones activas : pueden conservarse filas inactivas adicionales de las pruebas. #### Cómo presentar cada evidencia Cada caso debe indicar: regla demostrada Las capturas deben permitir leer la petición y su respuesta. Si no caben, sepáralas y usa el mismo número de caso. Acompáñalas con las operaciones como texto para poder repetirlas. No basta una captura del código fuente, del servidor encendido o de una respuesta “exitosa” sin comprobar su contenido. Utiliza usuarios y datos ficticios. No muestres contraseñas, tokens, hashes completos ni credenciales de conexión en las evidencias. Esta actividad evalúa la configuración de permisos, no la exposición de secretos. Entregables Entrega un link a github y un archivo ZIP en Teams llamado unidad2_actividad5_equipo, con esta organización orientativa: unidad2_actividad5_equipo/ ingresos/ # Proyecto completo actualizado ... # Archivos y estructura existentes tests/ # Incluye la prueba E07 README.md investigacion.md operaciones.graphql variables/ # JSON de los casos de prueba configuracion_inicial.json configuracion_final.json comprobaciones.sql evidencias.md evidencias/ # Capturas identificadas E01, E02, etc.|precondición, operación y variables, resultado esperado, resultado obtenido y. Añade el SQL o test correspondiente cuando se pida comprobar persistencia.|
|---|---|
|Entregable|Contenido mínimo verificable|
|Código|Tres funcionalidades, tipos Strawberry, validaciones, operación atómica e idempotente, relaciones únicas y carga inicial que respeta la configuración|
|README|Integrantes y aportaciones; dependencias; instrucciones para iniciar API/MySQL, preparar los datos, ejecutar operaciones y correr E07; nombres reales de archivos y comandos|

Fundamentos de Arquitectura de Software y Desarrollo Backend 14 / 15

|Entregable|Contenido mínimo verificable|
|---|---|
|Investigación|Cuatro respuestas razonadas, ejemplos propios y al menos tres fuentes oficiales|
|Operaciones y variables|Documentos GraphQL ejecutables con nombre, variables reales de laboratorio, al menos un alias y un fragmento utilizados|
|Configuraciones y SQL|Matriz inicial y final por códigos, consultas de verificación y preparación/restauración de datos de E06|
|Evidencias Incluye las migraciones si modificaste el esquema y un archivo de configuración de ejemplo sin secretos si hace falta. Excluye entornos virtuales, cachés y credenciales reales. El código y las instrucciones deben permitir repetir la entrega; las capturas no los sustituyen. Lista de revisión antes de entregar · Puedo explicar por qué un ID de membresía no autentica a una persona. · Las tres funcionalidades consultan o actualizan la base real del proyecto. · Previsualizar no cambia filas; aplicar confirma toda la lista una sola vez. · Las entradas inválidas no cambian la configuración y E07 demuestra reversión. · Repetir una lista no duplica parejas; reactivar conserva el ID de relación. · Una lista vacía permanece vacía después de reiniciar. · La matriz final coincide con la inicial y las funciones anteriores siguen operando. · Las operaciones, variables y evidencias permiten reproducir cada caso. · El trabajo se mantiene en el tema 1; no anticipa la implementación del tema 2.|Casos E01 a E10 identificados y explicados, con las comprobaciones que exige cada fila|

Fundamentos de Arquitectura de Software y Desarrollo Backend 15 / 15