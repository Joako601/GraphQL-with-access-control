"""Unidad II, Actividad 7: preparación del conjunto de datos verificable por GraphQL.

Cada llamada a preparar() crea empresas nuevas con un sufijo aleatorio: la empresa A recibe Banco, Caja,
Ahorro y los seis movimientos del PDF; B, C, D y E aíslan los casos que modifican datos. Por eso no hace
falta restaurar la base entre ejecuciones. Usa los helpers de login y empresa de la actividad 6.
"""
import json
import urllib.error

import actividad6 as a6
from actividad6 import RUN, empresa, login, ok

P, F, T = "2026-10-", "2026-10-26", "2026-10-30"
# Varias líneas para que la operación completa se lea en las capturas de GraphiQL.
CAMPOS = """accountId
    accountName
    isActive
    openingBalance
    totalIncome
    totalExpense
    profit
    closingBalance
    isInRed"""
ACCOUNT_BALANCE = f"""query BalanceDeUnaCuenta($a: ID!, $f: Date!, $t: Date!) {{
  accountBalance(accountId: $a, fromDate: $f, toDate: $t) {{
    {CAMPOS}
  }}
}}"""
GENERAL_BALANCE = """query BalanceDeLaEmpresa($f: Date!, $t: Date!) {
  generalBalance(fromDate: $f, toDate: $t) {
    companyId
    currency
    fromDate
    toDate
    openingBalance
    totalIncome
    totalExpense
    profit
    closingBalance
    isInRed
    accountsInRed
    accounts {
      accountId
      accountName
      isActive
      openingBalance
      totalIncome
      totalExpense
      profit
      closingBalance
      isInRed
    }
  }
}"""
CREATE_TX = """mutation($a: ID!, $c: ID!, $t: TransactionType!, $m: Decimal!, $d: Time, $s: String) {
  createTransaction(input: {accountId: $a, conceptId: $c, transactionType: $t, amount: $m,
  transactionDate: $d, shortDescription: $s}) { id amount transactionDate capturedAt } }"""

# Movimientos del PDF; todos a las 12:00:00Z. El ingreso del 25 se registra una sola vez.
DATOS = [
    ("Banco", "25", "INCOME", "1000.00", "Ingreso de apertura"),
    ("Banco", "26", "INCOME", "3000.00", "Cobro de servicios"),
    ("Banco", "27", "EXPENSE", "1200.00", "Pago de renta"),
    ("Banco", "28", "EXPENSE", "1000.00", "Compra de materiales"),
    ("Caja", "26", "INCOME", "500.00", "Venta de contado"),
    ("Caja", "29", "EXPENSE", "700.00", "Pago de insumos"),
]
CUENTAS = ("Banco", "Caja", "Ahorro")

# Resultado esperado del 26 al 30, calculado a mano a partir de DATOS (no con el servicio de balances).
N = ("openingBalance", "totalIncome", "totalExpense", "profit", "closingBalance", "isInRed")
ESPERADO = {
    "Banco": dict(zip(N, ("1000.00", "3000.00", "2200.00", "800.00", "1800.00", False))),
    "Caja": dict(zip(N, ("0.00", "500.00", "700.00", "-200.00", "-200.00", True))),
    "Ahorro": dict(zip(N, ("0.00", "0.00", "0.00", "0.00", "0.00", False))),
}
GENERAL = {"currency": "MXN", **dict(zip(N, ("1000.00", "3500.00", "2900.00", "600.00", "1600.00", False))),
           "accountsInRed": 1}
CEROS = {**dict(zip(N, ("0.00",) * 5 + (False,))), "accountsInRed": 0, "accounts": []}


def gql(query, variables=None, token=None):
    try:
        return a6.gql(query, variables, token)
    except urllib.error.HTTPError as error:  # una variable inválida puede llegar como 400 con el error en el cuerpo
        return json.loads(error.read())


def utc(dia, hora="12:00:00"):
    return f"{P}{dia}T{hora}Z"


def conceptos(token, company):
    q = """mutation($c: ID!, $t: ConceptType!, $n: String!) {
      createConcept(input: {companyId: $c, conceptType: $t, name: $n}) { id } }"""
    return {t: ok(gql(q, {"c": company, "t": t, "n": f"{t.title()} {RUN}"}, token), "createConcept")["id"]
            for t in ("INCOME", "EXPENSE")}


def asignar(token, cuenta_id, concepto_id):
    q = "mutation($a: ID!, $c: ID!) { assignConceptToAccount(input: {accountId: $a, conceptId: $c}) { id } }"
    ok(gql(q, {"a": cuenta_id, "c": concepto_id}, token), "assignConceptToAccount")


def cuenta(token, company, concs, nombre):
    q = "mutation($c: ID!, $n: String!) { createAccount(input: {companyId: $c, accountType: CASH, name: $n}) { id } }"
    cuenta_id = ok(gql(q, {"c": company, "n": nombre}, token), "createAccount")["id"]
    for concepto_id in concs.values():
        asignar(token, cuenta_id, concepto_id)
    return cuenta_id


def mov(token, concs, cuenta_id, tipo, monto, fecha, desc=None):
    variables = {"a": cuenta_id, "c": concs[tipo], "t": tipo, "m": monto, "d": fecha, "s": desc}
    return ok(gql(CREATE_TX, variables, token), "createTransaction")


# Las operaciones que se muestran como evidencia pasan por aquí; evidencias_actividad7.py lo sustituye
# por un ejecutor que corre la misma operación en GraphiQL y guarda la captura en CAPTURAS.
ejecutar = gql
CAPTURAS = []
NOMBRES = {}  # token -> persona, solo para rotular capturas


def balance(token, cuenta_id, f=F, t=T):
    return ejecutar(ACCOUNT_BALANCE, {"a": cuenta_id, "f": f, "t": t}, token)


def general(token, f=F, t=T):
    return ejecutar(GENERAL_BALANCE, {"f": f, "t": t}, token)


def usuario(token_admin, company, nombre, role_id):
    q = """mutation($c: ID!, $n: String!, $e: String!, $p: String!, $r: ID!) {
      createCompanyUser(input: {companyId: $c, name: $n, email: $e, password: $p, roleId: $r}) { id } }"""
    variables = {"c": company, "n": nombre, "e": a6.correo(nombre), "p": a6.PASSWORD, "r": role_id}
    ok(gql(q, variables, token_admin), "createCompanyUser")
    token = login(nombre)
    NOMBRES[token] = nombre
    return token


def preparar():
    roles = {r["code"]: r["id"] for r in ok(gql("{ roles { id code } }"), "roles")}
    s = {"A": empresa(f"Balances {RUN}", "Ana"), "B": empresa(f"Ajena {RUN}", "Beto"),
         "C": empresa(f"Sin cuentas {RUN}", "Carla"), "D": empresa(f"Casos {RUN}", "Dani"),
         "E": empresa(f"Rojo {RUN}", "Eva"), "roles": roles}
    s["t"] = {n: login(n) for n in ("Ana", "Beto", "Carla", "Dani", "Eva")}
    s["t"]["Pedro"] = usuario(s["t"]["Ana"], s["A"], "Pedro", roles["CONSULTA"])

    s["cA"] = conceptos(s["t"]["Ana"], s["A"])
    s["cuentas"] = {n: cuenta(s["t"]["Ana"], s["A"], s["cA"], n) for n in CUENTAS}
    for nombre, dia, tipo, monto, desc in DATOS:
        mov(s["t"]["Ana"], s["cA"], s["cuentas"][nombre], tipo, monto, utc(dia), desc)

    concs_b = conceptos(s["t"]["Beto"], s["B"])
    s["ajena"] = cuenta(s["t"]["Beto"], s["B"], concs_b, "Banco B")
    mov(s["t"]["Beto"], concs_b, s["ajena"], "INCOME", "9999.99", utc("27"), "Dato privado de B")
    s["cD"], s["cE"] = conceptos(s["t"]["Dani"], s["D"]), conceptos(s["t"]["Eva"], s["E"])
    return s
