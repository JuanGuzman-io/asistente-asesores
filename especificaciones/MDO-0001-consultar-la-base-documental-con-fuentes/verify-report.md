---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
verdict: blocked
date: 2026-10-23
---

# Verify — Consultar la base documental con fuentes

**Bloqueado por un ajuste del PE.** Todo lo construido pasa: 250 pruebas unitarias, 17 e2e, evals
`consultas@v3` sin caída y gates. Con Gemini real, T13–T15 quedan resueltos: `modo` `modelo`, sin mezclar
productos y p95 mediana 1,3 s con 5 concurrentes. Durante este verify el PE concretó AC-7 ("un mensaje claro"):
el `detail` del 422 no puede llevar el prefijo de Pydantic ni repetir la entrada. Queda como T17; después se
repite `/mandao-verify MDO-0001`.

## Acceptance criteria → tests

| AC / clause | Critical | Tests | Level | Result |
|---|---|---|---|---|
| AC-1, AC-1/C1 | sí | S-1.1, S-1.1/C1, S-1.2 (`test_cargador`, `test_indice`, `test_arranque_indice`) | unit, e2e | pass |
| AC-2, AC-2/C1 | no | S-2.1, S-2.1/C1, S-2.2 (`test_duplicados`, `test_fuentes`) | unit | pass |
| AC-3 | sí | S-3.1, S-3.3, S-4.1, S-14.1 (`test_buscador`, `test_fts`, `test_flujo_consulta`); EV-1 0,982; humo con Gemini; p95 con modelo 1,3 s | unit, e2e, eval, manual | pass |
| AC-3/C1 | sí | S-4.1/C1, S-5.2 | unit, e2e | pass |
| AC-4, AC-4/C1 | sí | S-4.2, S-4.2/C1, `test_T14_S_4_1_*`; EV-4 1,00; humo: solo $50.000.000 | unit, eval, manual | pass |
| AC-5 | sí | S-5.1, S-5.2 (`test_flujo_consulta`); EV-7 1,00; humo: nombra la tasa que falta | unit, e2e, eval, manual | pass |
| AC-5/C1 | sí | S-5.1/C1 (`test_validacion`, `test_gemini`) | unit | pass |
| AC-5/C2 | sí | S-5.2, S-5.2/C1; EV-7 1,00 | unit, eval | pass |
| AC-6, AC-6/C1 | sí | S-6.1, S-6.1/C1 (`test_consultar`, `test_flujo_consulta`); EV-5 1,00 | unit, e2e, eval | pass |
| AC-7 | no | S-7.1 (`test_consultar_api::test_s7_1_*`); quickstart paso 3 | unit, manual | **falla según el ajuste del PE** (T17): el `detail` es "La petición no es válida. pregunta: Value error, …" |
| AC-7/C1 | no | S-7.1/C1 (`test_limites::test_s11_1_c1_*`) | unit | pass |
| AC-8 | no | S-8.1, S-8.1/C1, S-8.2 (`test_buscador`) | unit | pass |
| AC-9, AC-9/C1 | no | S-7.2, S-7.2/C1, S-7.2/C2 (`test_consultar_api::test_s7_2_*`) | unit | pass; el texto exacto del `detail` lo fija T17 |
| AC-10 | no | S-9.1, S-9.2 (`test_limites`); quickstart paso 4 | unit, manual | pass |
| AC-11 | sí | S-3.2, S-10.1 (`test_flujo_consulta`); EV-2 1,000; quickstart paso 5 | unit, e2e, eval, manual | pass |
| AC-12, AC-12/C1 | no | S-10.2, S-10.2/C1 (`test_consultar`) | unit | pass |
| AC-13, AC-13/C1 | no | S-10.3, S-10.3/C1 (`test_consultar`, `test_flujo_consulta`) | unit, e2e | pass |
| AC-14, AC-14/C1 | sí | S-11.1, S-11.1/C1, S-11.2 (`test_repositorio`, `test_flujo_consulta`) | unit, e2e | pass |
| AC-15, AC-15/C1 | no | S-13.1, S-13.1/C1 (`test_errores`) | unit | pass |
| AC-16 | sí | S-12.1, S-12.2 (`test_respaldo`, `test_respaldo_e2e`, `test_T13_D9_*`, semáforo de T15) | unit, e2e | pass |

### T13–T16, con Gemini real

- **T13:** las 3 preguntas con soporte y los 25 pedidos de la medición quedaron con `modo` `modelo`. El log no tiene ningún "se usa el extractivo".
- **T14:** "¿Cuál es el monto máximo del Crédito Productivo Impulso?" respondió "$50.000.000", con una sola fuente. No menciona $80.000.000 ni $30.000.000.
- **T15:** 5 concurrentes con modelo, N = 5 corridas: p95 mediana 1.312 ms (mín. 1.279, máx. 2.309), contra 3 s de NFR-1. Antes, con el candado, daba 4,4 s.
- **T16:** "¿Cuánto le prestan como máximo a un pequeño comerciante?" encuentra Crédito Productivo Impulso con modelo y en extractivo. En extractivo agrega Crédito Mujer Emprende como segunda fuente; es la limitación de [D12](design.md#d12) que el README anota.

## Suites

| Project | Kind | Result |
|---|---|---|
| asistente-asesores | unit (tester, `tests/server` sin `e2e`) | 250 passed, 9 deselected |
| asistente-asesores | e2e (tester, `tests/server/e2e`) | 17 passed |
| asistente-asesores | evals (`consultas@v3`) | 9 passed: EV-1 0,982, EV-2 1,000, EV-3 0,000, EV-4 1,00, EV-5 1,00, EV-7 1,00; margen mínimo 0,008 (s06). Igual a D4 v3; sin caída contra v2 |
| asistente-asesores | binario real sin clave (quickstart, puerto 8765) | 5/5 pasos como se espera; el paso 3 lo cambia T17 |
| asistente-asesores | humo con Gemini real | pass (T13, T14) |
| asistente-asesores | carga con modelo (5 concurrentes, N = 5) | p95 mediana 1.312 ms (≤ 3 s) |
| asistente-asesores | gates de T14 (`format`, `lint`, `typecheck`, `secrets`, `sast`, `metrics`) | PASS; `audit` omitido (sin cambio de dependencias); `test` NOT_INSTALLED (ver Evidence) |

`node .mandao/bin/mandao.mjs run tests` y el gate `test` del runner terminan con exit 127 (`pytest: command not
found`): llaman a `pytest` en lugar de `uv run pytest`. Los testers corrieron la suite con `uv run pytest`. Es un
defecto del runner, no del producto.

## TDD evidence (ADR 0022)

`missingRed`: ninguno. No cambió ninguna prueba en este verify.

## Security mentions (not blocking)

None.

Seguridad: secretos (`detect-secrets`) y SAST (`bandit`) están cubiertos en local. El receipt de T14 (`security`)
trae PASS ejecutado en los dos. El log del servidor de la prueba con Gemini no tiene la clave ni el texto de
las preguntas.

## Product bugs

- **PRODUCT_BUG T17** (ajuste del PE, 2026-10-23): el `detail` del 422 arma "La petición no es válida. " +
  `loc: msg` de Pydantic (`src/server/http/problemas.py:36-45`). Ejemplo: "La petición no es válida.
  pregunta: Value error, …". El PE pide estos textos exactos:
  - "La pregunta no puede estar vacía." (vacía o solo espacios)
  - "La pregunta no puede superar los 1.000 caracteres."
  - Para otros cuerpos inválidos, un mensaje claro sin detalles del framework.

  Concreta AC-7 ("un mensaje claro") y alinea con MDO-0002 (S-3.1).

## Deferred to CI

None.

## Blockers

- T17 por agregar e implementar con prueba roja primero (`/mandao-implement MDO-0001`). Después,
  `/mandao-verify MDO-0001`.

## Consistency Check

| ID | Type | Finding | Severity | Owner | Status |
|---|---|---|---|---|---|
| CC-1 | PREMISE | D9 ("`HttpOptions(timeout=5000)`") contra el API real, que exige al menos 10 s de plazo de servidor. | critical | dev | resolved 2026-10-23: D9 corregido; T13 verificado con Gemini real |
| CC-2 | CONTRADICTION | NFR-1 ("≤ 3 s con el modelo") contra el candado de `http/rutas.py`. | critical | dev | resolved 2026-10-23: T15; p95 mediana 1,3 s |
| CC-3 | GAP | AC-4 ("solo información encontrada") contra D7, que no daba al modelo la identidad de cada fragmento. | critical | dev | resolved 2026-10-23: T14; verificado con Gemini real |
| CC-4 | CONTRADICTION | EV-2 (dato faltante contaba como "sin soporte") contra AC-5 (soporte parcial). | normal | PO | resolved 2026-10-23: C-9 (PE), EV-7 |
| CC-5 | GAP | AC-7 ("un mensaje claro") contra S-7.1 ("un `detail` legible") y D8, que no fijan el texto: el `detail` expone el formato de Pydantic. | normal | PO | resolved 2026-10-23: el PE fijó los textos; se registra como C-11 y T17 |

## Evidence

```
$ node .mandao/bin/mandao.mjs run verify-plan MDO-0001
"missingRed":[], "deferred":[], "findings":[], "blockers":[],
"securityScans":[{"project":"asistente-asesores","secrets":"covered","sast":"covered","pendingCi":false}]

$ node .mandao/bin/mandao.mjs run gates MDO-0001 T14
format PASS · lint PASS · typecheck PASS · test NOT_INSTALLED (127) · build SKIPPED (none)
secrets PASS · audit SKIPPED (no dependency change) · sast PASS · metrics PASS
metrics: 9 passed, 267 deselected

$ node .mandao/bin/mandao.mjs run tests asistente-asesores <16 files>
sh: pytest: command not found   (exit 127)

$ uv run pytest tests/server --ignore=tests/server/e2e -q        (tester unit)
250 passed, 9 deselected, 1 warning
$ uv run ruff format --check . / uv run ruff check . / uv run mypy src
158 files already formatted / All checks passed! / Success: no issues found in 34 source files

$ uv run pytest tests/server/evals -s -q -o addopts=""           (tester unit)
=== EVALS consultas@v3 (umbrales alto=0.6 bajo=0.525) ===
EV-1=0.982  EV-2=1.000  EV-3=0.000  EV-4=1.000  EV-5=1.000  EV-7=1.000
coseno que decide, CON soporte: n=56 min=0.534 mediana=0.662 max=0.881
coseno que decide, dato faltante: n=4 min=0.577 mediana=0.584 max=0.604
coseno que decide, SIN soporte: n=20 min=-0.005 mediana=0.345 max=0.531
margen mínimo al umbral: 0.008 (s06)
9 passed

$ uv run pytest tests/server/e2e -v                               (tester e2e)
17 passed, 3 warnings in 1.20s

$ env -u GEMINI_API_KEY uv run uvicorn src.server.principal:app --port 8765 --workers 1   (quickstart)
1. 200 Exitosa, $50.000.000, fuente Productos de Crédito > Crédito Productivo Impulso (+ Crédito Mujer Emprende)
2. 200 "No tengo información suficiente para responder.", fuentes [], Sin información suficiente
3. 422, detail "pregunta: ... no puede estar vacía", requestId
4. 415 con requestId
5. token interno / clave temporal → mensaje fijo, fuentes []

$ uv run --env-file .env uvicorn src.server.principal:app --port 8000 --workers 1   (humo con Gemini real)
¿Cuál es el monto máximo del Crédito Productivo Impulso?
  200 1734ms Exitosa | 'El monto máximo del Crédito Productivo Impulso es $50.000.000.'
  fuentes=['Productos de Crédito > Crédito Productivo Impulso']
¿Cuál es el plazo máximo del Crédito Mujer Emprende y qué tasa de interés tiene?
  200 1146ms Exitosa | 'El plazo máximo del Crédito Mujer Emprende es de 48 meses. No encontré información sobre la tasa de interés.'
¿Cuánto le prestan como máximo a un pequeño comerciante?
  200 891ms Exitosa | 'El monto máximo para el Crédito Productivo Impulso, dirigido a pequeños comerciantes y microempresarios, es de $50.000.000.'
¿Cuál es el horario de atención de las agencias?
  200 29ms Sin información suficiente
$ sqlite3 almacen/consultas.db "select id, estado, modo ..."
544|EXITOSA|modelo · 543|EXITOSA|modelo · 542|EXITOSA|modelo · 545|SIN_INFORMACION|ninguno

$ carga_modelo.py almacen/consultas.db 5 30   (5 concurrentes con modelo, 30 s entre corridas)
corrida 1: 879 · 920 · 970 · 1178 · 1425 ms  p95=1376ms
corrida 2: 999 · 1224 · 1529 · 1879 · 2416 ms  p95=2309ms
corrida 3: 1066 · 1075 · 1216 · 1279 · 1321 ms  p95=1312ms
corrida 4: 947 · 1014 · 1074 · 1236 · 1319 ms  p95=1303ms
corrida 5: 961 · 961 · 1179 · 1261 · 1284 ms  p95=1279ms
modos: 25/25 'modelo'
p95 mediana=1312ms min=1279 max=2309 (N=5)

$ grep -c 'AIza' server.log; grep -ciE 'extractivo|traceback' server.log; grep -c 'Productivo' server.log
0 · 0 · 0
```
