---
schema_version: 1
spec: MDO-0002-consultar-desde-la-interfaz
status: approved
---

# Tasks — Consultar desde la interfaz

Cuatro tareas en orden: el proyecto `web` con sus gates y el cliente de la API, el resultado, la
pantalla que los une y, al final, las tres e2e con Playwright contra el backend real de MDO-0001. Las
tres primeras usan un backend simulado según el contrato y empiezan con pruebas rojas.

## Overview

### AC-2 — Ver errores

- [x] T1 [AC-2] El proyecto web existe y el cliente de la API traduce cada respuesta del servicio — `src/web/package.json`

**Checkpoint:** `npm --prefix src/web test -- api` passes (T1); this confirms AC-2 before the next group.

### AC-1 — Realizar consulta y ver la respuesta

- [x] T2 [AC-1] El resultado muestra respuesta, estado distinguible y fuentes como texto — `src/web/src/Resultado.tsx`
- [ ] T5 [AC-1] La pregunta vacía o de más de 1.000 caracteres no se envía y un contador muestra el largo — `src/web/src/pregunta.ts`

**Checkpoint:** `npm --prefix src/web test -- Resultado` and `npm --prefix src/web test -- pregunta App` passes (T2, T5); this confirms AC-1 before the next group.

### AC-1, AC-2 — Realizar consulta y ver la respuesta; Ver errores

- [x] T3 [AC-1, AC-2] La pantalla consulta, muestra el procesamiento y los errores, y conserva la pregunta — `src/web/src/App.tsx`
- [x] T4 [AC-1, AC-2] Tres pruebas de punta a punta pasan con el backend real — `src/web/playwright.config.ts`
- [ ] T6 [AC-1, AC-2] Las e2e de caja vacía y error visible reemplazan la de pregunta vacía — `tests/web/e2e/consultar.spec.ts`

**Checkpoint:** `npm --prefix src/web test -- App` and `npm --prefix src/web run e2e` passes (T3, T4, T6); this confirms AC-1, AC-2 before the next group.

## Details

### [x] T1 — El proyecto web existe y el cliente de la API traduce cada respuesta del servicio

- **What:** crea el proyecto `web` en `src/web` ([D1](spec.md#d1), [D2](spec.md#d2), [D7](spec.md#d7)) con
  los gates de [D6](spec.md#d6), y el cliente `consultar()` que nunca lanza ([D3](spec.md#d3)).
- **Done when:**
  - S-3.1, S-3.2, S-3.3 y S-3.4 se cumplen en el cliente, con `fetch` simulado y el tiempo límite inyectado; un 200 válido devuelve `{ tipo: "ok" }` con respuesta, fuentes y estado.
  - El resultado de error nunca trae el cuerpo recibido ni nombres de campos (S-3.4/C1).
  - `npm ci` instala las versiones de D7 sin servicios pagos; el informe de licencias y `npm audit` quedan adjuntos a los gates de la tarea, y toda licencia fuera de MIT, Apache-2.0, BSD y la excepción de C-1 detiene la tarea.
  - `projects[].gates` de `web` en `.mandao/config.yml` declara los seis gates de D6 (aprobados por el PE, [C-5](spec.md#c-5)) y los seis pasan; un hallazgo de `npm audit` se acepta solo si no es alcanzable, con su motivo y aprobación del PE; los gates de `asistente-asesores` no cambian.

```yaml
project: web
kind: feat
tier: standard
files: [src/web/package.json, src/web/package-lock.json, src/web/vite.config.ts, src/web/tsconfig.json, src/web/eslint.config.js, src/web/.prettierrc, src/web/.prettierignore, src/web/index.html, src/web/src/main.tsx, src/web/src/api.ts, tests/web/api.test.ts, .gitignore, .mandao/config.yml, .mandao/mandao.lock]
exemplar: none (proyecto nuevo; api.ts será el exemplar de cliente)
ac: [AC-2, AC-2/C1]
scenarios: [S-3.1, S-3.2, S-3.3, S-3.4, S-3.4/C1]
test_levels: { S-3.1: unit, S-3.2: unit, S-3.3: unit, S-3.4: unit, S-3.4/C1: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [input, public-api, security]
decisions: [D1, D2, D3, D6, D7]
depends_on: []
parallel_safe: false
verify: npm --prefix src/web test -- api
```

### [x] T2 — El resultado muestra respuesta, estado distinguible y fuentes como texto

- **What:** el componente `Resultado` pinta la respuesta, el rótulo del estado y la lista de fuentes
  ([D3](spec.md#d3), [D4](spec.md#d4)).
- **Done when:**
  - S-2.1 se cumple: respuesta, "Exitosa" y "Productos de Crédito > Crédito Productivo Impulso" con su fragmento.
  - S-2.2 y S-2.3 se cumplen: cada estado tiene su rótulo y sin fuentes se ve "Sin fuentes" (S-2.2/C2, S-2.3/C2).
  - S-2.4 se cumple: `<b>` y `<a>` del servicio aparecen literales, sin elementos creados (S-2.4/C3).
  - Los elementos se encuentran por rol o texto (NFR-1).

```yaml
project: web
kind: feat
tier: standard
files: [src/web/src/Resultado.tsx, tests/web/Resultado.test.tsx, src/web/vite.config.ts, src/web/tsconfig.json, src/web/AGENTS.md, .mandao/config.yml, .mandao/mandao.lock]
exemplar: src/web/src/api.ts
ac: [AC-1, AC-1/C2, AC-1/C3]
scenarios: [S-2.1, S-2.2, S-2.2/C2, S-2.3, S-2.3/C2, S-2.4, S-2.4/C3]
test_levels: { S-2.1: unit, S-2.2: unit, S-2.2/C2: unit, S-2.3: unit, S-2.3/C2: unit, S-2.4: unit, S-2.4/C3: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [ui, security]
decisions: [D3, D4]
depends_on: [T1]
parallel_safe: false
verify: npm --prefix src/web test -- Resultado
```

### [x] T3 — La pantalla consulta, muestra el procesamiento y los errores, y conserva la pregunta

- **What:** `App` con el formulario, `EstadoProcesamiento` y el área de resultado o error, sobre el
  cliente de T1 y el `Resultado` de T2 ([D3](spec.md#d3)); `main.tsx` la monta.
- **Done when:**
  - S-1.1 se cumple: "Procesando consulta…" mientras espera y `completado` al llegar la respuesta.
  - S-1.2 se cumple: con la consulta en `procesando`, ni el botón ni el teclado envían otra petición (S-1.2/C1).
  - Un error del cliente se ve con `role="alert"` y su código de referencia (S-3.1 en pantalla).
  - S-4.1 se cumple: tras un error la pregunta sigue en el campo y el botón está habilitado (S-4.1/C2); un nuevo envío limpia el resultado anterior.
  - El campo tiene la etiqueta "Pregunta" y la región de estado es `aria-live="polite"` (NFR-1).

```yaml
project: web
kind: feat
tier: standard
files: [src/web/src/App.tsx, src/web/src/main.tsx, tests/web/App.test.tsx, src/web/vite.config.ts, src/web/tsconfig.json, src/web/AGENTS.md]
exemplar: src/web/src/Resultado.tsx
ac: [AC-1, AC-1/C1, AC-2, AC-2/C2]
scenarios: [S-1.1, S-1.2, S-1.2/C1, S-3.1, S-4.1, S-4.1/C2]
test_levels: { S-1.1: unit, S-1.2: unit, S-1.2/C1: unit, S-3.1: unit, S-4.1: unit, S-4.1/C2: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [ui]
decisions: [D3]
depends_on: [T1, T2]
parallel_safe: false
verify: npm --prefix src/web test -- App
```

### [x] T4 — Tres pruebas de punta a punta pasan con el backend real

- **What:** Playwright con tres escenarios contra el backend real de MDO-0001 y la interfaz en
  `vite dev` ([D5](spec.md#d5), [C-3](spec.md#c-3)).
- **Done when:**
  - Consulta exitosa: S-1.1 y S-2.1 con la pregunta del Crédito Productivo Impulso.
  - Pregunta vacía: S-3.1, error visible con código de referencia.
  - Pregunta sin información: S-2.2 con "¿Va a llover mañana en Bogotá?".
  - `npm run e2e` arranca la interfaz, usa un backend ya corriendo en el puerto 8000 y no es gate.

```yaml
project: web
kind: chore
tier: standard
files: [src/web/playwright.config.ts, src/web/package.json, src/web/package-lock.json, tests/web/e2e/consultar.spec.ts, tests/web/e2e/tsconfig.json, src/web/tsconfig.json, src/web/AGENTS.md, .gitignore]
exemplar: tests/web/App.test.tsx
ac: [AC-1, AC-2]
scenarios: [S-1.1, S-2.1, S-2.2, S-3.1]
test_levels: { S-1.1: e2e, S-2.1: e2e, S-2.2: e2e, S-3.1: e2e }
partial_failure_tests: []
evidence: none
risk_tags: [public-api]
decisions: [D5]
depends_on: [T3]
parallel_safe: false
verify: npm --prefix src/web run e2e
```

**Notes:** T4 necesita MDO-0001 en `main` y esta rama actualizada con él (R-1). Sin TDD rojo: prueba un comportamiento que T1–T3 ya construyeron contra el backend simulado.

### [x] T5 — La pregunta vacía o de más de 1.000 caracteres no se envía y un contador muestra el largo

- **What:** `pregunta.ts` con la regla de largo de [D8](spec.md#d8); `Compositor` deshabilita el envío y
  muestra el contador; el manejador de `App` no envía una pregunta inválida ([C-9](spec.md#c-9)).
- **Done when:**
  - S-1.3 se cumple: con el campo vacío o solo espacios el botón está deshabilitado, el contador dice "0/1.000" y ni el clic ni Enter sacan una petición; al escribir un carácter el botón se habilita.
  - S-1.4 se cumple: con 1.001 puntos de código el contador dice "1.001/1.000", marcado como excedido, y no sale ninguna petición; con exactamente 1.000, aunque haya espacios a los lados, "é" descompuesta o emojis, se envía.
  - `largoPregunta` y `preguntaValida` dan los mismos resultados que el backend en los casos de P4.
  - S-3.1 en pantalla usa una pregunta válida con el 422 simulado; S-1.1, S-1.2 y S-4.1 siguen pasando.
  - El contador se encuentra por texto y está asociado al campo con `aria-describedby` (NFR-1); `src/web/AGENTS.md` ya no dice que la pregunta vacía llega al backend.

```yaml
project: web
kind: feat
tier: standard
files: [src/web/src/pregunta.ts, src/web/src/Compositor.tsx, src/web/src/App.tsx, src/web/src/estilos.css, tests/web/pregunta.test.ts, tests/web/App.test.tsx, src/web/AGENTS.md]
exemplar: src/web/src/api.ts
ac: [AC-1, AC-1/C4]
scenarios: [S-1.3, S-1.3/C4, S-1.4, S-1.4/C4]
test_levels: { S-1.3: unit, S-1.3/C4: unit, S-1.4: unit, S-1.4/C4: unit }
partial_failure_tests: []
evidence: tdd
risk_tags: [input, ui]
decisions: [D8]
depends_on: [T3]
parallel_safe: false
verify: npm --prefix src/web test -- pregunta App
```

### [x] T6 — Las e2e de caja vacía y error visible reemplazan la de pregunta vacía

- **What:** en `tests/web/e2e/consultar.spec.ts`, la prueba de pregunta vacía se reemplaza por las dos de
  [D5](spec.md#d5) (enmienda C-9).
- **Done when:**
  - Caja vacía: el botón está deshabilitado y no sale ninguna petición a `/api/consultar` (S-1.3).
  - Error visible: con una pregunta válida y la respuesta forzada a 422 con `page.route`, se ven el `detail` y "Código de referencia: …" (S-3.1).
  - Las e2e de consulta exitosa y sin información siguen pasando contra el backend real.

```yaml
project: web
kind: chore
tier: standard
files: [tests/web/e2e/consultar.spec.ts, src/web/AGENTS.md]
exemplar: tests/web/e2e/consultar.spec.ts
ac: [AC-1/C4, AC-2]
scenarios: [S-1.3, S-3.1]
test_levels: { S-1.3: e2e, S-3.1: e2e }
partial_failure_tests: []
evidence: none
risk_tags: [ui]
decisions: [D5]
depends_on: [T5]
parallel_safe: false
verify: npm --prefix src/web run e2e
```

**Notes:** T6 necesita el backend de MDO-0001 corriendo (R-1). Sin TDD rojo: prueba contra el backend lo que T5 ya construyó con pruebas rojas.
