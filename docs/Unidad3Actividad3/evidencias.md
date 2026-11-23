# Evidencias · Unidad III, Actividad 3

Capturas del dashboard y GraphiQL sobre la API local con PostgreSQL y los usuarios de laboratorio.

1. [Matriz inicial](evidencias/01-matriz-inicial.png). Los diez permisos coinciden con la sección 2.2 y Administrador figura en solo lectura.
2. [Capturista en GraphiQL](evidencias/02-graphiql-capturista.png). `rolePermissions` devuelve las cuatro concesiones iniciales del rol.
3. [Vista previa](evidencias/03-vista-previa.png). Se activa `accounts.write`, quedan cuatro permisos sin cambio y el total final es cinco.
4. [Cuentas antes](evidencias/04a-cuentas-antes.png) y [Cuentas después](evidencias/04b-cuentas-despues.png). Aparece **Nueva cuenta** en la sesión de Ariff tras guardar la columna Capturista.
5. [Usuario reasignado](evidencias/05a-usuario-reasignado.png) y [columna Consulta](evidencias/05b-columna-consulta.png). Fernando ahora es Capturista, sigue con `isAdmin: false` y la columna Consulta conserva sus celdas.
6. [Segundo guardado](evidencias/06-guardado-sin-cambios.png). El mismo conjunto de cinco permisos devuelve `changed: false`.
7. [Contador en solo lectura](evidencias/07-contador-solo-lectura.png). La matriz se ve y la sesión carece de controles de edición.
