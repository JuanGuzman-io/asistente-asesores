---
schema_version: 1
spec: MDO-0002-consultar-desde-la-interfaz
verdict: blocked        # pending | verified | blocked
date: 2026-10-23
---

# Verify — Consultar desde la interfaz

Lo construido cumple AC-1 (crítico) y AC-2 con evidencia: 67 pruebas de unidad y 4 e2e en verde; el
flujo crítico corrió contra el backend real de MDO-0001. Los secretos quedaron cubiertos con
detect-secrets (00f6c57); el SAST del proyecto `web` es un hueco aceptado por el PE. No hay `PRODUCT_BUG`.
Queda `blocked` solo porque las e2e de T4 siguen diferidas a CI y el repositorio aún no tiene CI.

## Acceptance criteria → tests

| AC / clause | Critical | Tests | Level | Result |
|---|---|---|---|---|
| AC-1 | yes | `App.test.tsx` (S-1.1), `Resultado.test.tsx` (S-2.1), `api.test.ts` (200 válido); e2e "consulta exitosa muestra respuesta, estado y fuente" (S-1.1, S-2.1) | unit + e2e (backend real) | PASS |
| AC-1/C1 | yes | `App.test.tsx`: el botón y Enter no envían otra petición mientras está `procesando` (S-1.2) | unit | PASS |
| AC-1/C2 | yes | `Resultado.test.tsx`: "Sin información suficiente" con "Sin fuentes" (S-2.2) y "Bloqueada por seguridad" (S-2.3); e2e "pregunta sin información muestra estado y sin fuentes" (S-2.2) | unit + e2e (backend real) | PASS |
| AC-1/C3 | yes | `Resultado.test.tsx`: `<b>` y `<a>` salen literales y no crean elementos; Markdown con formato, sin enlaces ni imágenes (S-2.4) | unit | PASS |
| AC-1/C4 | yes | `pregunta.test.ts` (vacía, espacios, 1.000 y 1.001 con NFC y emojis); `App.test.tsx` (botón deshabilitado, contador "0/1.000" y "1.001/1.000", envío de exactamente 1.000) (S-1.3, S-1.4); e2e "caja vacía: botón deshabilitado y ninguna petición" (S-1.3) | unit + e2e | PASS |
| AC-2 | no | `api.test.ts`: 422 con `detail` y `requestId`, 422 sin `detail`, 413 (S-3.1); 500, 415, 503, 404 (S-3.2); sin conexión y tiempo agotado (S-3.3); `App.test.tsx`: 422 con `role=alert` y código de referencia; e2e "error visible con un 422 forzado" (S-3.1) | unit + e2e (422 simulado, D5) | PASS |
| AC-2/C1 | no | `api.test.ts`: 500 con HTML o texto, problem+json, `estado` inválido, fuentes inválidas o cuerpo no JSON no muestran cuerpo, campos ni trazas (S-3.4) | unit | PASS |
| AC-2/C2 | no | `App.test.tsx`: tras un error la pregunta sigue en el campo, editable y con el botón activo; un envío nuevo limpia el error y el resultado anterior (S-4.1) | unit | PASS |

NFR-1 (accesibilidad básica): `App.test.tsx` comprueba la etiqueta "Pregunta", la región
`aria-live=polite` y el contador enlazado con `aria-describedby`. `mandao run trace` no da hallazgos.

### AC-1 — flujo crítico de punta a punta

La e2e del flujo crítico usa `page.route` solo para retener la petición hasta ver "Procesando consulta…"
y luego llama a `route.continue()`: la respuesta que se pinta es la del backend real. La e2e de S-3.1
fuerza un 422 con `route.fulfill` a propósito (D5, C-9); el 422 real lo cubren MDO-0001 (AC-7) y
`api.test.ts`.

## Suites

| Project | Kind | Result |
|---|---|---|
| web | unit (`vitest related`, 4 archivos impactados) | PASS — 67/67 |
| web | e2e (Playwright, backend real de MDO-0001 en :8000) | PASS — 4/4 |
| web | build (`mandao run build web`, antes de las e2e) | PASS |
| web | gates T1 y T2 (format, lint, typecheck, test, build, secrets) | PASS; audit SKIPPED (sin cambio de dependencias); sast no configurado |

## TDD evidence (ADR 0022)

- `missingRed`: ninguno.
- Hay filas RED (vitest, exit 1) antes del verde para T1 (`api.test.ts`), T2 (`Resultado.test.tsx`),
  T3 (`App.test.tsx`) y T5 (`pregunta.test.ts`, `App.test.tsx`). T4 y T6 son e2e sin rojo, como declara
  `tasks.md`.
- Prueba roja cambiada: T5 cambió `tests/web/App.test.tsx`. El cambio quedó reportado y el revisor dio PASS después.
- Ninguna prueba cambió en este verify.

## Security

- **Secretos:** el proyecto `web` no tenía gate. Por decisión del PE (2026-10-23) se agregó el mismo gate
  detect-secrets de MDO-0001 con el `.secrets.baseline` del repo (00f6c57). Lo probé con un canario
  (detectó una clave AWS sembrada) y pasó en T1 y T2 (`_log/gates.md`, intento 2).
- **SAST:** el PE aceptó el hueco y quedó registrado con `mandao approve MDO-0002 security-gaps`. Motivo:
  es un frontend sin código de servidor ni secretos, muestra el texto sin interpretar HTML ni enlaces
  (aba941b) y usa datos irreales. **Mejora futura:** SAST para TypeScript en CI.

## Security mentions (not blocking)

None.

## Product bugs

None.

## Deferred to CI

Las tres corridas e2e de T4 estaban diferidas porque el backend de MDO-0001 no estaba en `main` ni en
:8000 (R-1). Por decisión del PE corrieron aquí contra el backend real, levantado desde la rama
`feat/MDO-0001-…` (aún no está en `main`), y pasaron 4/4. CI todavía tiene que confirmar la e2e completa
y el smoke del flujo crítico cuando MDO-0001 esté en `main`.

## Blockers

- `verify-plan` mantiene "3 run(s) deferred to CI wait for CI (T4)" hasta que CI confirme
  (`verify-plan --ci-confirmed`). `mandao run status MDO-0002 verified` responde `allowed: false` por ese
  motivo.
- El repositorio no tiene CI (no hay `.github/workflows` en esta rama ni en la de MDO-0001), así que
  nada puede confirmar esas corridas todavía. Para desbloquear hace falta una de dos cosas: un
  `/mandao-quick` que agregue un workflow de CI con la e2e y el smoke del flujo crítico, o que la e2e
  pase en CI una vez MDO-0001 esté en `main`. Después se vuelve a correr `/mandao-verify MDO-0002`.

## Observations

- En el Overview de `tasks.md`, T5 y T6 siguen en `[ ]`, pero en Details están en `[x]` y sus commits
  existen (f783067, 7421a5e). Hay que corregir solo la casilla.
- El quickstart coincide con lo construido: los pasos 2 y 3 los comprobé contra el backend real. Queda igual.

## Consistency Check

| ID | Type | Finding | Severity | Owner | Status |
|---|---|---|---|---|---|

No findings. Story, spec y este informe concuerdan: cada AC y cláusula tiene FR, escenario y prueba en
verde. El contrato que usa el cliente coincide con las respuestas reales del backend de MDO-0001.

## Evidence

```
$ node .mandao/bin/mandao.mjs run tests web src/web/src/App.tsx src/web/src/Compositor.tsx src/web/src/Resultado.tsx src/web/src/api.ts src/web/src/main.tsx src/web/src/pregunta.ts
Test Files  4 passed (4)
Tests  67 passed (67)
{"status":"PASS", ... "exitCode":0}

$ node .mandao/bin/mandao.mjs run build web
✓ built in 511ms
{"status":"PASS", ... "exitCode":0}

$ npm --prefix src/web run e2e        # backend: uv run --no-sync uvicorn src.server.principal:app --port 8000 --workers 1 (worktree MDO-0001)
Running 4 tests using 1 worker
4 passed (3.8s)

$ node .mandao/bin/mandao.mjs run gates MDO-0002 T1
{"task":"T1","attempt":2,"passed":true,"results":[{"gate":"format","status":"PASS"},{"gate":"lint","status":"PASS"},{"gate":"typecheck","status":"PASS"},{"gate":"test","status":"PASS"},{"gate":"build","status":"PASS"},{"gate":"secrets","status":"PASS"},{"gate":"audit","status":"SKIPPED","reason":"no dependency change"}],"notConfigured":["sast","metrics"]}

$ node .mandao/bin/mandao.mjs run gates MDO-0002 T2
{"task":"T2","attempt":2,"passed":true,"results":[{"gate":"format","status":"PASS"},{"gate":"lint","status":"PASS"},{"gate":"typecheck","status":"PASS"},{"gate":"test","status":"PASS"},{"gate":"build","status":"PASS"},{"gate":"secrets","status":"PASS"},{"gate":"audit","status":"SKIPPED","reason":"no dependency change"}],"notConfigured":["sast","metrics"]}

$ (canario en src/web/zz-canary.txt, borrado después) detect-secrets-hook ...
ERROR: Potential secrets about to be committed to git repo!
Secret Type: AWS Access Key   Location: zz-canary.txt:1

$ node .mandao/bin/mandao.mjs approve MDO-0002 security-gaps --reason "..."
{"approved":true,"step":"security-gaps","by":"Juan D. Guzmán","at":"2026-10-23T20:30:44.949Z"}

$ node .mandao/bin/mandao.mjs run trace MDO-0002
{"rows":[...8 filas AC/cláusula...],"findings":[],"issues":[]}
```
