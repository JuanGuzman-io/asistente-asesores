---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
verdict: verified
date: 2026-10-23
---

# Verify — Consultar la base documental con fuentes

**Verificado.** T17 cierra el único bloqueo del verify anterior: el `detail` de cada 422 es un texto fijo
([C-11](requirements.md#c-11)), sin prefijos de Pydantic y sin la entrada. Pasan 273 pruebas unitarias,
17 e2e y las evals `consultas@v3` sin caída. Con el binario real, los 5 pasos del quickstart dan lo esperado.

## Acceptance criteria → tests

| AC / clause | Critical | Tests | Level | Result |
|---|---|---|---|---|
| AC-1, AC-1/C1 | sí | S-1.1, S-1.1/C1, S-1.2 (`test_cargador`, `test_indice`, `test_arranque_indice::test_s11_*`) | unit, e2e | pass |
| AC-2, AC-2/C1 | no | S-2.1, S-2.1/C1, S-2.2 (`test_duplicados`, `test_fuentes`) | unit | pass |
| AC-3 | sí | S-3.1, S-3.3, S-4.1, S-14.1 (`test_buscador`, `test_fts`, `test_flujo_consulta::test_s4_1_*`); EV-1 0,982 | unit, e2e, eval | pass |
| AC-3/C1 | sí | S-4.1/C1, S-5.2 (`test_flujo_consulta::test_s5_2_*`) | unit, e2e | pass |
| AC-4, AC-4/C1 | sí | S-4.2, S-4.2/C1, `test_T14_S_4_1_*`, `test_flujo_consulta::test_s4_1_*`; EV-4 1,00 | unit, e2e, eval | pass |
| AC-5 | sí | S-5.1, S-5.2 (`test_flujo_consulta::test_s5_2_*`); EV-7 1,00 | unit, e2e, eval | pass |
| AC-5/C1 | sí | S-5.1/C1 (`test_validacion`, `test_gemini`) | unit | pass |
| AC-5/C2 | sí | S-5.2, S-5.2/C1; EV-7 1,00 | unit, eval | pass |
| AC-6, AC-6/C1 | sí | S-6.1, S-6.1/C1 (`test_consultar`, `test_flujo_consulta::test_s4_1_*`); EV-5 1,00 | unit, e2e, eval | pass |
| AC-7 | no | S-7.1, S-7.2 (`test_consultar_api::test_s7_1_el_422_responde_el_mensaje_fijo_exacto_de_su_causa`, 9 casos; prueba de 1.001 caracteres con `detail == MENSAJE_LARGA`); quickstart paso 3 | unit, manual | pass |
| AC-7/C1 | no | S-7.1/C1, S-7.2/C1 (`test_s7_1_cuerpo_invalido_responde_422_problema_sin_consultar_ni_registrar`, `_sin_efectos`, caso de 1.000 caracteres; `test_limites::test_s11_1_c1_*`) | unit | pass |
| AC-8 | no | S-8.1, S-8.1/C1, S-8.2 (`test_buscador`) | unit | pass |
| AC-9, AC-9/C1 | no | S-7.1/C2 (`test_s7_1_c2_el_detail_del_422_no_lleva_texto_de_pydantic`, `test_s7_1_c2_el_detail_del_422_no_repite_el_texto_enviado`), S-7.2/C2 | unit | pass |
| AC-10 | no | S-9.1, S-9.2 (`test_limites`); quickstart paso 4 | unit, manual | pass |
| AC-11 | sí | S-3.2, S-10.1 (`test_flujo_consulta::test_s10_1_*`, `test_el_confidencial_no_se_devuelve_ni_se_registra`); EV-2 1,000; quickstart paso 5 | unit, e2e, eval, manual | pass |
| AC-12, AC-12/C1 | no | S-10.2, S-10.2/C1 (`test_consultar`) | unit | pass |
| AC-13, AC-13/C1 | no | S-10.3, S-10.3/C1 (`test_consultar`, `test_flujo_consulta::test_s10_3_*`) | unit, e2e | pass |
| AC-14, AC-14/C1 | sí | S-11.1, S-11.1/C1, S-11.2 (`test_repositorio`, `test_flujo_consulta::test_s11_1_*`) | unit, e2e | pass |
| AC-15, AC-15/C1 | no | S-13.1, S-13.1/C1 (`test_errores`) | unit | pass |
| AC-16 | sí | S-12.1, S-12.2 (`test_respaldo`, `test_respaldo_e2e::test_s12_*`, `test_T13_D9_*`) | unit, e2e | pass |

Los resultados con Gemini real (T13–T16: `modo` `modelo`, sin mezcla de productos y p95 mediana de 1,3 s
con 5 consultas concurrentes) son del verify anterior. T17 cambia solo el handler del 422 (`http/problemas.py`,
`http/esquemas.py`) y no toca la ruta del modelo. Por eso no se repitieron.

## Suites

| Project | Kind | Result |
|---|---|---|
| asistente-asesores | unit (tester, `tests/server` sin `e2e`) | 273 passed, 9 deselected: 23 casos nuevos de T17 sobre los 250 anteriores |
| asistente-asesores | e2e (tester, `tests/server/e2e`) | 17 passed; cubre los 8 flujos críticos |
| asistente-asesores | evals (`consultas@v3`) | 9 passed: EV-1 0,982, EV-2 1,000, EV-3 0,000, EV-4 1,00, EV-5 1,00, EV-7 1,00; margen mínimo 0,008 (s06). Igual a la línea base |
| asistente-asesores | `format`, `lint`, `typecheck` | PASS |
| asistente-asesores | binario real sin clave (quickstart, puerto 8765) | 5 de 5 pasos como se espera, más 5 variantes del 422 |
| asistente-asesores | gates de T17 (`_log/gates.md`) | todos PASS; `build` SKIPPED (no hay build), `audit` SKIPPED (no cambiaron dependencias) |

`build`: `gates.build` es `none`, así que no hay artefacto que reconstruir; el servidor se probó desde el código.
`node .mandao/bin/mandao.mjs run tests` sigue llamando a `pytest` sin `uv run`; los testers usaron `uv run pytest`.

Dos avisos en las suites, que no son fallas:
- Starlette avisa que su uso de `httpx` está obsoleto.
- `QdrantClient.__del__` reporta un error de sqlite entre hilos al recolectar basura, en
  `test_la_app_abre_un_solo_qdrant_client_y_lo_cierra_al_apagar`. Es ruido del cierre, pero toca el cierre
  de D13 y conviene revisarlo.

## TDD evidence (ADR 0022)

`missingRed`: ninguno. T17 cambió una sola aserción existente: en S-7.2, `"1.000" in detail or "1000" in detail`
pasó a `detail == MENSAJE_LARGA`. Es más estricta. El resto del cambio son pruebas nuevas.

## Security mentions (not blocking)

None.

Seguridad: secretos (`detect-secrets`) y SAST (`bandit`) están cubiertos en local. Las tareas con la etiqueta
`security` son T1, T3, T7, T12 y T14. Las cinco tienen PASS ejecutado en los dos escáneres en `_log/gates.md`.
T17 (`input`, `public-api`, `pii`) también. El log del servidor de la prueba manual no contiene el texto de
ninguna pregunta.

## Product bugs

None.

## Deferred to CI

None.

## Blockers

None.

## Consistency Check

| ID | Type | Finding | Severity | Owner | Status |
|---|---|---|---|---|---|
| CC-1 | PREMISE | D9 ("`HttpOptions(timeout=5000)`") contra el API real, que exige al menos 10 s de plazo de servidor. | critical | dev | resolved 2026-10-23: D9 corregido; T13 verificado con Gemini real |
| CC-2 | CONTRADICTION | NFR-1 ("≤ 3 s con el modelo") contra el candado de `http/rutas.py`. | critical | dev | resolved 2026-10-23: T15; p95 mediana 1,3 s |
| CC-3 | GAP | AC-4 ("solo información encontrada") contra D7, que no daba al modelo la identidad de cada fragmento. | critical | dev | resolved 2026-10-23: T14; verificado con Gemini real |
| CC-4 | CONTRADICTION | EV-2 (dato faltante contaba como "sin soporte") contra AC-5 (soporte parcial). | normal | PO | resolved 2026-10-23: C-9 (PE), EV-7 |
| CC-5 | GAP | AC-7 ("un mensaje claro") contra S-7.1 ("un `detail` legible") y D8, que no fijaban el texto: el `detail` exponía el formato de Pydantic. | normal | PO | resolved 2026-10-23: C-11; S-7.1, S-7.2 y D8 fijan los textos; T17 verificado |

Revisión de este verify: S-7.1 y S-7.2 de `requirements.md` y D8 de `design.md` ya citan C-11 con los tres
textos exactos, y la API los devuelve igual. No hay hallazgos nuevos.

## Evidence

```
$ node .mandao/bin/mandao.mjs run verify-plan MDO-0001
"missingRed":[], "deferred":[], "findings":[], "blockers":[], "securityMentions":[]
securityScans: asistente-asesores · secrets covered · sast covered · pendingCi false

$ node .mandao/bin/mandao.mjs run build asistente-asesores
{"gate":"build","status":"SKIPPED","reason":"gates.build is none: no build by choice"}

_log/gates.md, T17 attempt 1:
scan-markers PASS · format PASS · lint PASS · typecheck PASS · test PASS · build SKIPPED
secrets PASS · audit SKIPPED · sast PASS · metrics PASS
secrets/sast PASS also in T1, T3 (attempt 2), T7, T12, T14

$ uv run pytest tests/server --ignore=tests/server/e2e -q        (tester unit)
273 passed, 9 deselected, 1 warning in 5.65s
$ uv run ruff format --check . / uv run ruff check . / uv run mypy src
158 files already formatted / All checks passed! / Success: no issues found in 34 source files

$ uv run pytest tests/server/evals -s -q -o addopts=""           (tester unit)
EV-1=0.982  EV-2=1.000  EV-3=0.000  EV-4=1.000  EV-5=1.000  EV-7=1.000
margen mínimo al umbral: 0.008 (s06)
9 passed, 1 warning in 3.58s

$ uv run pytest tests/server/e2e -v                               (tester e2e)
17 passed, 2 warnings in 1.10s

$ git show fe65a6c -- tests
1 changed assertion (S-7.2: substring → detail == MENSAJE_LARGA); 59 added lines

$ env -u GEMINI_API_KEY uv run uvicorn src.server.principal:app --port 8765 --workers 1   (quickstart)
Application startup complete.
1.  200 Exitosa, $50.000.000, fuente Productos de Crédito > Crédito Productivo Impulso (+ Crédito Mujer Emprende)
2.  200 "No tengo información suficiente para responder.", fuentes [], Sin información suficiente
3.  {"pregunta":"   "}   422 application/problem+json  detail "La pregunta no puede estar vacía."  requestId
    {"pregunta":""}      422  "La pregunta no puede estar vacía."
    1.001 caracteres     422  "La pregunta no puede superar los 1.000 caracteres."
    {} · {"pregunta":5} · JSON mal formado   422  "El cuerpo debe ser un JSON con el campo pregunta de tipo texto."
4.  text/plain  415 "El Content-Type debe ser application/json."  requestId
5.  token interno / clave temporal  200 "No tengo información suficiente para responder.", fuentes []
$ grep -ciE 'Productivo|llover|token interno|traceback|aaaaaaaaaa' server.log
0
```
