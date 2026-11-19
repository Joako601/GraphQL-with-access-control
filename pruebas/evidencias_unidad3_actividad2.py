r"""Unidad III, Actividad 2: capturas del dashboard administrativo y de la idempotencia en GraphiQL.

Requiere docker compose (API + PostgreSQL), los datos de unidad3_actividad2_datos.py, el dashboard en
http://localhost:5173 (cd dashboard && npm run dev) y Playwright (pip install -r pruebas/requirements.txt;
python -m playwright install chromium). Ejecutar desde la raíz:
    python pruebas/evidencias_unidad3_actividad2.py

Guarda las capturas en docs/Unidad3Actividad2/evidencias/ y el conteo SQL en sql_idempotencia.txt. Cada corrida
crea un usuario, una cuenta y un concepto con sufijo nuevo (los datos del equipo no se tocan).
"""
import json
import re
import urllib.parse
import uuid
from datetime import datetime
from pathlib import Path

import actividad6 as a6
import unidad3_actividad2_datos as equipo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Unidad3Actividad2" / "evidencias"
DASHBOARD = "http://localhost:5173/"
API = a6.API.replace("127.0.0.1", "localhost")
INTEGRANTES = "Equipo: Joaquín Uriona · Mateo Tec · Ariff Medina · Fernando Castro"
SUFIJO = uuid.uuid4().hex[:4]

BANDA = """([izquierda, derecha]) => {
  const banda = document.createElement('div');
  banda.id = 'banda-evidencia';
  banda.style.cssText = 'background:#1e3a4c;color:#fff;font:13px system-ui;padding:8px 18px;display:flex;' +
    'justify-content:space-between;gap:12px;flex-wrap:wrap';
  banda.innerHTML = '<b></b><span></span>';
  banda.children[0].textContent = izquierda;
  banda.children[1].textContent = derecha;
  document.getElementById('banda-evidencia')?.remove();
  document.body.prepend(banda);
  const lateral = document.querySelector('aside');
  if (lateral) lateral.style.height = `calc(100svh - ${banda.offsetHeight}px)`;
}"""


class Dashboard:
    def __init__(self, browser, nombre, viewport=None):
        self.nombre = nombre
        self.context = browser.new_context(viewport=viewport or {"width": 1440, "height": 900}, locale="es-MX",
                                            timezone_id="America/Mexico_City")
        self.page = self.context.new_page()
        self.page.goto(DASHBOARD)
        self.page.fill("#email", equipo.correo(nombre))
        self.page.fill("#password", a6.PASSWORD)
        self.page.get_by_role("button", name="Continuar").click()
        self.page.get_by_role("button", name="Cerrar sesión").wait_for()

    def ir(self, hash_, espera):
        self.page.goto(DASHBOARD + hash_)
        self.page.get_by_text(espera).first.wait_for()
        self.page.wait_for_load_state("networkidle")

    def captura(self, archivo, rol):
        self.page.evaluate(BANDA, [INTEGRANTES, f"Sesión: {self.nombre} ({rol}) · {datetime.now():%Y-%m-%d %H:%M}"])
        # Se agranda la ventana al alto del documento (no full_page): así la barra lateral sticky queda en su lugar.
        ancho = self.page.viewport_size["width"]
        alto = self.page.evaluate("document.documentElement.scrollHeight")
        self.page.set_viewport_size({"width": ancho, "height": max(alto, 600)})
        self.page.wait_for_timeout(300)
        self.page.screenshot(path=str(OUT / archivo))
        print("  ", archivo)

    def cerrar(self):
        self.context.close()


def usuarios(browser):
    d = Dashboard(browser, "Joaquín Uriona")
    p = d.page
    d.ir("#/admin/usuarios", "¿Quién pertenece a la empresa?")
    p.get_by_role("cell", name="Fernando Castro").wait_for()
    d.captura("01-usuarios.png", "ADMINISTRADOR")

    nombre, correo = f"Invitado Prueba {SUFIJO}", f"invitado.{SUFIJO}@equipo.test"
    p.get_by_role("button", name="Nuevo usuario").click()
    p.fill("#nu-name", nombre)
    p.fill("#nu-email", correo)
    p.fill("#nu-password", "secreto123")
    p.get_by_role("button", name="Guardar").click()
    p.get_by_role("cell", name=nombre).wait_for()
    d.captura("02-usuario-creado.png", "ADMINISTRADOR")

    # Mismo correo otra vez: el API lo rechaza y el mensaje se lee en el formulario.
    p.fill("#nu-name", "Otra persona")
    p.fill("#nu-email", correo)
    p.fill("#nu-password", "secreto123")
    p.get_by_role("button", name="Guardar").click()
    p.get_by_text("ya está registrado").wait_for()
    d.captura("03-error-correo-duplicado.png", "ADMINISTRADOR")

    fila = p.get_by_role("row").filter(has_text=correo)
    fila.get_by_role("button", name="Desactivar").click()
    p.get_by_text("deja de operar en la empresa").wait_for()
    d.captura("04-desactivar-confirmacion.png", "ADMINISTRADOR")
    p.get_by_role("button", name="Confirmar desactivación").click()
    fila.get_by_text("Inactivo").wait_for()
    p.get_by_role("button", name="Inactivos").click()
    d.captura("05-usuario-inactivo.png", "ADMINISTRADOR")
    d.cerrar()
    return correo


def cuentas(browser):
    d = Dashboard(browser, "Mateo Tec")  # CONTADOR: accounts.write y concepts.write
    p = d.page
    d.ir("#/admin/cuentas", "¿Dónde está el dinero?")
    p.get_by_role("cell", name="Caja").wait_for()
    d.captura("06-cuentas.png", "CONTADOR")

    cuenta = f"Inversión {SUFIJO}"
    p.get_by_role("button", name="Nueva cuenta").click()
    p.fill("#na-name", cuenta)
    p.select_option("#na-type", "INVESTMENT")
    p.fill("#na-bank", "GBM")
    p.fill("#na-desc", "Cuenta de inversión del equipo")
    p.get_by_role("button", name="Guardar").click()
    p.get_by_role("cell", name=re.compile(cuenta)).wait_for()
    d.captura("07-cuenta-creada.png", "CONTADOR")
    d.cerrar()
    return cuenta


def conceptos(browser, cuenta):
    d = Dashboard(browser, "Mateo Tec")
    p = d.page
    d.ir("#/admin/conceptos", "¿Por qué se mueve el dinero")
    p.get_by_text("Conceptos de la cuenta Banco").wait_for()
    p.locator("li").filter(has_text="Nómina").wait_for()
    d.captura("08-conceptos.png", "CONTADOR")

    concepto = f"Papelería {SUFIJO}"
    p.get_by_role("button", name="Nuevo concepto").click()
    p.fill("#nc-name", concepto)
    p.get_by_label("Egreso").check()
    p.fill("#nc-desc", "Compras de oficina")
    p.get_by_role("button", name="Guardar").click()
    p.get_by_role("cell", name=re.compile(concepto)).wait_for()

    p.select_option("#ac-account", label=cuenta)
    p.get_by_text(f"Conceptos de la cuenta {cuenta}").wait_for()
    p.select_option("#ac-concept", label=f"{concepto} · Egreso")
    p.get_by_role("button", name="Asignar concepto").click()
    p.locator("li").filter(has_text=concepto).wait_for()
    d.captura("09-concepto-asignado.png", "CONTADOR")

    p.select_option("#ac-concept", label=f"{concepto} · Egreso (ya asignado)")
    p.get_by_role("button", name="Asignar concepto").click()
    p.get_by_text("ya está asignado a la cuenta").wait_for()
    d.captura("10-error-concepto-ya-asignado.png", "CONTADOR")

    p.locator("li").filter(has_text=concepto).get_by_role("button", name="Quitar").click()
    p.get_by_text(f"La cuenta {cuenta} todavía no tiene conceptos asignados").wait_for()
    d.captura("11-concepto-quitado-sigue-en-catalogo.png", "CONTADOR")
    d.cerrar()


def solo_lectura(browser):
    d = Dashboard(browser, "Fernando Castro")  # CONSULTA: lee todo, no escribe nada
    d.ir("#/admin/usuarios", "¿Quién pertenece a la empresa?")
    d.page.get_by_role("cell", name="Mateo Tec").wait_for()
    d.captura("12-consulta-usuarios-sin-botones.png", "CONSULTA")
    d.ir("#/admin/cuentas", "¿Dónde está el dinero?")
    d.page.get_by_role("cell", name="Banco").wait_for()
    d.captura("13-consulta-cuentas-sin-botones.png", "CONSULTA")
    d.ir("#/admin/conceptos", "¿Por qué se mueve el dinero")
    d.page.get_by_text("Conceptos de la cuenta Banco").wait_for()
    d.page.locator("li").filter(has_text="Nómina").wait_for()
    d.captura("14-consulta-conceptos-sin-botones.png", "CONSULTA")
    d.cerrar()

    d = Dashboard(browser, "Ariff Medina")  # CAPTURISTA: sin company.users.read
    d.ir("#/admin/usuarios", "Acceso denegado")
    d.captura("15-capturista-usuarios-acceso-denegado.png", "CAPTURISTA")
    d.cerrar()


def navegacion(browser):
    d = Dashboard(browser, "Joaquín Uriona")
    d.ir("#/financiero", "Indicadores generales")
    d.captura("16-menu-dashboard-financiero.png", "ADMINISTRADOR")
    d.page.get_by_role("button", name="Cerrar sesión").click()
    d.page.locator("#email").wait_for()
    d.captura("17-cerrar-sesion-vuelve-al-login.png", "sin sesión")
    d.cerrar()

    d = Dashboard(browser, "Joaquín Uriona", viewport={"width": 390, "height": 844})
    d.ir("#/admin/usuarios", "¿Quién pertenece a la empresa?")
    d.page.locator("li").filter(has_text="Fernando Castro").wait_for()  # en móvil cada fila es una tarjeta
    d.captura("18-responsive-usuarios.png", "ADMINISTRADOR")
    d.cerrar()


CREATE_TX = """mutation RegistrarEgreso($input: CreateTransactionInput!) {
  createTransaction(input: $input) {
    id
    amount
    transactionType
    shortDescription
    account { name }
    concept { name }
  }
}"""


def graphiql(browser, token, variables, archivo, titulo):
    context = browser.new_context(viewport={"width": 1500, "height": 900})
    page = context.new_page()
    page.route(re.compile(re.escape(API) + r"(?:\?.*)?$"),
               lambda route: route.continue_(headers={**route.request.headers, "authorization": f"Bearer {token}"}))
    params = urllib.parse.urlencode({"q": CREATE_TX, "variables": json.dumps(variables, indent=2)},
                                    quote_via=urllib.parse.quote)
    page.goto(f"{API}?{params}", wait_until="networkidle", timeout=60000)
    boton = page.locator(".graphiql-execute-button")
    boton.wait_for(timeout=45000)
    with page.expect_response(lambda r: r.request.method == "POST" and r.url == API, timeout=30000) as respuesta:
        boton.click()
    payload = respuesta.value.json()
    page.evaluate(BANDA, [f"{titulo} · {INTEGRANTES}",
                          f"Authorization: Bearer {token[:14]}… · Ariff Medina (CAPTURISTA) · {datetime.now():%H:%M:%S}"])
    page.evaluate("document.getElementById('graphiql').style.height = 'calc(100vh - 36px)'")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / archivo))
    print("  ", archivo)
    context.close()
    return payload["data"]["createTransaction"]["id"]


def idempotencia(browser):
    token = equipo.login("Ariff Medina")
    q = "query($c: ID!) { accounts(companyId: $c) { id name } concepts(companyId: $c) { id name } }"
    me = a6.gql("{ me { companyId } }", token=token)["data"]["me"]
    datos = a6.gql(q, {"c": me["companyId"]}, token)["data"]
    banco = next(a["id"] for a in datos["accounts"] if a["name"] == "Banco")
    renta = next(c["id"] for c in datos["concepts"] if c["name"] == "Renta")
    llave = f"renta-nov-{SUFIJO}"

    def variables(k):
        return {"input": {"idempotencyKey": k, "accountId": banco, "conceptId": renta, "transactionType": "EXPENSE",
                          "amount": "100.00", "shortDescription": "Renta de noviembre"}}

    filas = f"SELECT COUNT(*) FROM transactions WHERE company_id = {int(me['companyId'])};"
    antes = a6.sql(filas)
    uno = graphiql(browser, token, variables(llave), "19-graphiql-idempotencia-envio-1.png", "Envío 1 · llave " + llave)
    dos = graphiql(browser, token, variables(llave), "20-graphiql-idempotencia-envio-2-misma-llave.png",
                   "Envío 2 (reintento) · misma llave " + llave)
    otra = f"renta-nov-{SUFIJO}-b"
    tres = graphiql(browser, token, variables(otra), "21-graphiql-otra-llave-otro-movimiento.png",
                    "Envío 3 · otra llave " + otra)
    despues = a6.sql(filas)
    sql_llave = a6.sql(f"""SELECT k.idempotency_key || ' -> transaction ' || t.id || ' (' || t.amount || ')'
        FROM idempotency_keys k JOIN transactions t ON t.id = k.transaction_id
        WHERE k.idempotency_key IN ('{llave}', '{otra}') ORDER BY t.id;""")
    texto = (f"Llave {llave}: envío 1 -> id {uno}, envío 2 -> id {dos} (mismo id: {uno == dos})\n"
             f"Llave {otra}: envío 3 -> id {tres} (otro movimiento: {tres != uno})\n"
             f"Movimientos de la empresa: {antes} antes, {despues} después (+{int(despues) - int(antes)})\n\n"
             f"SELECT de idempotency_keys JOIN transactions:\n{sql_llave}\n")
    (OUT / "sql_idempotencia.txt").write_text(texto, encoding="utf-8")
    print(texto)
    return uno == dos and tres != uno and int(despues) - int(antes) == 2


def main():
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    for vieja in OUT.glob("*.png"):
        vieja.unlink()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        print("Usuarios");  usuarios(browser)
        print("Cuentas");   cuenta = cuentas(browser)
        print("Conceptos"); conceptos(browser, cuenta)
        print("Permisos");  solo_lectura(browser)
        print("Navegación"); navegacion(browser)
        print("Idempotencia"); ok = idempotencia(browser)
        browser.close()
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
