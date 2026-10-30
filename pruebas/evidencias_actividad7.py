r"""Unidad II, Actividad 7: corre B01-B15 en GraphiQL real, guarda una captura por operación y arma el PDF.

Requiere la API de docker compose y Playwright (pip install playwright==1.64.0; python -m playwright install chromium).
Antes, guarda la salida de las pruebas unitarias para que entre al PDF:
    python -m unittest pruebas.test_actividad7_balances -v 2> docs/Actividad7/evidencias/salida_unittest.txt
    python pruebas/evidencias_actividad7.py
El token se inyecta solo en la petición al endpoint local; en la captura aparece recortado.
"""
import base64
import html
import json
import re
import sys
import urllib.parse
from datetime import datetime

import actividad7
import actividad7_datos as datos
from actividad6 import API
from actividad7_datos import preparar

EQUIPO = ("Ariff Medina", "Joaquín Uriona", "Mateo Martin", "Fernando Castro")
EVIDENCIAS = actividad7.DOCS / "evidencias"
CAPTURAS = EVIDENCIAS / "capturas"
PDF = actividad7.DOCS / "Evidencias Unidad II Actividad 7 - Balances.pdf"
REGLAS = {
    "B01": "El saldo inicial sale de los movimientos anteriores al período y consultar un balance no modifica filas.",
    "B02": "Un profit negativo del día no implica números rojos si el saldo previo lo cubre.",
    "B03": "Una empresa sin cuentas responde con lista vacía, importes 0.00 y ninguna cuenta en rojo.",
    "B04": "El período cubre días completos en UTC: el inicio se incluye y la medianoche siguiente a toDate queda fuera.",
    "B05": "El movimiento cuenta en la fecha de operación (transactionDate), no en la fecha de captura.",
    "B06": "Con Decimal, 0.10 + 0.20 − 0.30 da exactamente 0.00, y un saldo de cero no es estar en rojo.",
    "B07": "Solo participan los movimientos activos; desactivar uno no afecta a los demás.",
    "B08": "Desactivar una cuenta no borra su historial: sigue en el balance con isActive false y aporta al total.",
    "B09": "El signo lo decide transaction_type; asignar más conceptos a una cuenta no duplica importes.",
    "B10": "Un período invertido o una fecha inexistente se rechazan sin devolver un balance.",
    "B11": "Sin un token válido y vigente no se accede a ninguna de las dos consultas.",
    "B12": "La empresa sale del token: una cuenta ajena responde igual que una inexistente y no revela datos.",
    "B13": "El rol CONSULTA lee balances, pero no puede registrar movimientos.",
    "B14": "El permiso se lee en cada petición: sin transactions.read el mismo token deja de ver balances.",
    "B15": "Se permite un egreso que deja saldo negativo; el backend lo informa como números rojos.",
}
BANDA = """([texto, quien]) => {
  const banda = document.createElement('div');
  banda.style.cssText = 'background:#1e3a4c;color:#fff;font:15px system-ui;padding:10px 18px;display:flex;justify-content:space-between';
  banda.innerHTML = '<b></b><span></span>';
  banda.children[0].textContent = texto;
  banda.children[1].textContent = quien;
  document.body.prepend(banda);
  document.getElementById('graphiql').style.height = 'calc(100vh - 42px)';
}"""


class Capturador:
    """Ejecuta la operación en GraphiQL (el clic real hace la petición) y guarda la pantalla."""

    def __init__(self, browser):
        self.browser, self.numero, self.nombres = browser, 0, {}

    def __call__(self, query, variables=None, token=None):
        self.numero += 1
        archivo = f"{self.numero:02d}.png"
        contexto = self.browser.new_context(viewport={"width": 1500, "height": 900})
        page = contexto.new_page()
        if token:
            page.route(re.compile(re.escape(API) + r"(?:\?.*)?$"),
                       lambda route: route.continue_(headers={**route.request.headers, "authorization": f"Bearer {token}"}))
        params = urllib.parse.urlencode({"q": query, "variables": json.dumps(variables or {}, indent=2)},
                                        quote_via=urllib.parse.quote)
        page.goto(f"{API}?{params}", wait_until="networkidle", timeout=60000)
        boton = page.locator(".graphiql-execute-button")
        boton.wait_for(timeout=45000)
        with page.expect_response(lambda r: r.request.method == "POST" and r.url == API, timeout=30000) as respuesta:
            boton.click()
        payload = respuesta.value.json()
        quien = self.nombres.get(token) or datos.NOMBRES.get(token, "token alterado o vencido") if token else "sin token"
        encabezado = f"Authorization: Bearer {token[:14]}… · {quien}" if token else "Sin encabezado Authorization"
        page.evaluate(BANDA, [" · ".join(EQUIPO), f"{encabezado} · {datetime.now():%Y-%m-%d %H:%M:%S}"])
        # Se agranda el lienzo para que la respuesta completa quepa en la captura.
        lineas = max(len(json.dumps(payload, indent=2).splitlines()), len(query.splitlines()) + 14)
        page.set_viewport_size({"width": 1500, "height": min(3200, max(900, lineas * 21 + 200))})
        page.wait_for_timeout(500)
        page.screenshot(path=str(CAPTURAS / archivo))
        contexto.close()
        datos.CAPTURAS.append(archivo)
        return payload


def imagen(archivo):
    return "data:image/png;base64," + base64.b64encode((CAPTURAS / archivo).read_bytes()).decode()


def resumen(valor):
    # Se corta por líneas para que la tabla quepa en una página; las capturas muestran la respuesta completa.
    lineas = json.dumps(valor, ensure_ascii=False, indent=1).splitlines()
    return "\n".join(lineas if len(lineas) <= 34 else lineas[:34] + ["… (completo en evidencias/resultados.json)"])


def construir_pdf(browser, reporte):
    e = html.escape
    filas = "".join(f"<tr><td>{c['caso']}</td><td>{e(c['prueba'])}</td><td class={'ok' if c['paso'] else 'mal'}>"
                    f"{'Correcto' if c['paso'] else 'Falló'}</td></tr>" for c in reporte["casos"])
    unittest = EVIDENCIAS / "salida_unittest.txt"
    salida = unittest.read_text(encoding="utf-8") if unittest.exists() else "(no se encontró salida_unittest.txt)"
    doc = f"""<!doctype html><meta charset="utf-8"><style>
      body{{font:13px system-ui;color:#17243a;margin:0}} h1{{font-size:26px;margin:0 0 6px}} h2{{font-size:19px;margin:0 0 6px}}
      .portada{{padding:60px 40px;page-break-after:always}} .caso{{page-break-before:always;padding:10px 6px}}
      table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #cbd5e1;padding:5px 8px;text-align:left}}
      .ok{{color:#166534;font-weight:bold}} .mal{{color:#b91c1c;font-weight:bold}} .regla{{background:#eef6fb;padding:8px 12px;border-left:4px solid #1e3a4c}}
      pre{{background:#f4f6fa;border:1px solid #cbd5e1;padding:8px;white-space:pre-wrap;font:11px Consolas,monospace}}
      img{{display:block;max-width:100%;max-height:175mm;margin:8px auto;border:1px solid #94a3b8}} .captura{{page-break-inside:avoid}}
    </style>
    <section class="portada"><small>Tecnológico de Software · Fundamentos de Arquitectura de Software y Desarrollo Backend</small>
      <h1>Unidad II · Actividad 7 — Gestión de balances</h1><p>Evidencias B01 a B15 ejecutadas en GraphiQL contra la API y PostgreSQL de docker compose.</p>
      <p><b>Integrantes:</b> {e(', '.join(EQUIPO))}</p>
      <p><b>Ejecutado:</b> {e(reporte['ejecutado'])} · <b>Sufijo de datos:</b> {e(reporte['sufijo'])} · <b>Empresas:</b> {e(json.dumps(reporte['empresas']))}</p>
      <table><tr><th>Caso</th><th>Prueba</th><th>Resultado</th></tr>{filas}</table>
      <h2 style="margin-top:22px">Saldo inicial, profit, saldo final y números rojos</h2>
      <p>Banco empieza el período del 26 al 30 con 1,000.00 (ingreso de apertura del 25). Entran 3,000.00 y salen 2,200.00: su
      profit es 800.00, pero su saldo final es 1,800.00 porque conserva el dinero que ya tenía. Consultando solo el 28, el profit es
      −1,000.00 y el saldo final sigue en 1,800.00: un día negativo no la pone en rojo.</p>
      <p>Caja empieza en 0.00, recibe 500.00 y paga 700.00: profit −200.00 y saldo final −200.00. Como el saldo final es menor que
      cero, está en números rojos. El general cierra en 1,600.00 (isInRed false), pero accountsInRed = 1 revela a Caja.</p>
      <h2>Pruebas unitarias</h2><pre>{e(salida)}</pre></section>"""
    for c in reporte["casos"]:
        doc += (f"<section class='caso'><h2>{c['caso']} · {e(c['prueba'])} · "
                f"<span class={'ok' if c['paso'] else 'mal'}>{'Correcto' if c['paso'] else 'Falló'}</span></h2>"
                f"<p class='regla'><b>Regla comprobada:</b> {e(REGLAS[c['caso']])}</p>"
                f"<table><tr><th>Esperado</th><th>Obtenido</th></tr><tr><td><pre>{e(resumen(c['esperado']))}</pre></td>"
                f"<td><pre>{e(resumen(c['obtenido']))}</pre></td></tr></table>")
        doc += "".join(f"<div class='captura'><img src='{imagen(a)}'></div>" for a in c["capturas"]) + "</section>"
    page = browser.new_page()
    page.set_content(doc, wait_until="load")
    pie = f"<div style='font-size:8px;width:100%;text-align:center'>{e(' · '.join(EQUIPO))} · página <span class='pageNumber'></span></div>"
    page.pdf(path=str(PDF), format="A4", landscape=True, print_background=True, display_header_footer=True,
             header_template="<span></span>", footer_template=pie, margin={"top": "12mm", "bottom": "14mm", "left": "10mm", "right": "10mm"})
    page.close()


def main():
    from playwright.sync_api import sync_playwright

    CAPTURAS.mkdir(parents=True, exist_ok=True)
    for vieja in CAPTURAS.glob("*.png"):
        vieja.unlink()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        capturador = Capturador(browser)
        s = preparar()
        capturador.nombres = {t: f"{n} ({'CONSULTA' if n == 'Pedro' else 'ADMINISTRADOR'})" for n, t in s["t"].items()}
        datos.ejecutar = capturador
        reporte = actividad7.ejecutar_casos(s)
        construir_pdf(browser, reporte)
        browser.close()
    print(f"PDF: {PDF.relative_to(actividad7.ROOT)}")
    sys.exit(1 if any(not c["paso"] for c in reporte["casos"]) else 0)


if __name__ == "__main__":
    main()
