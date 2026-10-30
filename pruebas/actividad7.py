r"""Unidad II, Actividad 7: casos B01 a B15 de balances contra la API y PostgreSQL de docker compose.

    python pruebas/actividad7.py

Los esperados están escritos a mano desde los datos de entrada (tabla del PDF), no con el servicio de
balances. Guarda docs/Actividad7/evidencias/resultados.json (sin tokens) y docs/Actividad7/variables/*.json.
"""
import json
import sys
from datetime import datetime
from decimal import Decimal

import actividad7_datos as datos
from actividad6 import ROOT, RUN, ok, sql, token_alterado, token_vencido
from actividad7_datos import (CEROS, ESPERADO, GENERAL, F, N, P, T, asignar, balance, cuenta, general, gql, mov,
                              preparar, usuario, utc)

DOCS = ROOT / "docs" / "Actividad7"
resultados = []


def caso(codigo, prueba, esperado, obtenido, paso):
    # Las capturas tomadas desde el caso anterior pertenecen a este.
    capturas, datos.CAPTURAS[:] = list(datos.CAPTURAS), []
    resultados.append({"caso": codigo, "prueba": prueba, "esperado": esperado, "obtenido": obtenido,
                       "paso": bool(paso), "capturas": capturas})
    print(f"{codigo} {'OK ' if paso else 'MAL'} {prueba}")


def coincide(obtenido, esperado):
    return obtenido is not None and all(obtenido.get(k) == v for k, v in esperado.items())


def dato(r, campo):
    return (r.get("data") or {}).get(campo)


def rechazo(r):
    return {"data": r.get("data"), "errors": [e["message"] for e in r.get("errors", [])]}


def rechazado(r):
    return bool(r.get("errors")) and r.get("data") is None


def identidades(g):
    d = {k: Decimal(g[k]) for k in ("openingBalance", "totalIncome", "totalExpense", "profit", "closingBalance")}
    return (d["profit"] == d["totalIncome"] - d["totalExpense"]
            and d["closingBalance"] == d["openingBalance"] + d["profit"]
            and d["closingBalance"] == sum(Decimal(c["closingBalance"]) for c in g["accounts"])
            and g["accountsInRed"] == sum(Decimal(c["closingBalance"]) < 0 for c in g["accounts"]))


def referencia(s):
    ana, cuentas = s["t"]["Ana"], s["cuentas"]
    filas = f"SELECT COUNT(*) || ' / ' || MAX(updated_at) FROM transactions WHERE company_id = {int(s['A'])};"
    antes = sql(filas)
    individuales = {n: dato(balance(ana, cuentas[n]), "accountBalance") for n in ESPERADO}
    g = dato(general(ana), "generalBalance")
    despues = sql(filas)
    paso = (all(coincide(individuales[n], ESPERADO[n]) for n in ESPERADO) and coincide(g, GENERAL)
            and identidades(g) and antes == despues)
    caso("B01", "Banco, Caja, Ahorro y general del 26 al 30", {"cuentas": ESPERADO, "general": GENERAL},
         {"cuentas": individuales, "general": g, "filas_antes": antes, "filas_despues": despues}, paso)

    b02 = dato(balance(ana, cuentas["Banco"], f"{P}28", f"{P}28"), "accountBalance")
    esperado = dict(zip(N, ("2800.00", "0.00", "1000.00", "-1000.00", "1800.00", False)))
    caso("B02", "Banco solo el 28", esperado, b02, coincide(b02, esperado))
    b03 = dato(general(s["t"]["Carla"]), "generalBalance")
    caso("B03", "Empresa sin cuentas", CEROS, b03, coincide(b03, CEROS))

    variables = {n.lower(): {"accountId": cuentas[n], "from": F, "to": T} for n in ESPERADO}
    variables |= {"general": {"from": F, "to": T}, "banco_28": {"accountId": cuentas["Banco"], "from": f"{P}28", "to": f"{P}28"}}
    for nombre, valores in variables.items():
        (DOCS / "variables" / f"{nombre}.json").write_text(json.dumps(valores, indent=2) + "\n", encoding="utf-8")


def fechas_y_precision(s):
    dani, cd = s["t"]["Dani"], s["cD"]
    limites = cuenta(dani, s["D"], cd, "Limites")
    for monto, fecha in (("10.00", "25T23:59:59"), ("20.00", "26T00:00:00"), ("30.00", "30T23:59:59"), ("40.00", "31T00:00:00")):
        mov(dani, cd, limites, "INCOME", monto, f"{P}{fecha}Z")
    b04 = dato(balance(dani, limites), "accountBalance")
    esperado = {"openingBalance": "10.00", "totalIncome": "50.00", "closingBalance": "60.00"}
    caso("B04", "Movimientos en los cuatro límites del período", esperado, b04, coincide(b04, esperado))

    tardia = cuenta(dani, s["D"], cd, "Captura tardia")
    tx = mov(dani, cd, tardia, "INCOME", "75.00", utc("27"))
    dia27 = dato(balance(dani, tardia, f"{P}27", f"{P}27"), "accountBalance")
    dia28 = dato(balance(dani, tardia, f"{P}28", f"{P}28"), "accountBalance")
    paso = (datetime.fromisoformat(tx["capturedAt"]) > datetime.fromisoformat(tx["transactionDate"])
            and coincide(dia27, {"totalIncome": "75.00"}) and coincide(dia28, {"openingBalance": "75.00", "totalIncome": "0.00"}))
    caso("B05", "Movimiento del 27 capturado después", {"27": {"totalIncome": "75.00"}, "28": {"openingBalance": "75.00"}},
         {"movimiento": tx, "27": dia27, "28": dia28}, paso)

    centavos = cuenta(dani, s["D"], cd, "Centavos")
    for tipo, monto in (("INCOME", "0.10"), ("INCOME", "0.20"), ("EXPENSE", "0.30")):
        mov(dani, cd, centavos, tipo, monto, utc("27"))
    b06 = dato(balance(dani, centavos), "accountBalance")
    esperado = {"totalIncome": "0.30", "totalExpense": "0.30", "profit": "0.00", "closingBalance": "0.00", "isInRed": False}
    caso("B06", "0.10 + 0.20 - 0.30", esperado, b06, coincide(b06, esperado))


def estados(s):
    dani, cd = s["t"]["Dani"], s["cD"]
    anulable = cuenta(dani, s["D"], cd, "Anulable")
    mov(dani, cd, anulable, "INCOME", "100.00", utc("27"))
    tx = mov(dani, cd, anulable, "INCOME", "50.00", utc("27"))
    antes = dato(balance(dani, anulable), "accountBalance")
    ok(datos.ejecutar("mutation DesactivarMovimiento($id: ID!) {\n  deleteTransaction(id: $id) {\n    id\n    amount\n"
                      "    isActive\n  }\n}", {"id": tx["id"]}, dani), "deleteTransaction")
    despues = dato(balance(dani, anulable), "accountBalance")
    caso("B07", "Desactivar un movimiento de 50.00", {"antes": "150.00", "despues": "100.00"}, {"antes": antes, "despues": despues},
         coincide(antes, {"totalIncome": "150.00"}) and coincide(despues, {"totalIncome": "100.00"}))

    cerrada = cuenta(dani, s["D"], cd, "Cerrada")
    mov(dani, cd, cerrada, "INCOME", "200.00", utc("27"))
    g_antes = dato(general(dani), "generalBalance")
    # No existe mutación para desactivar cuentas: se prepara con SQL de laboratorio (ver docs/Actividad7/laboratorio.sql).
    sql(f"UPDATE accounts SET is_active = FALSE, updated_at = NOW() WHERE id = {int(cerrada)};")
    individual = dato(balance(dani, cerrada), "accountBalance")
    g_despues = dato(general(dani), "generalBalance")
    en_general = next(c for c in g_despues["accounts"] if c["accountId"] == cerrada)
    caso("B08", "Cuenta desactivada con movimientos", {"isActive": False, "closingBalance": "200.00", "general": "sin cambios"},
         {"cuenta": individual, "general_antes": g_antes["closingBalance"], "general_despues": g_despues["closingBalance"]},
         coincide(individual, {"isActive": False, "closingBalance": "200.00"}) and en_general == individual
         and g_antes["closingBalance"] == g_despues["closingBalance"])

    q = 'mutation($c: ID!) { createConcept(input: {companyId: $c, conceptType: INCOME, name: "Intereses"}) { id } }'
    antes = dato(general(dani), "generalBalance")
    asignar(dani, anulable, ok(gql(q, {"c": s["D"]}, dani), "createConcept")["id"])
    despues = dato(general(dani), "generalBalance")
    caso("B09", "Otro concepto en una cuenta sin movimientos nuevos", "general idéntico", {"antes": antes, "despues": despues},
         antes == despues)


def acceso(s):
    ana, banco = s["t"]["Ana"], s["cuentas"]["Banco"]
    errores = [general(ana, f"{P}30", f"{P}26"), balance(ana, banco, f"{P}30", f"{P}26"), general(ana, "2026-02-30", T)]
    caso("B10", "fromDate > toDate y fecha inexistente", "error sin balance", [rechazo(r) for r in errores],
         all(rechazado(r) for r in errores))

    tokens = {"sin token": None, "alterado": token_alterado(ana), "vencido": token_vencido(ana)}
    b11 = {n: [rechazo(general(t)), rechazo(balance(t, banco))] for n, t in tokens.items()}
    caso("B11", "Sin token, alterado y vencido", "rechazo en ambas consultas", b11,
         all(r["data"] is None and r["errors"] for par in b11.values() for r in par))

    ajena, inexistente = balance(ana, s["ajena"]), balance(ana, "999999999")
    g = dato(general(ana), "generalBalance")
    texto = json.dumps([ajena, inexistente])
    paso = (rechazado(ajena) and rechazo(ajena)["errors"] == ["Cuenta no disponible"] == rechazo(inexistente)["errors"]
            and "Banco B" not in texto and "9999.99" not in texto
            and sorted(c["accountId"] for c in g["accounts"]) == sorted(s["cuentas"].values()))
    caso("B12", "Token de A con cuenta de B; general de A", {"error": "Cuenta no disponible", "general": "solo cuentas de A"},
         {"ajena": rechazo(ajena), "inexistente": rechazo(inexistente), "cuentas_general_A": [c["accountName"] for c in g["accounts"]]}, paso)

    pedro, contar = s["t"]["Pedro"], f"SELECT COUNT(*) FROM transactions WHERE company_id = {int(s['A'])};"
    lectura = dato(general(pedro), "generalBalance")
    antes = sql(contar)
    captura = datos.ejecutar("""mutation CapturaConsulta($a: ID!, $c: ID!) {
  createTransaction(input: {accountId: $a, conceptId: $c, transactionType: INCOME, amount: "10.00"}) {
    id
  }
}""", {"a": banco, "c": s["cA"]["INCOME"]}, pedro)
    despues = sql(contar)
    caso("B13", "Rol CONSULTA lee balances pero no captura", {"lectura": GENERAL, "captura": "rechazada", "filas": "iguales"},
         {"lectura": lectura, "captura": rechazo(captura), "filas_antes": antes, "filas_despues": despues},
         coincide(lectura, GENERAL) and rechazado(captura) and antes == despues)
    permisos_temporales(s)


def permisos_temporales(s):
    ana = s["t"]["Ana"]
    permisos = {p["code"]: p["id"] for p in ok(gql("{ permissions { id code } }"), "permissions")}
    rol = ok(gql('mutation($c: String!) { createRole(input: {code: $c, name: "Lector de balances"}) { id } }',
                 {"c": f"BALANCES_{RUN.upper()}"}, ana), "createRole")["id"]
    poner = "mutation($r: ID!, $p: ID!) { assignPermissionToRole(input: {roleId: $r, permissionId: $p}) { id } }"
    quitar = "mutation($r: ID!, $p: ID!) { removePermissionFromRole(roleId: $r, permissionId: $p) }"
    for codigo in ("accounts.read", "transactions.read"):
        ok(gql(poner, {"r": rol, "p": permisos[codigo]}, ana), "assignPermissionToRole")
    rita = usuario(ana, s["A"], "Rita", rol)
    con_permiso = general(rita)
    ok(gql(quitar, {"r": rol, "p": permisos["transactions.read"]}, ana), "removePermissionFromRole")
    sin_permiso = [general(rita), balance(rita, s["cuentas"]["Banco"])]
    ok(gql(poner, {"r": rol, "p": permisos["transactions.read"]}, ana), "assignPermissionToRole")
    restaurado = general(rita)
    caso("B14", "Retirar transactions.read al rol de prueba y restaurarlo", "lee / rechaza ambas / lee",
         {"con_permiso": bool(dato(con_permiso, "generalBalance")), "sin_permiso": [rechazo(r) for r in sin_permiso],
          "restaurado": bool(dato(restaurado, "generalBalance"))},
         dato(con_permiso, "generalBalance") and all(rechazado(r) for r in sin_permiso) and dato(restaurado, "generalBalance"))

    eva = s["t"]["Eva"]
    vacia = cuenta(eva, s["E"], s["cE"], "Vacia")
    mov(eva, s["cE"], vacia, "EXPENSE", "50.00", utc("27"))
    individual, g = dato(balance(eva, vacia), "accountBalance"), dato(general(eva), "generalBalance")
    esperado = {"closingBalance": "-50.00", "isInRed": True}
    caso("B15", "Egreso de 50.00 en cuenta vacía", {**esperado, "accountsInRed": 1}, {"cuenta": individual, "general": g},
         coincide(individual, esperado) and coincide(g, {**esperado, "accountsInRed": 1}))


def ejecutar_casos(s):
    """Corre B01-B15 sobre los datos de preparar(), guarda resultados.json y devuelve el reporte."""
    for carpeta in ("variables", "evidencias"):
        (DOCS / carpeta).mkdir(parents=True, exist_ok=True)
    for grupo in (referencia, fechas_y_precision, estados, acceso):
        grupo(s)
    reporte = {"ejecutado": datetime.now().isoformat(timespec="seconds"), "sufijo": RUN,
               "empresas": {k: s[k] for k in "ABCDE"}, "casos": resultados}
    salida = DOCS / "evidencias" / "resultados.json"
    salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fallos = sum(not r["paso"] for r in resultados)
    print(f"{len(resultados) - fallos}/{len(resultados)} casos correctos. Evidencia: {salida.relative_to(ROOT)}")
    return reporte


def main():
    reporte = ejecutar_casos(preparar())
    sys.exit(1 if any(not r["paso"] for r in reporte["casos"]) else 0)


if __name__ == "__main__":
    main()
