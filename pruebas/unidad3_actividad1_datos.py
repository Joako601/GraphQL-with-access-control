r"""Unidad III, Actividad 1: datos fijos para la demo del dashboard.

A diferencia de actividad7.py (empresas nuevas con sufijo aleatorio en cada corrida), aquí los correos son fijos
para poder iniciar sesión en el dashboard sin buscar sufijos. Es idempotente: si la empresa demo ya existe, no
crea nada. Requiere la API de docker compose. Ejecutar desde la raíz:
    python pruebas/unidad3_actividad1_datos.py

Crea la empresa "Empresa Demo Dashboard" con Banco/Caja/Ahorro y los seis movimientos de la Actividad 7, y tres
usuarios (contraseña secreto123):
    ana.demo@empresa.test         ADMINISTRADOR     ve el dashboard completo
    pedro.demo@empresa.test       CONSULTA          solo lectura, también ve el dashboard
    sinlectura.demo@empresa.test  DEMO_SIN_LECTURA  rol sin accounts.read ni transactions.read: acceso denegado
"""
import actividad6 as a6
import actividad7_datos as d

EMPRESA = "Empresa Demo Dashboard"
ROL_SIN_LECTURA = "DEMO_SIN_LECTURA"
LOGIN = "mutation($e: String!, $p: String!) { login(input: {email: $e, password: $p}) { token } }"


def correo(nombre):
    return f"{nombre.lower()}.demo@empresa.test"


def login(nombre):
    r = d.gql(LOGIN, {"e": correo(nombre), "p": a6.PASSWORD})
    return None if r.get("errors") else r["data"]["login"]["token"]


def usuario(token_admin, company, nombre, role_id):
    q = """mutation($c: ID!, $n: String!, $e: String!, $p: String!, $r: ID!) {
      createCompanyUser(input: {companyId: $c, name: $n, email: $e, password: $p, roleId: $r}) { id } }"""
    variables = {"c": company, "n": nombre, "e": correo(nombre), "p": a6.PASSWORD, "r": role_id}
    a6.ok(d.gql(q, variables, token_admin), "createCompanyUser")


def rol_sin_lectura(token_admin, roles):
    """Rol con un solo permiso que no es de lectura de balances; se reutiliza si ya existe."""
    if ROL_SIN_LECTURA in roles:
        return roles[ROL_SIN_LECTURA]
    q = """mutation($c: String!) { createRole(input: {code: $c, name: "Demo sin lectura",
      description: "Unidad III: usuario de demo sin permisos de lectura de balances"}) { id } }"""
    rol = a6.ok(d.gql(q, {"c": ROL_SIN_LECTURA}, token_admin), "createRole")["id"]
    permisos = {p["code"]: p["id"] for p in a6.ok(d.gql("{ permissions { id code } }"), "permissions")}
    q = "mutation($r: ID!, $p: ID!) { assignPermissionToRole(input: {roleId: $r, permissionId: $p}) { id } }"
    a6.ok(d.gql(q, {"r": rol, "p": permisos["concepts.read"]}, token_admin), "assignPermissionToRole")
    return rol


def preparar():
    if login("Ana"):
        print(f"{EMPRESA} ya existe; no se crea nada.")
        return
    company = a6.ok(d.gql('mutation($n: String!) { createCompany(input: {name: $n}) { id } }', {"n": EMPRESA}),
                    "createCompany")["id"]
    a6.ok(d.gql("""mutation($c: ID!, $n: String!, $e: String!, $p: String!) {
      createCompanyAdmin(input: {companyId: $c, name: $n, email: $e, password: $p}) { id } }""",
                {"c": company, "n": "Ana Demo", "e": correo("Ana"), "p": a6.PASSWORD}), "createCompanyAdmin")
    ana = login("Ana")

    concs = d.conceptos(ana, company)
    cuentas = {n: d.cuenta(ana, company, concs, n) for n in d.CUENTAS}
    for nombre, dia, tipo, monto, desc in d.DATOS:
        d.mov(ana, concs, cuentas[nombre], tipo, monto, d.utc(dia), desc)

    roles = {r["code"]: r["id"] for r in a6.ok(d.gql("{ roles { id code } }"), "roles")}
    usuario(ana, company, "Pedro", roles["CONSULTA"])
    usuario(ana, company, "SinLectura", rol_sin_lectura(ana, roles))
    print(f"{EMPRESA} creada (companyId {company}). Usuarios: "
          + ", ".join(correo(n) for n in ("Ana", "Pedro", "SinLectura")) + f" / {a6.PASSWORD}")


def verificar():
    """Compara el generalBalance real con la tabla calculada a mano en actividad7_datos.py."""
    g = a6.ok(d.general(login("Ana")), "generalBalance")
    cuentas = {c["accountName"]: c for c in g["accounts"]}
    fallos = [k for k, v in d.GENERAL.items() if g[k] != v]
    fallos += [f"{n}.{k}" for n, esp in d.ESPERADO.items() for k, v in esp.items() if cuentas[n][k] != v]
    sin_lectura = d.general(login("SinLectura")).get("errors", [{}])[0].get("message", "(sin error)")
    print(f"Período {d.F} a {d.T}: {'coincide con la tabla a mano' if not fallos else f'DIFERENCIAS {fallos}'}")
    print(f"SinLectura -> {sin_lectura}")
    return not fallos and sin_lectura.startswith("Permiso denegado")


if __name__ == "__main__":
    preparar()
    raise SystemExit(0 if verificar() else 1)
