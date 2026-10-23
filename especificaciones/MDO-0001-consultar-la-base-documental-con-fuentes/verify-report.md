---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
verdict: blocked
date: 2026-10-23
---

# Verify — Consultar la base documental con fuentes

**Bloqueado.** El modo extractivo cumple: pruebas, evals con `consultas@v2` y latencia (p95 19 ms con 5
concurrentes). Pero la prueba de humo con Gemini real encontró tres defectos de producto: con clave, el
modelo nunca responde; además mezcla productos y el candado pasa de 3 s. Quedan como T13–T15 (decisión
del PE); después se repite `/mandao-verify MDO-0001`.

## Acceptance criteria → tests

| AC / clause | Critical | Tests | Level | Result |
|---|---|---|---|---|
| AC-1, AC-1/C1 | sí | S-1.1, S-1.1/C1, S-1.2 (`test_cargador`, `test_arranque_indice`); arranque real con uvicorn | unit, e2e, manual | pass |
| AC-2, AC-2/C1 | no | S-2.1, S-2.1/C1, S-2.2 (`test_duplicados`) | unit | pass |
| AC-3 | sí | S-3.1, S-3.2, S-4.1, S-14.1; EV-1 0,952, EV-3 0,000 | unit, e2e, eval | pass en extractivo; NFR-1 con modelo **falla** (T15) |
| AC-3/C1 | sí | S-4.1/C1, S-5.2 | unit, e2e | pass |
| AC-4, AC-4/C1 | sí | S-4.2, S-4.2/C1, S-5.1/C1; EV-4 1,00 | unit, eval | pass con dobles; con Gemini real **falla** (T14: mezcla montos de dos créditos) |
| AC-5 | sí | S-5.1, S-5.2; EV-7 1,00 | unit, e2e, eval | pass en extractivo; EV-6 sin medir (el modelo no responde, T13) |
| AC-5/C1 | sí | S-5.1/C1 | unit | pass con dobles |
| AC-5/C2 | sí | S-5.2, S-5.2/C1; EV-7 1,00 | unit, eval | pass |
| AC-6, AC-6/C1 | sí | S-6.1, S-6.1/C1; EV-5 1,00 | unit, e2e, eval | pass |
| AC-7, AC-7/C1 | no | S-7.1, S-7.1/C1 (`test_consultar_api`) | unit | pass |
| AC-8 | no | S-8.1, S-8.1/C1, S-8.2 | unit | pass |
| AC-9, AC-9/C1 | no | S-7.2, S-7.2/C1, S-7.2/C2 | unit | pass |
| AC-10 | no | S-9.1, S-9.2 (`test_limites`) | unit | pass |
| AC-11 | sí | S-10.1; EV-2 1,000 | unit, e2e, eval | pass |
| AC-12, AC-12/C1 | no | S-10.2, S-10.2/C1 | unit | pass |
| AC-13, AC-13/C1 | no | S-10.3, S-10.3/C1; EV-2 (s04, s05, s14) | unit, eval | pass |
| AC-14, AC-14/C1 | sí | S-11.1, S-11.1/C1, S-11.2 (`test_repositorio`) | unit, e2e | pass |
| AC-15, AC-15/C1 | no | S-13.1, S-13.1/C1 (`test_errores`) | unit | pass |
| AC-16 | sí | S-12.1, S-12.2 (`test_respaldo`, `test_respaldo_e2e`) | unit, e2e | pass (el respaldo funcionó en la prueba real); el corte de 5 s es rechazado por el API (T13) |

## Suites

| Project | Kind | Result |
|---|---|---|
| asistente-asesores | unit (`uv run pytest`) | 254 passed, 9 deselected |
| asistente-asesores | e2e (incluidas en la suite: `tests/server/e2e`) | pass |
| asistente-asesores | evals (`uv run pytest -m eval`, `consultas@v2`) | 9 passed: EV-1 0,952, EV-2 1,000, EV-3 0,000, EV-4 1,00, EV-5 1,00, EV-7 1,00, margen mínimo 0,008 |
| asistente-asesores | humo con Gemini real | **falla**: 400 en toda llamada (T13) |
| asistente-asesores | carga extractiva (5 concurrentes, N = 5) | p95 mediana 19,0 ms (≤ 300 ms) |
| asistente-asesores | gates `format`, `lint`, `typecheck`, `secrets`, `sast`, `audit` | pass |

No se delegaron testers por suite: `verify-plan` ya bloquea por T13–T15 abiertas, y la corrida completa con
testers va en el próximo verify. Las suites de arriba las corrió esta sesión.

### Pedidos del PE en esta sesión

1. **Punto de entrada:** `src.server.principal:app`; `uv run uvicorn src.server.principal:app --port 8000 --workers 1` arrancó, indexó y respondió por `curl` (200 `Exitosa` con fuente; 200 `Sin información suficiente`). Documentado en `AGENTS.md` ("Levantar el backend"), `README.md` y `src/server/AGENTS.md`. `almacen/` se agregó a `.gitignore` (design.md lo pedía y faltaba).
2. **Dataset v2 y recalibración:** de 32 a 66 preguntas. Las 4 de dato faltante pasaron a `dato_faltante` ([C-9](requirements.md#c-9)); `UMBRAL_BAJO` de 0,54 a 0,525.

   | | v1, 0,60 / 0,54 (antes) | v2, 0,60 / 0,54 | v2, 0,60 / 0,525 (después) |
   |---|---|---|---|
   | EV-1 | 0,955 | 0,929 | 0,952 |
   | EV-2 | 1,000 | 1,000 | 1,000 |
   | EV-3 | 0,000 | 0,024 | 0,000 |
   | EV-4 / EV-5 | 1,00 / 1,00 | 1,00 / 1,00 | 1,00 / 1,00 |
   | EV-7 | — | 1,000 | 1,000 |
   | Margen mínimo real | 0,016 (c09) | 0,006 (c33, fuera) | 0,008 (s06 y c33) |

   El "0,001 del borde" de T10 (s02, 0,599) salía del mejor coseno de todo el índice. El buscador decide con el coseno del mejor fragmento tras RRF (s02: 0,410 con FTS). El reporte ahora imprime ese coseno y una eval falla si un margen baja de 0,005. 0,008 es el máximo posible con v2: sigue siendo estrecho.
3. **Humo con Gemini real** (`GEMINI_API_KEY` presente en `.env`): ver Product bugs. La limitación del README es la de C-9, no la falta de clave.
4. **p95:** extractivo con 5 concurrentes: 19,0 ms. Con modelo: el candado serializa y 5 concurrentes dieron 0,9 / 1,7 / 2,6 / 3,6 / 4,4 s, así que **sí rompe los 3 s** desde la 4.ª en cola (T15). Además, un corte de 5 s ya supera los 3 s por sí solo.

## TDD evidence (ADR 0022)

`missingRed`: T13, T14, T15. Son tareas nuevas sin implementar: su evidencia roja va en `/mandao-implement`.
Pruebas que cambiaron en esta sesión: `test_buscador.py::test_d4_umbrales_calibrados_en_configuracion`
(fija 0,525 en vez de 0,54; es una recalibración pedida, no una aserción más débil) y `test_evals.py`
(v2, EV-7 y el control de margen).

## Security mentions (not blocking)

None.

## Product bugs

- **PRODUCT_BUG T13:** `HttpOptions(timeout=5000)` hace que el SDK envíe `X-Server-Timeout: 5`, y el API responde 400 `INVALID_ARGUMENT` "Manually set deadline 5s is too short. Minimum allowed deadline is 10s." Con clave real toda consulta cayó al extractivo (`modo` `extractivo` en las 3 con soporte). Con `headers={"X-Server-Timeout": "10"}` y el corte de 5 s del cliente, las llamadas llegaron al modelo (0,9 a 1,5 s).
- **PRODUCT_BUG T14:** `contents` solo lleva el texto del fragmento, sin `documento > sección`. A "¿Cuál es el monto máximo del Crédito Productivo Impulso?", con fragmentos de dos créditos, el modelo respondió "los montos máximos indicados son $50.000.000 y $80.000.000. No encontré información sobre Crédito Productivo Impulso." Pasó el guardrail, porque ambas cifras estaban en fragmentos citados.
- **PRODUCT_BUG T15:** el candado global de `RedactorExclusivo` serializa las llamadas al modelo: p95 de unos 4,4 s con 5 concurrentes contra los 3 s de NFR-1.

## Deferred to CI

None.

## Blockers

- T13, T14 y T15 abiertas (`verify-plan`: "T13 is not done", "T14 is not done", "T15 is not done").

## Consistency Check

| ID | Type | Finding | Severity | Owner | Status |
|---|---|---|---|---|---|
| CC-1 | PREMISE | D9 ("`HttpOptions(timeout=5000)`") contra el API real, que exige al menos 10 s de plazo de servidor. | critical | dev | resolved 2026-10-23: D9 corregido; T13 lo implementa |
| CC-2 | CONTRADICTION | NFR-1 ("≤ 3 s con el modelo") contra el candado de `http/rutas.py`, que serializa las llamadas al modelo (4,4 s con 5 concurrentes). | critical | dev | resolved 2026-10-23: el PE abrió T15 (semáforo) |
| CC-3 | GAP | AC-4 ("solo información encontrada") contra D7, que no daba al modelo la identidad de cada fragmento: mezcló montos de dos créditos. | critical | dev | resolved 2026-10-23: D7 corregido; T14 lo implementa |
| CC-4 | CONTRADICTION | EV-2 (dato faltante contaba como "sin soporte") contra AC-5 (soporte parcial): con v2 ningún par de umbrales cumplía EV-2 y EV-3. | normal | PO | resolved 2026-10-23: C-9 (PE), EV-7 |

## Evidence

```
$ uv run pytest -m eval   (antes: v1, 0,60 / 0,54)
EV-1=0.955 (>=0.90)  EV-2=1.000 (>=0.90)  EV-3=0.000 (<=0.10)  EV-4=1.000 (==1.00)  EV-5=1.000 (==1.00)
7 passed, 252 deselected

$ uv run pytest -m eval -s   (v2 sin reclasificar, 0,60 / 0,54)
EV-1=0.929  EV-2=0.833  EV-3=0.024  EV-4=1.000  EV-5=1.000
FAILED tests/server/evals/test_evals.py::test_ev2_precision_de_sin_informacion

$ uv run pytest -m eval -s   (después: v2, 0,60 / 0,525)
=== EVALS consultas@v2 (umbrales alto=0.6 bajo=0.525) ===
EV-1=0.952 (>=0.90)  EV-2=1.000 (>=0.90)  EV-3=0.000 (<=0.10)  EV-4=1.000 (==1.00)  EV-5=1.000 (==1.00)  EV-7=1.000 (>=0.90)
coseno que decide, CON soporte: n=42 min=0.534 mediana=0.667 max=0.881
coseno que decide, dato faltante: n=4 min=0.577 mediana=0.584 max=0.604
coseno que decide, SIN soporte: n=20 min=0.076 mediana=0.345 max=0.531
margen mínimo al umbral: 0.008 (s06)
9 passed, 254 deselected

$ uv run ruff format --check . && uv run ruff check . && uv run mypy src && uv run pytest -q
157 files already formatted / All checks passed! / Success: no issues found in 34 source files
254 passed, 9 deselected, 2 warnings

$ secrets (detect-secrets, tracked + untracked) → exit 0
$ uvx --quiet bandit -r src -q → exit 0
$ pip-audit (gate audit) → No known vulnerabilities found, 35 ignored

$ uv run uvicorn src.server.principal:app --port 8000 --workers 1
INFO:     Application startup complete.
$ curl ... '{"pregunta":"¿Cuál es el monto máximo del Crédito Productivo Impulso?"}'
HTTP/1.1 200 OK · x-request-id: a1d6b55e-… · "estado":"Exitosa" · fuente Productos de Crédito > Crédito Productivo Impulso
$ curl ... '{"pregunta":"¿Cuál es la capital de Francia?"}'
{"respuesta":"No tengo información suficiente para responder.","fuentes":[],"estado":"Sin información suficiente"}

$ carga.py consultas.json 5 100 5   (extractivo, 5 concurrentes)
corrida 1: p95=21.7ms · corrida 2: p95=28.2ms · corrida 3: p95=19.0ms · corrida 4: p95=17.0ms · corrida 5: p95=17.9ms
p95 mediana=19.0ms min=17.0 max=28.2 (N=5), códigos [200]

$ uv run --env-file .env uvicorn src.server.principal:app ...   (humo con Gemini real)
¿Cuál es el monto máximo del Crédito Productivo Impulso?  → 200 1138ms Exitosa modo=extractivo
¿Cuál es el horario de atención de las agencias?          → 200 24ms Sin información suficiente modo=ninguno
log: Redactor con modelo no disponible, se usa el extractivo: fallo del modelo (ClientError)

$ diag_gemini2.py   (la llamada exacta del redactor)
APIError code=400 status=INVALID_ARGUMENT
Manually set deadline 5s is too short. Minimum allowed deadline is 10s.

$ diag_gemini3.py   (headers X-Server-Timeout: 10, corte de 5 s)
1467ms modo=modelo usados=[1, 2] sin_soporte=['Crédito Productivo Impulso']
  La información proporcionada no especifica a qué producto corresponde cada monto máximo, pero los montos máximos indicados en los documentos son $50.000.000 y $80.000.000. …
1473ms modo=modelo usados=[1, 2] sin_soporte=['la tasa de interés']

$ candado.py   (5 concurrentes vía RedactorExclusivo, Gemini real)
917ms · 1708ms · 2585ms · 3593ms · 4364ms (todas modo=modelo) → max=4364ms
```
