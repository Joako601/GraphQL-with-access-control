# Unidad II, Actividad 6 — Control de acceso según el rol

La persona ya no escribe `actorCompanyUserId`. `login` comprueba el hash y firma un JWT (HS256, 30 minutos) con
`companyUserId`, `companyId` y `exp`. Cada ruta protegida lee la membresía desde `Authorization: Bearer <token>`
(`leer_actor` en `services/auth.py`) y después llama `exigir_permiso` con el mismo permiso de antes.

## Secreto

Se genera una sola vez y se guarda en `.env` (ignorado por Git), nunca en el código:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env.example` documenta `JWT_SECRET` con un valor de ejemplo sin uso real y `JWT_EXPIRE_MINUTES=30`.

## Uso en GraphiQL (`http://localhost:8004/graphql`)

1. Mutación `login` sin encabezado:
   ```graphql
   mutation { login(input: { email: "maria@empresa.test", password: "secreto123" }) { tokenType token user { name } } }
   ```
   Si la persona pertenece a varias empresas, agrega `companyId` para elegir la membresía; cada token vale para una empresa.
2. En *Headers*: `{"Authorization": "Bearer TOKEN_QUE_DEVOLVIO_LOGIN"}` y lanza la operación sin `actorCompanyUserId`.

`login`, `createCompany` y `createCompanyAdmin` no piden token. Los catálogos `roles`, `permissions` y `rolePermissions`
siguen públicos como en las actividades anteriores.

## Pruebas (casos 1 a 9)

Con `docker compose up -d --build` en marcha:

```
python pruebas/actividad6.py
```

Crea dos empresas nuevas (Ana, María, Luis, Pedro y Beto en la otra empresa), ejecuta los casos y escribe
`evidencias.json` con el encabezado recortado, el resultado y el conteo SQL antes/después de cada escritura.
El caso 9 se divide en 9a (firma alterada) y 9b (token vencido, firmado localmente con `exp` en el pasado).

| Caso | Token | Ruta | Regla que demuestra |
|---|---|---|---|
| 1 | Ninguno | `createAccount` | Sin token no se escribe |
| 2 | María, capturista | `createTransaction` | El rol tiene `transactions.write` |
| 3 | María, capturista | `createAccount` | Token válido no basta: falta `accounts.write` |
| 4 | Luis, contador | `createAccount` | Misma ruta, otro rol, sí se guarda |
| 5 | Pedro, consulta | `createTransaction` | CONSULTA no escribe movimientos |
| 6 | Ana | `assignRole` Pedro → CAPTURISTA | Solo `roles.write` cambia puestos |
| 7 | Token anterior de Pedro | `createTransaction` | El rol se lee en la base en cada petición |
| 8 | Beto, otra empresa | `accounts` de esta empresa | El token solo vale para su empresa |
| 9 | Alterado / vencido | `createAccount` | `jwt.decode` rechaza y no se escribe |

Consulta para comprobar que un rechazo no dejó fila (sustituye el id de la empresa):

```sql
SELECT COUNT(*) FROM accounts WHERE company_id = 1;
SELECT COUNT(*) FROM transactions WHERE company_id = 1;
```

No publiques `.env`, el secreto ni tokens vigentes.
