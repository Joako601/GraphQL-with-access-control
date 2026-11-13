# Guion de la demostración final (Parcial III)

Duración objetivo: 4–5 minutos. Antes de empezar: `docker compose up -d`, `python pruebas/unidad3_actividad1_datos.py`
(debe decir "coincide con la tabla a mano") y `npm run dev` en `dashboard/` (ver README). Tener GraphiQL abierto en
`http://localhost:8004/graphql`.

1. **Contexto (20 s).** "El dashboard es un cliente web de nuestro API GraphQL. No calcula nada: todos los números salen de `generalBalance`."
2. **Login (40 s).** Abrir `http://localhost:5173`, escribir `ana.demo@empresa.test` / `secreto123` y pulsar "Continuar".
   En DevTools → Network mostrar que `login` es una mutación y que la siguiente petición lleva `Authorization: Bearer …` y no envía `companyId`.
3. **Indicadores generales (60 s).** Con el período 26–30 oct 2026, señalar el encabezado ("Empresa Demo Dashboard", MXN,
   período) y leer las cinco tarjetas: $1,000.00 · $3,500.00 · $2,900.00 · $600.00 · $1,600.00. Ejecutar la misma consulta
   en GraphiQL (con el token en *Headers*) para mostrar que las cifras coinciden.
4. **Cuenta en rojo con total positivo (40 s).** "Estado de riesgo": "¿General en rojo?" → No y "Cuentas en rojo: 1" (Caja).
   En "Detalle por cuenta", Caja termina en −$200.00 con "En rojo" mientras el saldo general sigue en $1,600.00.
   Aclarar que un profit negativo (ámbar) no es lo mismo que un saldo negativo (rojo).
5. **Cambio de fechas (40 s).** Poner "Desde" y "Hasta" en 28/10/2026 y pulsar "Actualizar": profit −$1,000.00 (ámbar),
   saldo final $2,300.00, ninguna cuenta en rojo; "Período consultado" muestra "28 oct 2026 – 28 oct 2026". Después poner
   "Desde" posterior a "Hasta": "La fecha inicial no puede ser posterior a la fecha final.", sin llamada al API.
6. **Seguridad (40 s).** "Cerrar sesión" y entrar como `sinlectura.demo@empresa.test`: "Acceso denegado", sin números.
   Luego, en DevTools → Application → Session Storage, alterar el `token` dentro de `dashboard.session` y recargar: vuelve
   al login con "Tu sesión expiró o el token no es válido. Inicia sesión de nuevo."
7. **Cierre (20 s).** Cada tarjeta corresponde a un campo GraphQL (`openingBalance`, `totalIncome`, `totalExpense`,
   `profit`, `closingBalance`, `isInRed`, `accountsInRed`, `accounts`).
