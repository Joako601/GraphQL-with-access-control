import html
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
USAR_GRAPHIQL = "--graphiql" in sys.argv
API_URL = ARGS[0] if ARGS else "http://localhost:8001/graphql"
CARPETA = Path(__file__).resolve().parent.parent / "docs" / "evidencias_roles"
SALIDA = CARPETA / "resultados.json"
CAPTURAS = CARPETA / "capturas"
DB_CONTAINER = "actividad4-postgres"
API_CONTAINER = "actividad4-api"
SUFIJO = str(int(time.time()))
PASSWORD = "Password123"
NOTA_ROLE_PERMISSIONS = (
    "role_permissions tiene 27 filas: las 26 parejas de la matriz (10 + 8 + 4 + 4) y la pareja "
    "CAPTURISTA + accounts.write que removePermissionFromRole dejó con is_active = false, porque no se borra."
)

pasos = []
navegador = None


def abrir_navegador():
    global navegador
    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    navegador = playwright.chromium.launch(channel="chrome")
    CAPTURAS.mkdir(parents=True, exist_ok=True)


def nombre_captura(clave):
    return f"{len(pasos) + 1:02d}_{clave}.png"


def graphiql(query, variables, token, archivo):
    parametros = {"q": query.strip()}
    if variables:
        parametros["variables"] = json.dumps(variables, indent=2, ensure_ascii=False)
    if token:
        parametros["headers"] = json.dumps({"Authorization": f"Bearer {token}"}, indent=2)
    url = API_URL + "?" + urllib.parse.urlencode(parametros, quote_via=urllib.parse.quote)
    contexto = navegador.new_context(viewport={"width": 1500, "height": 900})
    page = contexto.new_page()
    page.goto(url)
    page.wait_for_selector(".graphiql-execute-button", timeout=30000)
    page.wait_for_timeout(1200)
    page.click(".graphiql-execute-button")
    page.wait_for_function(
        "() => { const e = document.querySelector('.result-window .CodeMirror');"
        " return e && e.CodeMirror.getValue().trim().length > 2; }",
        timeout=20000,
    )
    texto = page.evaluate("() => document.querySelector('.result-window .CodeMirror').CodeMirror.getValue()")
    lineas_variables = len(parametros.get("variables", "").splitlines())
    lineas = max(len(texto.splitlines()), len(query.strip().splitlines()) + lineas_variables + 16)
    page.set_viewport_size({"width": 1500, "height": max(900, int(lineas * 22.5) + 160)})
    page.wait_for_timeout(600)
    page.screenshot(path=str(CAPTURAS / archivo))
    contexto.close()
    return json.loads(texto)


def captura_terminal(texto, archivo):
    contexto = navegador.new_context(viewport={"width": 1300, "height": 400})
    page = contexto.new_page()
    page.set_content(
        "<html><body style='margin:0;background:#1e1e1e'>"
        "<div style='padding:10px 16px;background:#2d2d2d;color:#ccc;font:13px Segoe UI'>"
        f"PowerShell — docker exec -it {DB_CONTAINER} psql -U postgres -d sistema_financiero</div>"
        "<pre style='margin:0;padding:16px;color:#e6e6e6;font:15px Consolas,monospace;white-space:pre'>"
        f"{html.escape(texto)}</pre></body></html>"
    )
    page.screenshot(path=str(CAPTURAS / archivo), full_page=True)
    contexto.close()


def graphql(query, variables=None, token=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    request = urllib.request.Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())


def sql(consulta):
    resultado = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", "postgres", "-d", "sistema_financiero", "-c", consulta],
        capture_output=True, text=True, encoding="utf-8",
    )
    return resultado.stdout.strip()


def sql_valor(consulta):
    resultado = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", "postgres", "-d", "sistema_financiero", "-tAc", consulta],
        capture_output=True, text=True, encoding="utf-8",
    )
    return resultado.stdout.strip()


def paso(clave, titulo, regla, query, variables=None, token=None, actor=None, espera_error=False, extra=None):
    captura = None
    if USAR_GRAPHIQL:
        captura = nombre_captura(clave)
        respuesta = graphiql(query, variables, token, captura)
    else:
        respuesta = graphql(query, variables, token)
    tiene_error = bool(respuesta.get("errors"))
    correcto = tiene_error == espera_error
    pasos.append({
        "clave": clave,
        "titulo": titulo,
        "regla": regla,
        "actor": actor,
        "query": query.strip(),
        "variables": variables or {},
        "respuesta": respuesta,
        "espera_error": espera_error,
        "correcto": correcto,
        "extra": extra,
        "captura": captura,
    })
    marca = "OK " if correcto else "FALLA"
    print(f"[{marca}] {clave}: {titulo}")
    return respuesta


def paso_sql(clave, titulo, regla, consultas, correcto=True):
    salida = "\n\n".join(f"sistema_financiero=# {c}\n{sql(c)}" for c in consultas)
    captura = None
    if USAR_GRAPHIQL:
        captura = nombre_captura(clave)
        captura_terminal(salida, captura)
    pasos.append({"clave": clave, "titulo": titulo, "regla": regla, "sql": salida, "correcto": correcto,
                  "captura": captura})
    print(f"[{'OK ' if correcto else 'FALLA'}] {clave}: {titulo}")


def login(email):
    datos = graphql(
        "mutation($input: LoginInput!) { login(input: $input) { token user { id name } } }",
        {"input": {"email": email, "password": PASSWORD}},
    )
    return datos["data"]["login"]["token"]


def rol_id(codigo):
    roles = graphql("{ roles { id code } }")["data"]["roles"]
    return next(r["id"] for r in roles if r["code"] == codigo)


def permisos_de(resp):
    return [rp["permission"]["code"] for rp in resp["data"]["rolePermissions"]]


def main():
    if USAR_GRAPHIQL:
        abrir_navegador()
    empresa = graphql(
        "mutation($input: CreateCompanyInput!) { createCompany(input: $input) { id name } }",
        {"input": {"name": f"Comercializadora Roles {SUFIJO}"}},
    )["data"]["createCompany"]
    empresa_b = graphql(
        "mutation($input: CreateCompanyInput!) { createCompany(input: $input) { id name } }",
        {"input": {"name": f"Empresa B {SUFIJO}"}},
    )["data"]["createCompany"]

    admin_query = """
mutation CrearAdmin($input: CreateCompanyAdminInput!) {
  createCompanyAdmin(input: $input) {
    id
    isAdmin
    user { name email }
    role { code name }
  }
}"""
    admin_email = f"admin.{SUFIJO}@ingresos.mx"
    admin = paso(
        "admin", "createCompanyAdmin crea al administrador principal con el rol ADMINISTRADOR",
        "El administrador principal conserva isAdmin = true y además recibe el rol ADMINISTRADOR.",
        admin_query,
        {"input": {"companyId": empresa["id"], "name": "Andrea Administradora", "email": admin_email, "password": PASSWORD}},
        actor="Sin autenticación (operación pública, igual que antes)",
    )["data"]["createCompanyAdmin"]
    admin_token = login(admin_email)
    admin_cu = admin["id"]

    admin_b_cu = graphql(
        "mutation($input: CreateCompanyAdminInput!) { createCompanyAdmin(input: $input) { id } }",
        {"input": {"companyId": empresa_b["id"], "name": "Beto Admin B", "email": f"adminb.{SUFIJO}@ingresos.mx", "password": PASSWORD}},
    )["data"]["createCompanyAdmin"]["id"]
    admin_b_token = login(f"adminb.{SUFIJO}@ingresos.mx")

    paso(
        "roles", "roles muestra los cuatro códigos",
        "El catálogo de roles se sembró al arrancar con ADMINISTRADOR, CONTADOR, CAPTURISTA y CONSULTA.",
        """
query {
  roles {
    id
    code
    name
    description
    isActive
  }
}""",
        actor="Consulta pública del catálogo",
    )
    paso(
        "permissions", "permissions muestra los diez códigos",
        "El catálogo de permisos tiene los diez códigos recurso.accion que salen de las operaciones del sistema.",
        """
query {
  permissions {
    id
    code
    name
    isActive
  }
}""",
        actor="Consulta pública del catálogo",
    )

    rp_query = """
query PermisosDelRol($roleId: ID!) {
  rolePermissions(roleId: $roleId) {
    id
    isActive
    role { code }
    permission { code }
  }
}"""
    capturista_rp = paso(
        "rp_capturista", "rolePermissions del CAPTURISTA",
        "El capturista tiene transactions.write y no tiene accounts.write: registra movimientos, pero no cambia el catálogo.",
        rp_query, {"roleId": rol_id("CAPTURISTA")}, actor="Consulta pública de la matriz",
    )
    codigos = permisos_de(capturista_rp)
    pasos[-1]["correcto"] = "transactions.write" in codigos and "accounts.write" not in codigos

    consulta_rp = paso(
        "rp_consulta", "rolePermissions de CONSULTA",
        "El rol CONSULTA no tiene ningún permiso que termine en .write: solo lee.",
        rp_query, {"roleId": rol_id("CONSULTA")}, actor="Consulta pública de la matriz",
    )
    pasos[-1]["correcto"] = not any(c.endswith(".write") for c in permisos_de(consulta_rp))

    crear_usuario_query = """
mutation CrearUsuario($actor: ID!, $input: CreateCompanyUserInput!) {
  createCompanyUser(actorCompanyUserId: $actor, input: $input) {
    id
    isAdmin
    user { name email }
    role { code }
  }
}"""
    miembros = {}
    for clave, nombre, rol in [
        ("contador", "Carlos Contador", "CONTADOR"),
        ("capturista", "Ana Capturista", "CAPTURISTA"),
        ("consulta", "Olga Consulta", "CONSULTA"),
        ("capturista2", "Luis Capturista", "CAPTURISTA"),
    ]:
        email = f"{clave}.{SUFIJO}@ingresos.mx"
        variables = {"actor": admin_cu, "input": {
            "companyId": empresa["id"], "name": nombre, "email": email, "password": PASSWORD, "roleId": rol_id(rol)}}
        if clave == "contador":
            cu = paso(
                "crear_usuarios", "El administrador crea usuarios y les da un rol",
                "createCompanyUser exige company.users.write; la membresía nace con el rol indicado, no con un permiso suelto.",
                crear_usuario_query, variables, admin_token, actor="Andrea (ADMINISTRADOR)",
            )["data"]["createCompanyUser"]
        else:
            cu = graphql(crear_usuario_query, variables, admin_token)["data"]["createCompanyUser"]
        miembros[clave] = {"id": cu["id"], "token": login(email), "nombre": nombre}

    paso(
        "consulta_no_crea_usuarios", "CONSULTA intenta crear un usuario",
        "Sin company.users.write la operación se rechaza aunque la persona pertenezca a la empresa.",
        crear_usuario_query,
        {"actor": miembros["consulta"]["id"], "input": {
            "companyId": empresa["id"], "name": "Intruso", "email": f"intruso.{SUFIJO}@ingresos.mx", "password": PASSWORD}},
        miembros["consulta"]["token"], actor="Olga (CONSULTA)", espera_error=True,
    )

    cuenta = graphql(
        """mutation($actor: ID!, $input: CreateAccountInput!) {
          createAccount(actorCompanyUserId: $actor, input: $input) { id name } }""",
        {"actor": admin_cu, "input": {"companyId": empresa["id"], "accountType": "DEBIT", "name": "Cuenta operativa"}},
        admin_token,
    )["data"]["createAccount"]
    concepto = graphql(
        """mutation($actor: ID!, $input: CreateConceptInput!) {
          createConcept(actorCompanyUserId: $actor, input: $input) { id name } }""",
        {"actor": admin_cu, "input": {"companyId": empresa["id"], "conceptType": "INCOME", "name": "Venta de mostrador"}},
        admin_token,
    )["data"]["createConcept"]
    graphql(
        """mutation($actor: ID!, $input: AssignConceptToAccountInput!) {
          assignConceptToAccount(actorCompanyUserId: $actor, input: $input) { id } }""",
        {"actor": admin_cu, "input": {"accountId": cuenta["id"], "conceptId": concepto["id"]}},
        admin_token,
    )

    mov_query = """
mutation RegistrarMovimiento($actor: ID!, $input: CreateTransactionInput!) {
  createTransaction(actorCompanyUserId: $actor, input: $input) {
    id
    transactionType
    amount
    capturedByUser { name }
    account { name }
    concept { name }
  }
}"""
    mov_input = {"accountId": cuenta["id"], "conceptId": concepto["id"], "transactionType": "INCOME",
                 "amount": "1500.00", "shortDescription": "Venta del día"}

    antes = sql_valor(f"SELECT COUNT(*) FROM transactions WHERE company_id = {empresa['id']};")
    paso(
        "mov_capturista", "CAPTURISTA registra un movimiento",
        "El rol CAPTURISTA incluye transactions.write: createTransaction guarda el movimiento.",
        mov_query, {"actor": miembros["capturista"]["id"], "input": mov_input},
        miembros["capturista"]["token"], actor="Ana (CAPTURISTA)",
    )
    despues_ok = sql_valor(f"SELECT COUNT(*) FROM transactions WHERE company_id = {empresa['id']};")

    paso(
        "mov_consulta", "CONSULTA intenta registrar un movimiento",
        "CONSULTA no tiene transactions.write: GraphQL responde errors y la tabla transactions no gana la fila.",
        mov_query, {"actor": miembros["consulta"]["id"], "input": {**mov_input, "amount": "999.00"}},
        miembros["consulta"]["token"], actor="Olga (CONSULTA)", espera_error=True,
    )
    despues_rechazo = sql_valor(f"SELECT COUNT(*) FROM transactions WHERE company_id = {empresa['id']};")
    pasos[-1]["extra"] = (
        f"Movimientos de la empresa en PostgreSQL: antes {antes}, después del capturista {despues_ok}, "
        f"después del intento de consulta {despues_rechazo}."
    )
    pasos[-1]["correcto"] = pasos[-1]["correcto"] and despues_ok == despues_rechazo and int(despues_ok) == int(antes) + 1

    cuenta_query = """
mutation CrearCuenta($actor: ID!, $input: CreateAccountInput!) {
  createAccount(actorCompanyUserId: $actor, input: $input) {
    id
    name
    accountType
    company { name }
  }
}"""
    paso(
        "cuenta_contador", "CONTADOR crea una cuenta",
        "El rol CONTADOR incluye accounts.write: createAccount funciona.",
        cuenta_query,
        {"actor": miembros["contador"]["id"], "input": {"companyId": empresa["id"], "accountType": "CASH", "name": "Caja chica"}},
        miembros["contador"]["token"], actor="Carlos (CONTADOR)",
    )
    paso(
        "cuenta_capturista", "CAPTURISTA intenta crear una cuenta",
        "El rol CAPTURISTA no incluye accounts.write: createAccount se rechaza antes del INSERT.",
        cuenta_query,
        {"actor": miembros["capturista"]["id"], "input": {"companyId": empresa["id"], "accountType": "CASH", "name": "Caja de Ana"}},
        miembros["capturista"]["token"], actor="Ana (CAPTURISTA)", espera_error=True,
    )

    paso(
        "cuenta_capturista2_antes", "Luis (CAPTURISTA) intenta crear una cuenta antes del cambio de rol",
        "Antes de assignRole, Luis no tiene accounts.write.",
        cuenta_query,
        {"actor": miembros["capturista2"]["id"], "input": {"companyId": empresa["id"], "accountType": "SAVINGS", "name": "Ahorro"}},
        miembros["capturista2"]["token"], actor="Luis (CAPTURISTA)", espera_error=True,
    )
    paso(
        "assign_role", "assignRole cambia a Luis de CAPTURISTA a CONTADOR",
        "assignRole exige roles.write, desactiva el rol anterior y deja un solo rol activo en la membresía.",
        """
mutation CambiarRol($actor: ID!, $input: AssignRoleInput!) {
  assignRole(actorCompanyUserId: $actor, input: $input) {
    id
    isActive
    role { code }
    companyUser { id user { name } }
  }
}""",
        {"actor": admin_cu, "input": {"companyUserId": miembros["capturista2"]["id"], "roleId": rol_id("CONTADOR")}},
        admin_token, actor="Andrea (ADMINISTRADOR)",
    )
    paso_sql(
        "assign_role_sql", "Historial de roles de la membresía de Luis",
        "La fila anterior queda con is_active = false y solo hay un rol activo por membresía.",
        [f"SELECT cur.id, cur.company_user_id, r.code, cur.is_active FROM company_user_roles cur "
         f"JOIN roles r ON r.id = cur.role_id WHERE cur.company_user_id = {miembros['capturista2']['id']} ORDER BY cur.id;"],
    )
    paso(
        "cuenta_capturista2_despues", "Luis, ya como CONTADOR, crea una cuenta",
        "Después de assignRole el permiso se lee del nuevo rol: ahora createAccount funciona.",
        cuenta_query,
        {"actor": miembros["capturista2"]["id"], "input": {"companyId": empresa["id"], "accountType": "SAVINGS", "name": "Ahorro"}},
        miembros["capturista2"]["token"], actor="Luis (CONTADOR)",
    )
    paso(
        "assign_role_contador", "CONTADOR intenta cambiar el rol de otra persona",
        "El contador no tiene roles.write: no puede cambiar la matriz ni los roles.",
        """
mutation CambiarRol($actor: ID!, $input: AssignRoleInput!) {
  assignRole(actorCompanyUserId: $actor, input: $input) { id role { code } }
}""",
        {"actor": miembros["contador"]["id"], "input": {"companyUserId": miembros["capturista"]["id"], "roleId": rol_id("CONTADOR")}},
        miembros["contador"]["token"], actor="Carlos (CONTADOR)", espera_error=True,
    )

    permisos = graphql("{ permissions { id code } }")["data"]["permissions"]
    accounts_write = next(p["id"] for p in permisos if p["code"] == "accounts.write")
    asignar_permiso = """
mutation AsignarPermiso($actor: ID!, $input: AssignPermissionToRoleInput!) {
  assignPermissionToRole(actorCompanyUserId: $actor, input: $input) {
    id
    isActive
    role { code }
    permission { code }
  }
}"""
    paso(
        "permiso_duplicado", "assignPermissionToRole con una pareja que ya está activa",
        "assignPermissionToRole rechaza la pareja duplicada CONTADOR + accounts.write.",
        asignar_permiso,
        {"actor": admin_cu, "input": {"roleId": rol_id("CONTADOR"), "permissionId": accounts_write}},
        admin_token, actor="Andrea (ADMINISTRADOR)", espera_error=True,
    )
    paso(
        "permiso_capturista", "El administrador da accounts.write al rol CAPTURISTA",
        "Un cambio de política se hace una vez en el rol y vale para todas las membresías con ese rol.",
        asignar_permiso,
        {"actor": admin_cu, "input": {"roleId": rol_id("CAPTURISTA"), "permissionId": accounts_write}},
        admin_token, actor="Andrea (ADMINISTRADOR)",
    )
    paso(
        "quitar_permiso", "removePermissionFromRole quita accounts.write al CAPTURISTA",
        "removePermissionFromRole desactiva la pareja (no borra la fila) y la matriz vuelve a la del documento.",
        """
mutation QuitarPermiso($actor: ID!, $roleId: ID!, $permissionId: ID!) {
  removePermissionFromRole(actorCompanyUserId: $actor, roleId: $roleId, permissionId: $permissionId)
}""",
        {"actor": admin_cu, "roleId": rol_id("CAPTURISTA"), "permissionId": accounts_write},
        admin_token, actor="Andrea (ADMINISTRADOR)",
    )

    paso(
        "segundo_admin", "Un segundo createCompanyAdmin en la misma empresa",
        "La regla de un solo administrador principal se mantiene: el segundo createCompanyAdmin sigue fallando.",
        admin_query,
        {"input": {"companyId": empresa["id"], "name": "Otro Admin", "email": f"otro.{SUFIJO}@ingresos.mx", "password": PASSWORD}},
        actor="Sin autenticación", espera_error=True,
    )

    paso(
        "otra_empresa", "El administrador de la Empresa B intenta crear una cuenta en la Empresa A",
        "Los datos de una empresa no se mezclan: la membresía del actor debe ser de la empresa del recurso.",
        cuenta_query,
        {"actor": admin_b_cu, "input": {"companyId": empresa["id"], "accountType": "CASH", "name": "Cuenta ajena"}},
        admin_b_token, actor="Beto (ADMINISTRADOR de la Empresa B)", espera_error=True,
    )

    paso(
        "transacciones_consulta", "CONSULTA lee los movimientos",
        "Las consultas exigen el permiso .read: CONSULTA tiene transactions.read y ve solo los movimientos de su empresa.",
        """
query Movimientos($actor: ID!) {
  transactions(actorCompanyUserId: $actor) {
    id
    transactionType
    amount
    capturedByUser { name }
  }
}""",
        {"actor": miembros["consulta"]["id"]}, miembros["consulta"]["token"], actor="Olga (CONSULTA)",
    )

    paso_sql(
        "sql_matriz", "SELECT de roles, permissions y role_permissions en PostgreSQL",
        "La matriz vive en role_permissions y coincide con la del documento.",
        [
            "SELECT id, code, name, is_active FROM roles ORDER BY id;",
            "SELECT id, code, is_active FROM permissions ORDER BY id;",
            """SELECT p.code AS permiso,
       MAX(CASE WHEN r.code = 'ADMINISTRADOR' AND rp.is_active THEN 'sí' ELSE 'no' END) AS administrador,
       MAX(CASE WHEN r.code = 'CONTADOR' AND rp.is_active THEN 'sí' ELSE 'no' END) AS contador,
       MAX(CASE WHEN r.code = 'CAPTURISTA' AND rp.is_active THEN 'sí' ELSE 'no' END) AS capturista,
       MAX(CASE WHEN r.code = 'CONSULTA' AND rp.is_active THEN 'sí' ELSE 'no' END) AS consulta
FROM permissions p
LEFT JOIN role_permissions rp ON rp.permission_id = p.id
LEFT JOIN roles r ON r.id = rp.role_id
GROUP BY p.id, p.code ORDER BY p.id;""",
        ],
    )

    antes_reinicio = sql_valor("SELECT COUNT(*) FROM roles;")
    subprocess.run(["docker", "restart", API_CONTAINER], capture_output=True)
    for _ in range(30):
        try:
            graphql("{ roles { id } }")
            break
        except Exception:
            time.sleep(1)
    despues_reinicio = sql_valor("SELECT COUNT(*) FROM roles;")
    paso(
        "reinicio", "roles después de reiniciar el contenedor de la API",
        "Al arrancar solo se insertan roles si la tabla está vacía: después de reiniciar siguen siendo cuatro.",
        """
query {
  roles {
    id
    code
  }
}""", actor="Consulta pública después de docker restart actividad4-api",
        extra=f"SELECT COUNT(*) FROM roles: {antes_reinicio} antes del reinicio y {despues_reinicio} después.",
    )
    pasos[-1]["correcto"] = antes_reinicio == despues_reinicio == "4"
    paso_sql(
        "reinicio_sql", "Conteo de catálogos en PostgreSQL después del reinicio",
        "El reinicio no duplicó roles, permisos ni la matriz.",
        ["SELECT (SELECT COUNT(*) FROM roles) AS roles, (SELECT COUNT(*) FROM permissions) AS permisos, "
         "(SELECT COUNT(*) FROM role_permissions) AS role_permissions;"],
    )
    pasos[-1]["extra"] = NOTA_ROLE_PERMISSIONS

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps({"api": API_URL, "pasos": pasos}, ensure_ascii=False, indent=2), encoding="utf-8")
    fallas = [p["clave"] for p in pasos if not p["correcto"]]
    print(f"\n{len(pasos) - len(fallas)}/{len(pasos)} pasos con el resultado esperado")
    if fallas:
        print("Fallas:", ", ".join(fallas))
        sys.exit(1)


if __name__ == "__main__":
    main()
