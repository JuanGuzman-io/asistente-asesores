---
schema_version: 1
spec: MDO-0002-consultar-desde-la-interfaz
verdict: verified       # pending | verified | blocked
date: 2026-10-23
---

# Verify — Consultar desde la interfaz

Verificado. AC-1 (crítico) y AC-2 cumplen con evidencia sobre 509aa7f, el último commit con código:
67/67 pruebas de unidad, build, format, lint y typecheck en verde en local. La CI del PR #2 corrió sobre
ese mismo commit las e2e diferidas de T4 contra el backend real y pasaron 4/4 (corrida 40025377094).
No hay `PRODUCT_BUG` ni bloqueos.

## Acceptance criteria → tests

| AC / clause | Critical | Tests | Level | Result |
|---|---|---|---|---|
| AC-1 | yes | `App.test.tsx` (S-1.1: procesando → completado), `Resultado.test.tsx` (S-2.1: respuesta, Exitosa, fuente "documento > sección"), `api.test.ts` (S-2.1: 200 válido); e2e `@S-1.1 @S-2.1` "consulta exitosa muestra respuesta, estado y fuente" | unit + e2e (backend real, CI) | PASS |
| AC-1/C1 | yes | `App.test.tsx`: S-1.2/C1, ni el botón ni Enter envían otra petición mientras está `procesando` | unit | PASS |
| AC-1/C2 | yes | `Resultado.test.tsx`: S-2.2 "Sin información suficiente" con "Sin fuentes", S-2.2/C2 rótulo distinto de Exitosa, S-2.3 y S-2.3/C2 "Bloqueada por seguridad" y un solo rótulo por estado; e2e `@S-2.2` "pregunta sin información muestra estado y sin fuentes" | unit + e2e (backend real, CI) | PASS |
| AC-1/C3 | yes | `Resultado.test.tsx`: S-2.4 y S-2.4/C3, `<b>` y `<a>` salen literales y no crean elementos (también en documento y sección); AC-1/C3, enlaces, URL e imágenes Markdown quedan como texto | unit | PASS |
| AC-1/C4 | yes | `pregunta.test.ts` (S-1.4: 1.000 en NFC y NFD, emojis, espacios laterales, 1.001 inválido); `App.test.tsx` (S-1.3/C4 botón deshabilitado y Enter sin petición, S-1.4 contador "1.001/1.000" y campo marcado, S-1.4/C4); e2e `@S-1.3` "caja vacía: botón deshabilitado y ninguna petición" | unit + e2e (CI) | PASS |
| AC-2 | no | `api.test.ts`: S-3.1 (422 con `detail` y `requestId`, 422 sin `detail`, 413), S-3.2 (500), S-3.3 (sin conexión y tiempo agotado); `App.test.tsx`: S-3.1 con `role=alert` y código de referencia; e2e `@S-3.1` "error visible con un 422 forzado" | unit + e2e (422 simulado, D5; CI) | PASS |
| AC-2/C1 | no | `api.test.ts`: S-3.4 y S-3.4/C1, un 500 con HTML, texto o problem+json, un `estado` inválido, fuentes inválidas o un cuerpo no JSON no muestran cuerpo, campos ni trazas | unit | PASS |
| AC-2/C2 | no | `App.test.tsx`: S-4.1/C2, tras un error la pregunta sigue editable y el botón activo; S-4.1, un envío nuevo limpia el error y el resultado anteriores | unit | PASS |

NFR-1 (accesibilidad básica): `App.test.tsx` (pruebas NFR-1) comprueba la etiqueta "Pregunta", la región
`aria-live=polite` y el contador enlazado con `aria-describedby`. `verify-plan` da `findings: []`.

### AC-1: flujo crítico de punta a punta

En CI, el job `frontend` levanta el backend real de MDO-0001 en :8000 (modo extractivo, un worker) y
corre `npm run e2e`. La e2e del flujo crítico usa `page.route` solo para retener la petición hasta ver
"Procesando consulta…". Después llama a `route.continue()`, así que lo que se pinta es la respuesta real.
La e2e de S-3.1 fuerza un 422 a propósito (D5, C-9). El 422 real lo cubren MDO-0001 (AC-7) y
`api.test.ts`.

Hoy, en local, un smoke con curl contra el backend real devolvió $50.000.000 con la fuente "Productos de
Crédito > Crédito Productivo Impulso". La pregunta fuera de alcance devolvió "No tengo información
suficiente para responder.", `fuentes: []` y "Sin información suficiente".

## Suites

| Project | Kind | Result |
|---|---|---|
| web | unit (`mandao run tests`, 4 de 4 archivos impactados), HEAD 509aa7f | PASS: 67/67 |
| web | build (`mandao run build web`), HEAD 509aa7f | PASS |
| web | format, lint y typecheck, HEAD 509aa7f | PASS |
| web | unit, build y e2e (Playwright, backend real), CI del PR #2 sobre 509aa7f | PASS: 67/67 y 4/4 |
| web | e2e local sobre 509aa7f | NOT RUN: el guardián de recursos lo bloqueó (3,5 GB libres, se piden 4,5 GB); la cubre CI |
| asistente-asesores | backend, evals, secrets, sast (bandit), CI del PR #2 sobre 509aa7f | PASS |

## TDD evidence (ADR 0022)

- `missingRed`: ninguno.
- T1, T2, T3 y T5 tienen filas RED (vitest, exit 1) antes del verde. T4 y T6 son e2e sin rojo, como
  declara `tasks.md`.
- Prueba roja cambiada: T5 cambió `tests/web/App.test.tsx`. Ya se informó y el revisor dio PASS.
- Este verify no cambió ninguna prueba. El merge 509aa7f no toca `tests/`.

## Security

- **Secretos:** cubiertos. T1 y T2 llevan el tag `security` y tienen PASS ejecutado del gate
  detect-secrets (`_log/gates.md`, intento 2 de cada una). En CI el gate corre sobre todo el repositorio.
- **SAST del proyecto `web`:** `unknown`. Es un hueco aceptado por el PE (`mandao approve MDO-0002
  security-gaps`, 2026-10-23T20:30:44Z). Bandit en CI cubre solo el backend Python. **Mejora futura:**
  SAST para TypeScript en CI.

## Security mentions (not blocking)

None.

## Product bugs

None.

## Deferred to CI

Las tres corridas e2e de T4 (`tests/web/e2e/consultar.spec.ts`) quedaron confirmadas por la CI del PR #2.
Primero pasaron sobre 0f66689 (corrida 40024670663, "4 passed (12.1s)"). Después, ya con el renombre a
W+IA (merge de `draft/quick-renombrar-w-ia`), pasaron sobre 509aa7f (corrida 40025377094, "4 passed
(12.0s)"). Por eso este verify usa `--ci-confirmed`. Después de 509aa7f solo cambiaron documentos del
spec (`story.md`, `verify-report.md` y `_log/`).

## Blockers

None.

## Observations

- La spec (C-7 y la sección de impacto en `ux.md`, `spec.md:329` y `spec.md:388-389`) todavía llama
  "Bot-W" a la interfaz. Desde 509aa7f el código y `src/web/AGENTS.md` dicen "W+IA". Es una decisión
  visual (fuera de alcance de los AC) y `/mandao-close` debe llevarla a `ux.md`.
- El commit 7492298 usa el emoji 💄, pero la guía pide 🎨 para `style`. No se corrige porque reescribir
  historia no compensa.
- El quickstart coincide con el backend: los pasos 2 y 3 se comprobaron hoy con curl. Los pasos de UI
  (1, 4 y 5) los cubren las e2e de CI y las pruebas de unidad. Queda igual.

## Consistency Check

| ID | Type | Finding | Severity | Owner | Status |
|---|---|---|---|---|---|

No findings. Story, spec y este informe concuerdan: cada AC y cada cláusula tienen FR, escenario y prueba
en verde. El contrato que usa el cliente coincide con las respuestas reales del backend de MDO-0001. El
cambio de nombre (Bot-W → W+IA) no toca ningún AC ni FR y queda en Observations.

## Evidence

```
$ node .mandao/bin/mandao.mjs run verify-plan MDO-0002
"missingRed":[], "findings":[], "blockers":["3 run(s) deferred to CI wait for CI (T4, T4, T4)"],
"securityScans":[{"project":"asistente-asesores","secrets":"covered","sast":"covered"},{"project":"web","secrets":"covered","sast":"unknown"}]

$ gh run view 40024670663 --json headSha,conclusion,jobs
{"conclusion":"success","headSha":"0f6668901af8e2e2347a12b452793258d188e8a0","jobs":[
 {"name":"backend","conclusion":"success"  (test sin red, secrets, sast: success)},
 {"name":"frontend","conclusion":"success" (test, Levantar el backend, e2e: success)},
 {"name":"evals","conclusion":"success"}]}
frontend  test  Test Files  4 passed (4)
frontend  test       Tests  67 passed (67)
frontend  e2e   4 passed (12.1s)

$ gh run view 40025377094 --json headSha,conclusion,jobs
{"conclusion":"success","headSha":"509aa7fdf6fbc723b36593477c87067604bacc56","jobs":[
 {"name":"evals","conclusion":"success"},{"name":"backend","conclusion":"success"},{"name":"frontend","conclusion":"success"}]}
frontend  test  Test Files  4 passed (4)
frontend  test       Tests  67 passed (67)
frontend  e2e   4 passed (12.0s)

$ git diff --stat 509aa7f HEAD   # solo documentos del spec
_log/costs.yml | _log/execution.md | story.md | verify-report.md

$ node .mandao/bin/mandao.mjs run tests web src/web/src/{App,Compositor,Resultado,Orbe,main}.tsx src/web/src/{api,pregunta}.ts   # HEAD 509aa7f
Test Files  4 passed (4)
Affected  4 of 4 test files (related to 7 files)
Tests  67 passed (67)
{"status":"PASS","exitCode":0,"impact":"configured"}

$ node .mandao/bin/mandao.mjs run build web   # HEAD 509aa7f
✓ built in 191ms
{"status":"PASS","exitCode":0}

$ npm --prefix src/web run format:check   → All matched files use Prettier code style!  (exit 0)
$ npm --prefix src/web run lint           → (sin salida)  (exit 0)
$ npm --prefix src/web run typecheck      → (sin salida)  (exit 0)

$ npm --prefix src/web run e2e   # local, HEAD 509aa7f
resource-guard: available RAM 3544 MB < 4500 MB required for e2e → blocked (no se forzó con RG_FORCE)

$ curl -s -X POST localhost:8000/api/consultar -d '{"pregunta":"¿Cuál es el monto máximo del Crédito Productivo Impulso?"}'
… "Monto máximo | $50.000.000" … "fuentes":[{"documento":"Productos de Crédito","seccion":"Crédito Productivo Impulso", …}, …]
$ curl -s -X POST localhost:8000/api/consultar -d '{"pregunta":"¿Va a llover mañana en Bogotá?"}'
{"respuesta":"No tengo información suficiente para responder.","fuentes":[],"estado":"Sin información suficiente"}

$ node .mandao/bin/mandao.mjs run security-scanning
web: secrets covered (detect-secrets local + CI), sast unknown (approved gap)

$ node .mandao/bin/mandao.mjs run verify-plan MDO-0002 --ci-confirmed
"missingRed":[], "findings":[], "blockers":[]

$ node .mandao/bin/mandao.mjs run status MDO-0002 verified --ci-confirmed
{"from":"in-progress","to":"verified","allowed":true,"problems":[]}
```
