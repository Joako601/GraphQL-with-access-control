r"""Unidad III, Actividad 2, parte 1: comprobación de la idempotencia de createTransaction contra la API real.

Requiere la API de docker compose y los datos de unidad3_actividad2_datos.py. Ejecutar desde la raíz:
    python pruebas/unidad3_actividad2_idempotencia.py

Casos (sección 6 del PDF):
    1. La misma mutación dos veces con la misma idempotencyKey devuelve el mismo id.
    2. La misma mutación con otra llave crea un segundo movimiento, aunque el monto coincida.
    3. En la base hay una sola fila de movimiento y una sola llave para la primera llave.
    4. La misma llave con otro monto se rechaza (no reutiliza ni inserta).
    5. Dos envíos simultáneos con la misma llave: un solo movimiento (el índice único decide).
    6. Una lectura (generalBalance) repetida no inserta filas.
Sale con código 1 si algún caso falla.
"""
import uuid
from concurrent.futures import ThreadPoolExecutor

import actividad6 as a6
import actividad7_datos as d
import unidad3_actividad2_datos as equipo

CREATE_TX = """mutation RegistrarEgreso($input: CreateTransactionInput!) {
  createTransaction(input: $input) {
    id
    amount
    transactionType
    account { name }
    concept { name }
  }
}"""
IDS = """query($c: ID!) { accounts(companyId: $c) { id name } concepts(companyId: $c) { id name } }"""
ME = "{ me { companyId } }"


def contar(sql):
    return int(a6.sql(sql))


def main():
    token = equipo.login("Ariff Medina")  # CAPTURISTA: tiene transactions.write
    if not token:
        raise SystemExit("Primero ejecuta: python pruebas/unidad3_actividad2_datos.py")
    company = a6.ok(d.gql(ME, token=token), "me")["companyId"]
    ids = a6.ok(d.gql(IDS, {"c": company}, token), "accounts")
    conceptos = {c["name"]: c["id"] for c in d.gql(IDS, {"c": company}, token)["data"]["concepts"]}
    banco = next(c["id"] for c in ids if c["name"] == "Banco")

    def entrada(llave, monto="100.00"):
        return {"input": {"idempotencyKey": llave, "accountId": banco, "conceptId": conceptos["Renta"],
                          "transactionType": "EXPENSE", "amount": monto,
                          "shortDescription": "Pago de renta (prueba de idempotencia)"}}

    def enviar(llave, monto="100.00"):
        return d.gql(CREATE_TX, entrada(llave, monto), token)

    total = f"SELECT COUNT(*) FROM transactions WHERE company_id = {int(company)};"
    llave = f"renta-{uuid.uuid4()}"
    resultados = []

    def caso(numero, descripcion, paso, detalle):
        resultados.append(paso)
        print(f"Caso {numero}: {'OK ' if paso else 'MAL'} {descripcion} -> {detalle}")

    antes = contar(total)
    primero = a6.ok(enviar(llave), "createTransaction")
    reintento = a6.ok(enviar(llave), "createTransaction")
    caso(1, "misma llave dos veces", primero["id"] == reintento["id"] and contar(total) == antes + 1,
         f"id {primero['id']} y {reintento['id']}, filas {antes} -> {contar(total)}")

    otra = a6.ok(enviar(f"renta-{uuid.uuid4()}"), "createTransaction")
    caso(2, "otra llave, mismo monto", otra["id"] != primero["id"] and contar(total) == antes + 2,
         f"id nuevo {otra['id']}, filas {contar(total)}")

    filas_llave = contar(f"SELECT COUNT(*) FROM idempotency_keys WHERE idempotency_key = '{llave}';")
    filas_mov = contar(f"""SELECT COUNT(*) FROM transactions t JOIN idempotency_keys k ON k.transaction_id = t.id
                           WHERE k.idempotency_key = '{llave}';""")
    caso(3, "una sola fila para la primera llave", filas_llave == 1 and filas_mov == 1,
         f"idempotency_keys={filas_llave}, transactions={filas_mov}")

    distinto = enviar(llave, "999.00")
    mensaje = distinto.get("errors", [{}])[0].get("message", "(sin error)")
    caso(4, "misma llave, otro monto", "ya se usó con otros datos" in mensaje and contar(total) == antes + 2, mensaje)

    simultanea = f"renta-{uuid.uuid4()}"
    previo = contar(total)
    with ThreadPoolExecutor(max_workers=5) as pool:
        respuestas = list(pool.map(lambda _: enviar(simultanea), range(5)))
    ids_simultaneos = {a6.ok(r, "createTransaction")["id"] for r in respuestas}
    caso(5, "5 envíos simultáneos, misma llave", len(ids_simultaneos) == 1 and contar(total) == previo + 1,
         f"ids {sorted(ids_simultaneos)}, filas {previo} -> {contar(total)}")

    previo = contar(total)
    for _ in range(3):
        a6.ok(d.gql("{ generalBalance(fromDate: \"2026-01-01\", toDate: \"2026-12-31\") { closingBalance } }",
                    token=equipo.login("Joaquín Uriona")), "generalBalance")
    caso(6, "lectura repetida", contar(total) == previo, f"filas {previo} -> {contar(total)}")

    print("\nTodas las comprobaciones pasaron." if all(resultados) else "\nHay comprobaciones que fallaron.")
    raise SystemExit(0 if all(resultados) else 1)


if __name__ == "__main__":
    main()
