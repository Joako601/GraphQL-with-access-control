r"""Unidad II, Actividad 6: casos 1 a 9 del control de acceso con JWT.

Requiere la API y PostgreSQL de docker compose. Ejecutar desde la raíz:
    python pruebas/actividad6.py
Crea dos empresas nuevas en cada ejecución. Guarda docs/Actividad6/evidencias.json
sin tokens completos ni el secreto.
"""
import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = os.getenv("API_URL", "http://127.0.0.1:8004/graphql")
DB = "unidad2-actividad4-postgres"
PASSWORD = "secreto123"
RUN = uuid.uuid4().hex[:6]


def gql(query, variables=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    request = urllib.request.Request(API, body, headers)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())


def ok(response, field):
    if response.get("errors"):
        raise RuntimeError(response["errors"][0]["message"])
    return response["data"][field]


def sql(query):
    env = {k: v for k, v in leer_env().items() if k.startswith("POSTGRES_")}
    cmd = ["docker", "exec", DB, "psql", "-U", env["POSTGRES_USER"], "-d", env["POSTGRES_DB"], "-tAc", query]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def leer_env():
    lines = (ROOT / ".env").read_text(encoding="utf-8").splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def payload(token):
    part = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))


def token_vencido(token):
    # Simula un token de 30 minutos que ya pasó: mismos datos y firma válida, exp en el pasado.
    datos = {**payload(token), "exp": int(time.time()) - 60}
    head = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64(json.dumps(datos).encode())
    firma = hmac.new(leer_env()["JWT_SECRET"].encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{b64(firma)}"


def token_alterado(token):
    head, body, firma = token.split(".")
    return f"{head}.{body}.{firma[:-2]}{'A' if firma[-2] != 'A' else 'B'}{firma[-1]}"


LOGIN = """mutation($e: String!, $p: String!) { login(input: {email: $e, password: $p}) {
  tokenType token user { name } } }"""
CREATE_ACCOUNT = """mutation($c: ID!, $n: String!) { createAccount(input: {companyId: $c, accountType: CASH, name: $n}) {
  id name } }"""
CREATE_TX = """mutation($a: ID!, $c: ID!) { createTransaction(input: {accountId: $a, conceptId: $c,
  transactionType: INCOME, amount: "100.00"}) { id amount } }"""
ASSIGN_ROLE = """mutation($m: ID!, $r: ID!) { assignRole(input: {companyUserId: $m, roleId: $r}) {
  id role { code } } }"""
ACCOUNTS = "query($c: ID!) { accounts(companyId: $c) { id name } }"


def empresa(nombre, admin):
    company = ok(gql('mutation($n: String!) { createCompany(input: {name: $n}) { id } }', {"n": nombre}), "createCompany")
    gql("""mutation($c: ID!, $n: String!, $e: String!, $p: String!) {
      createCompanyAdmin(input: {companyId: $c, name: $n, email: $e, password: $p}) { id } }""",
        {"c": company["id"], "n": admin, "e": correo(admin), "p": PASSWORD})
    return company["id"]


def correo(nombre):
    return f"{nombre.lower()}.{RUN}@empresa.test"


def login(nombre):
    return ok(gql(LOGIN, {"e": correo(nombre), "p": PASSWORD}), "login")["token"]


def preparar():
    roles = {r["code"]: r["id"] for r in ok(gql("{ roles { id code } }"), "roles")}
    c1, c2 = empresa(f"Ingresos {RUN}", "Ana"), empresa(f"Otra {RUN}", "Beto")
    ana = login("Ana")
    ids = {}
    for nombre, rol in (("Maria", "CAPTURISTA"), ("Luis", "CONTADOR"), ("Pedro", "CONSULTA")):
        r = gql("""mutation($c: ID!, $n: String!, $e: String!, $p: String!, $r: ID!) {
          createCompanyUser(input: {companyId: $c, name: $n, email: $e, password: $p, roleId: $r}) { id } }""",
                {"c": c1, "n": nombre, "e": correo(nombre), "p": PASSWORD, "r": roles[rol]}, ana)
        ids[nombre] = ok(r, "createCompanyUser")["id"]
    cuenta = ok(gql(CREATE_ACCOUNT, {"c": c1, "n": "Caja"}, ana), "createAccount")["id"]
    concepto = ok(gql('mutation($c: ID!) { createConcept(input: {companyId: $c, conceptType: INCOME, name: "Ventas"}) { id } }',
                      {"c": c1}, ana), "createConcept")["id"]
    ok(gql("mutation($a: ID!, $c: ID!) { assignConceptToAccount(input: {accountId: $a, conceptId: $c}) { id } }",
           {"a": cuenta, "c": concepto}, ana), "assignConceptToAccount")
    tokens = {n: login(n) for n in ("Ana", "Maria", "Luis", "Pedro", "Beto")}
    return {"c1": c1, "roles": roles, "ids": ids, "cuenta": cuenta, "concepto": concepto, "tokens": tokens}


def main():
    s = preparar()
    t, c1 = s["tokens"], s["c1"]
    tx_vars = {"a": s["cuenta"], "c": s["concepto"]}
    contar_cuentas = f"SELECT COUNT(*) FROM accounts WHERE company_id = {int(c1)};"
    contar_tx = f"SELECT COUNT(*) FROM transactions WHERE company_id = {int(c1)};"
    casos = [
        (1, "Ninguno", None, CREATE_ACCOUNT, {"c": c1, "n": "Sin token"}, contar_cuentas, False),
        (2, "Maria, capturista", t["Maria"], CREATE_TX, tx_vars, contar_tx, True),
        (3, "Maria, capturista", t["Maria"], CREATE_ACCOUNT, {"c": c1, "n": "De Maria"}, contar_cuentas, False),
        (4, "Luis, contador", t["Luis"], CREATE_ACCOUNT, {"c": c1, "n": "De Luis"}, contar_cuentas, True),
        (5, "Pedro, consulta", t["Pedro"], CREATE_TX, tx_vars, contar_tx, False),
        (6, "Ana", t["Ana"], ASSIGN_ROLE, {"m": s["ids"]["Pedro"], "r": s["roles"]["CAPTURISTA"]}, None, True),
        (7, "El mismo token de Pedro", t["Pedro"], CREATE_TX, tx_vars, contar_tx, True),
        (8, "Beto, otra empresa", t["Beto"], ACCOUNTS, {"c": c1}, None, False),
        ("9a", "Token alterado", token_alterado(t["Luis"]), CREATE_ACCOUNT, {"c": c1, "n": "Alterado"}, contar_cuentas, False),
        ("9b", "Token vencido", token_vencido(t["Luis"]), CREATE_ACCOUNT, {"c": c1, "n": "Vencido"}, contar_cuentas, False),
    ]
    rechazo = gql(LOGIN, {"e": correo("Maria"), "p": "incorrecta"})
    evidencias = {
        "login_correcto_payload": payload(t["Maria"]),
        "login_rechazado": {"data": rechazo.get("data"), "errors": [e["message"] for e in rechazo.get("errors", [])]},
        "casos": [],
    }
    fallos = 0
    for caso, quien, token, query, variables, conteo, debe_pasar in casos:
        antes = sql(conteo) if conteo else None
        r = gql(query, variables, token)
        despues = sql(conteo) if conteo else None
        paso = not r.get("errors")
        fallos += paso != debe_pasar
        evidencias["casos"].append({
            "caso": caso, "token": quien,
            "header": f"Authorization: Bearer {token[:16]}..." if token else "(sin encabezado)",
            "esperado": "se guarda" if debe_pasar else "se rechaza", "obtenido": "se guarda" if paso else "se rechaza",
            "error": r["errors"][0]["message"] if r.get("errors") else None,
            "filas_antes": antes, "filas_despues": despues,
        })
        print(f"Caso {caso:<3} {quien:<24} {'OK ' if paso == debe_pasar else 'MAL'} "
              f"{'guardado' if paso else r['errors'][0]['message']} {'' if antes is None else f'[{antes} -> {despues}]'}")
    out = ROOT / "docs" / "Actividad6" / "evidencias.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidencias, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Evidencia: {out.relative_to(ROOT)}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
