"""Comprueba la actividad y toma capturas con el API y la base de laboratorio."""

import json
import os
from pathlib import Path
from urllib.parse import quote, urlencode
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright

from actividad6 import API, PASSWORD, gql, ok
from unidad3_actividad2_datos import correo, login, preparar

DASHBOARD = os.getenv("DASHBOARD_URL", "http://127.0.0.1:5173")
OUT = Path(__file__).resolve().parents[1] / "docs" / "Unidad3Actividad3" / "evidencias"
ROLES = ("ADMINISTRADOR", "CONTADOR", "CAPTURISTA", "CONSULTA")
MATRIX = {
    "company.users.read": (True, True, False, True),
    "company.users.write": (True, False, False, False),
    "accounts.read": (True, True, True, True),
    "accounts.write": (True, True, False, False),
    "concepts.read": (True, True, True, True),
    "concepts.write": (True, True, False, False),
    "transactions.read": (True, True, True, True),
    "transactions.write": (True, True, True, False),
    "roles.read": (True, True, False, False),
    "roles.write": (True, False, False, False),
}
COLUMN = """query Capturista($roleId: ID!) {
  rolePermissions(roleId: $roleId) {
    isActive
    permission { id code }
  }
}"""
SAVE = """mutation($input: SetRolePermissionsInput!) {
  setRolePermissions(input: $input) { changed }
}"""
ASSIGN = """mutation($input: AssignRoleInput!) {
  assignRole(input: $input) { role { code } }
}"""
MY_ROLE = "{ me { companyId companyUserId isAdmin role { code } permissions } }"

def request(query, field, token, variables=None):
    return ok(gql(query, variables, token), field)


def open_dashboard(browser, name):
    page = browser.new_page(viewport={"width": 1440, "height": 960}, locale="es-MX")
    page.goto(DASHBOARD)
    page.locator("#email").fill(correo(name))
    page.locator("#password").fill(PASSWORD)
    page.get_by_role("button", name="Continuar").click()
    page.get_by_role("button", name="Cerrar sesión").wait_for()
    return page


def capture(page, name):
    page.screenshot(path=OUT / f"{name}.png", full_page=True, animations="disabled")
    print(name, flush=True)


def graphiql(browser, token, role_id, expected):
    page = browser.new_page(viewport={"width": 1440, "height": 820})
    page.route(f"{API}*", lambda route: route.continue_(headers={
        **route.request.headers, "authorization": f"Bearer {token}",
    }))
    params = urlencode({"q": COLUMN, "variables": json.dumps({"roleId": role_id})}, quote_via=quote)
    page.goto(f"{API}?{params}")
    with page.expect_response(lambda r: r.url == API and "query Capturista" in (r.request.post_data or "")) as response:
        page.locator(".graphiql-execute-button").click()
    rows = ok(response.value.json(), "rolePermissions")
    assert {row["permission"]["code"] for row in rows if row["isActive"]} == expected
    expect(page.locator(".graphiql-response")).to_contain_text("transactions.write")
    capture(page, "02-graphiql-capturista")
    page.context.close()


def check_initial_matrix(page):
    table = page.get_by_role("table", name="Matriz de roles y permisos")
    expect(table).to_be_visible()
    headers = table.get_by_role("columnheader").all_text_contents()
    assert all(code in header for code, header in zip(ROLES, headers[1:], strict=True))
    rows = table.locator('tr:has(th[scope="row"])')
    expect(rows).to_have_count(10)
    for row, (permission, expected) in zip(rows.all(), MATRIX.items(), strict=True):
        expect(row.get_by_role("rowheader")).to_contain_text(permission)
        expect(row.get_by_role("cell")).to_have_text(["Sí" if value else "No" for value in expected])
    expect(table.get_by_role("checkbox")).to_have_count(30)


def capture_flows(browser, tokens, roles, original, transaction):
    admin = open_dashboard(browser, "Joaquín Uriona")
    admin.get_by_role("link", name="Roles y permisos").click()
    check_initial_matrix(admin)
    capture(admin, "01-matriz-inicial")
    graphiql(browser, tokens["admin"], roles["CAPTURISTA"], {code for code, cells in MATRIX.items() if cells[2]})

    capturista = open_dashboard(browser, "Ariff Medina")
    capturista.get_by_role("link", name="Cuentas", exact=True).click()
    expect(capturista.get_by_role("row").filter(has_text="Caja")).to_be_visible()
    expect(capturista.get_by_role("button", name="Nueva cuenta")).to_have_count(0)
    capture(capturista, "04a-cuentas-antes")

    admin.get_by_role("checkbox", name="Capturista · Crear cuentas").check()
    expect(admin.get_by_role("button", name="Guardar columna")).to_be_disabled()
    admin.get_by_role("button", name="Vista previa").click()
    plan = admin.locator('dl[aria-label="Vista previa"]')
    expect(plan.locator("dd")).to_have_text(["accounts.write", "Ninguno", "4", "5"])
    capture(admin, "03-vista-previa")
    admin.get_by_role("button", name="Guardar columna").click()
    expect(admin.get_by_role("status").filter(has_text="changed: true")).to_be_visible()
    col = request(COLUMN, "rolePermissions", tokens["admin"], {"roleId": roles["CAPTURISTA"]})
    assert any(row["isActive"] and row["permission"]["code"] == "accounts.write" for row in col)
    capturista.reload()
    expect(capturista.get_by_role("button", name="Nueva cuenta")).to_be_visible()
    capture(capturista, "04b-cuentas-despues")

    admin.get_by_role("button", name="Editar Capturista").click()
    admin.get_by_role("button", name="Vista previa").click()
    expect(plan.locator("dd")).to_have_text(["Ninguno", "Ninguno", "5", "5"])
    admin.get_by_role("button", name="Guardar columna").click()
    expect(admin.get_by_role("status").filter(has_text="changed: false")).to_be_visible()
    expect(admin.get_by_role("button", name="Editar Capturista")).to_be_enabled()
    capture(admin, "06-guardado-sin-cambios")

    admin.get_by_role("link", name="Usuarios", exact=True).click()
    row = admin.get_by_role("row").filter(has_text="Fernando Castro")
    expect(row.get_by_role("cell").nth(2)).to_contain_text("Consulta")
    row.get_by_role("combobox", name="Rol de Fernando Castro").select_option(label="Capturista")
    row.get_by_role("button", name="Guardar rol").click()
    expect(row.get_by_role("cell").nth(2).locator("p").first).to_have_text("Capturista")
    expect(row.get_by_role("cell").nth(3)).to_have_text("No")
    capture(admin, "05a-usuario-reasignado")
    me = request(MY_ROLE, "me", tokens["consulta"])
    assert me["role"]["code"] == "CAPTURISTA" and not me["isAdmin"] and "accounts.write" in me["permissions"]
    assert request(transaction[0], "createTransaction", tokens["consulta"], transaction[1])["id"]
    admin.get_by_role("link", name="Roles y permisos").click()
    table = admin.get_by_role("table", name="Matriz de roles y permisos")
    expect(table.locator('tr:has(th[scope="row"]) td:last-child')).to_have_text(
        ["Sí" if cells[3] else "No" for cells in MATRIX.values()]
    )
    assert request(COLUMN, "rolePermissions", tokens["admin"], {"roleId": roles["CONSULTA"]}) == original
    capture(admin, "05b-columna-consulta")

    contador = open_dashboard(browser, "Mateo Tec")
    contador.get_by_role("link", name="Roles y permisos").click()
    expect(contador.get_by_text("Solo lectura. Se requiere roles.write para guardar.")).to_be_visible()
    expect(contador.get_by_role("checkbox")).to_have_count(0)
    expect(contador.get_by_role("button", name="Guardar columna")).to_have_count(0)
    capture(contador, "07-contador-solo-lectura")
    expect(capturista.get_by_role("link", name="Roles y permisos")).to_have_count(0)
    capturista.goto(f"{DASHBOARD}/#/admin/roles")
    expect(capturista.get_by_role("heading", name="Acceso denegado")).to_be_visible()


def main():
    expect.set_options(timeout=25000)
    preparar()
    OUT.mkdir(parents=True, exist_ok=True)
    tokens = {key: login(name) for key, name in [
        ("admin", "Joaquín Uriona"), ("consulta", "Fernando Castro"),
        ("capturista", "Ariff Medina"), ("contador", "Mateo Tec"),
    ]}
    actor = tokens["admin"]
    roles = {role["code"]: role["id"] for role in request("{ roles { id code } }", "roles", actor)}
    consulta = request(MY_ROLE, "me", tokens["consulta"])
    assert consulta["role"]["code"] == "CONSULTA", "Fernando debe iniciar como Consulta"
    original = request(COLUMN, "rolePermissions", actor, {"roleId": roles["CONSULTA"]})
    capt = request(COLUMN, "rolePermissions", actor, {"roleId": roles["CAPTURISTA"]})
    reset = {"input": {"roleId": roles["CAPTURISTA"], "permissionIds": [row["permission"]["id"] for row in capt]}}
    assert "Falta el token" in gql("{ roles { id } }")["errors"][0]["message"]
    for token in (tokens["capturista"], tokens["consulta"]):
        assert "roles.read" in gql(COLUMN, {"roleId": roles["CAPTURISTA"]}, token)["errors"][0]["message"]
        assert "roles.read" in gql("{ roles { id } }", token=token)["errors"][0]["message"]
        assert "roles.read" in gql("{ permissions { id } }", token=token)["errors"][0]["message"]
    assert "roles.write" in gql(SAVE, reset, tokens["contador"])["errors"][0]["message"]

    company = {"companyId": consulta["companyId"]}
    data = "{ accounts(companyId: $companyId) { id name } concepts(companyId: $companyId) { id name } }"
    data = gql("query($companyId: ID!) " + data, company, actor)["data"]
    transaction = ("""mutation($input: CreateTransactionInput!) {
      createTransaction(input: $input) { id }
    }""", {"input": {
        "accountId": next(row["id"] for row in data["accounts"] if row["name"] == "Caja"),
        "conceptId": next(row["id"] for row in data["concepts"] if row["name"] == "Ventas"),
        "transactionType": "INCOME", "amount": "1.00", "idempotencyKey": uuid4().hex,
    }})
    assert "transactions.write" in gql(*transaction, tokens["consulta"])["errors"][0]["message"]
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel=os.getenv("PLAYWRIGHT_CHANNEL") or None)
            capture_flows(browser, tokens, roles, original, transaction)
    finally:
        request(SAVE, "setRolePermissions", actor, reset)
        if request(MY_ROLE, "me", tokens["consulta"])["role"]["code"] == "CAPTURISTA":
            request(ASSIGN, "assignRole", actor, {"input": {
                "companyUserId": consulta["companyUserId"], "roleId": roles["CONSULTA"],
            }})
if __name__ == "__main__":
    main()
