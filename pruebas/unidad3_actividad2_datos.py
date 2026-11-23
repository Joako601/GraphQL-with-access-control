r"""Unidad III, Actividad 2: datos del equipo para el dashboard administrativo.

Idempotente: si Joaquín ya puede iniciar sesión, no crea nada. Requiere la API de docker compose.
Ejecutar desde la raíz:
    python pruebas/unidad3_actividad2_datos.py

Empresa "Sistema General de Ingresos - Equipo", contraseña de todos: secreto123 (solo laboratorio).
    joaquin.uriona@equipo.test   ADMINISTRADOR (administrador principal)  escribe usuarios, cuentas y conceptos
    mateo.tec@equipo.test        CONTADOR                                 escribe cuentas y conceptos, lee usuarios
    ariff.medina@equipo.test     CAPTURISTA                               captura movimientos (idempotencia)
    fernando.castro@equipo.test  CONSULTA                                 solo lectura: no ve botones de alta
"""
import actividad6 as a6
import actividad7_datos as d

EMPRESA = "Sistema General de Ingresos - Equipo"
DOMINIO = "equipo.test"

# (nombre, rol); el primero nace con createCompanyAdmin.
EQUIPO = [
    ("Joaquín Uriona", "ADMINISTRADOR"),
    ("Mateo Tec", "CONTADOR"),
    ("Ariff Medina", "CAPTURISTA"),
    ("Fernando Castro", "CONSULTA"),
]
# (nombre, tipo, banco, CLABE, descripción corta)
CUENTAS = [
    ("Banco", "DEBIT", "BBVA", "012180001234561234", "Cuenta de cheques principal"),
    ("Caja", "CASH", None, None, "Efectivo de la oficina"),
    ("Ahorro", "SAVINGS", "Banorte", "072180009876547788", "Fondo de reserva"),
]
CONCEPTOS = [
    ("Ventas", "INCOME", "Cobro a clientes"),
    ("Nómina", "EXPENSE", "Pago quincenal"),
    ("Renta", "EXPENSE", "Renta de la oficina"),
    ("Intereses", "INCOME", "Rendimiento del ahorro"),
]
ASIGNACIONES = {"Banco": ["Ventas", "Nómina", "Renta"], "Caja": ["Ventas"], "Ahorro": ["Intereses"]}

LOGIN = "mutation($e: String!, $p: String!) { login(input: {email: $e, password: $p}) { token } }"


def correo(nombre):
    simple = nombre.lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o")
    return simple.replace(" ", ".") + "@" + DOMINIO


def login(nombre):
    r = d.gql(LOGIN, {"e": correo(nombre), "p": a6.PASSWORD})
    return None if r.get("errors") else r["data"]["login"]["token"]


def preparar():
    admin = EQUIPO[0][0]
    if login(admin):
        print(f"{EMPRESA} ya existe; no se crea nada.")
        return
    company = a6.ok(d.gql('mutation($n: String!) { createCompany(input: {name: $n}) { id } }', {"n": EMPRESA}),
                    "createCompany")["id"]
    a6.ok(d.gql("""mutation($c: ID!, $n: String!, $e: String!, $p: String!) {
      createCompanyAdmin(input: {companyId: $c, name: $n, email: $e, password: $p}) { id } }""",
                {"c": company, "n": admin, "e": correo(admin), "p": a6.PASSWORD}), "createCompanyAdmin")
    token = login(admin)

    roles = {r["code"]: r["id"] for r in a6.ok(d.gql("{ roles { id code } }", token=token), "roles")}
    q = """mutation($c: ID!, $n: String!, $e: String!, $p: String!, $r: ID!) {
      createCompanyUser(input: {companyId: $c, name: $n, email: $e, password: $p, roleId: $r}) { id } }"""
    for nombre, rol in EQUIPO[1:]:
        a6.ok(d.gql(q, {"c": company, "n": nombre, "e": correo(nombre), "p": a6.PASSWORD, "r": roles[rol]}, token),
              "createCompanyUser")

    q = """mutation($i: CreateAccountInput!) { createAccount(input: $i) { id } }"""
    cuentas = {}
    for nombre, tipo, banco, clabe, desc in CUENTAS:
        datos = {"companyId": company, "accountType": tipo, "name": nombre, "bankName": banco, "clabe": clabe,
                 "shortDescription": desc}
        cuentas[nombre] = a6.ok(d.gql(q, {"i": datos}, token), "createAccount")["id"]

    q = """mutation($i: CreateConceptInput!) { createConcept(input: $i) { id } }"""
    conceptos = {}
    for nombre, tipo, desc in CONCEPTOS:
        datos = {"companyId": company, "conceptType": tipo, "name": nombre, "shortDescription": desc}
        conceptos[nombre] = a6.ok(d.gql(q, {"i": datos}, token), "createConcept")["id"]

    for cuenta, nombres in ASIGNACIONES.items():
        for nombre in nombres:
            d.asignar(token, cuentas[cuenta], conceptos[nombre])

    print(f"{EMPRESA} creada (companyId {company}). Usuarios: "
          + ", ".join(f"{correo(n)} ({r})" for n, r in EQUIPO) + f" / {a6.PASSWORD}")


if __name__ == "__main__":
    preparar()
