---
schema_version: 1
spec: MDO-0002-consultar-desde-la-interfaz
depth: lite
projects: [web]
status: approved
writes_data: no
---

# Spec — Consultar desde la interfaz

Una aplicación React + TypeScript (Vite) en `src/web` envía la pregunta a `POST /api/consultar` y
muestra el estado de procesamiento, la respuesta, el estado y las fuentes, o un error claro. Un
cliente de la API traduce cada respuesta del contrato de MDO-0001 a un resultado que la pantalla
solo pinta; las pruebas usan un backend simulado y tres e2e con Playwright contra el backend real.

## Functional requirements

<a id="fr1"></a>
### FR-1 — Enviar la consulta y mostrar el procesamiento
Serves: AC-1, AC-1/C1, AC-1/C4
Projects: web

La pantalla tiene un campo de pregunta con etiqueta y un botón `Consultar`. Al enviar, el estado de
procesamiento pasa de `inactivo` a `procesando`, visible en pantalla, y el botón queda deshabilitado
hasta que la consulta termina en `completado` o `error`. El envío también queda desactivado mientras la
pregunta no es válida: vacía, solo con espacios o de más de 1.000 caracteres, contados como el backend
(NFC, sin espacios a los lados, en puntos de código; [D8](#d8)). Un contador "N/1.000" muestra ese largo.
La validación del backend no cambia (MDO-0001 AC-7).

#### S-1.1 — Procesamiento visible
- **Given** la interfaz abierta en `inactivo`
- **When** el asesor escribe "¿Cuál es el monto máximo del Crédito Productivo Impulso?" y pulsa `Consultar`
- **Then** ve "Procesando consulta…" mientras el servicio no responde, y el estado pasa a `completado` cuando llega la respuesta

#### S-1.2 — Sin doble envío
- **Given** una consulta en `procesando`
- **When** el asesor pulsa `Consultar` otra vez o envía el formulario con el teclado
- **Then** **BUT it must NOT** salir una segunda petición a `/api/consultar` (C1)

#### S-1.3 — Pregunta vacía sin envío
- **Given** el campo vacío, o con solo espacios, tabulaciones o saltos de línea
- **When** el asesor mira el botón, lo pulsa o pulsa Enter en el campo
- **Then** el botón está deshabilitado y el contador dice "0/1.000"; al escribir un carácter que no sea espacio, el botón se habilita
- **BUT it must NOT** salir ninguna petición a `/api/consultar` (C4)

#### S-1.4 — Límite de 1.000 caracteres
- **Given** una pregunta que, sin espacios a los lados y normalizada a NFC, tiene 1.001 puntos de código
- **When** el asesor mira el contador, pulsa el botón o pulsa Enter
- **Then** el contador dice "1.001/1.000", marcado como excedido, y el botón está deshabilitado; con exactamente 1.000 puntos de código el envío se permite, aunque haya espacios a los lados, una "é" escrita como "e" más tilde combinable o emojis, que cuentan 1 cada uno
- **BUT it must NOT** salir ninguna petición a `/api/consultar` (C4)

<a id="fr2"></a>
### FR-2 — Mostrar respuesta, estado y fuentes
Serves: AC-1, AC-1/C2, AC-1/C3
Projects: web

Con una respuesta 200 la pantalla muestra la `respuesta`, el `estado` con su texto exacto y una lista
de fuentes con documento, sección y fragmento. Cada estado tiene su propio rótulo; sin fuentes se
muestra "Sin fuentes". Todo texto que llega del servicio se pinta como texto, nunca como HTML.

#### S-2.1 — Consulta exitosa con fuentes
- **Given** el servicio responde `{"respuesta": "El monto máximo es $50.000.000.", "fuentes": [{"documento": "Productos de Crédito", "seccion": "Crédito Productivo Impulso", "fragmento": "…"}], "estado": "Exitosa"}`
- **When** termina la consulta
- **Then** se ven la respuesta, el estado "Exitosa" y la fuente "Productos de Crédito > Crédito Productivo Impulso" con su fragmento

#### S-2.2 — Sin información suficiente
- **Given** el servicio responde "No tengo información suficiente para responder.", `fuentes` vacío y estado `Sin información suficiente`
- **When** termina la consulta
- **Then** se ven el mensaje y "Sin fuentes"
- **AND IT MUST** verse el estado "Sin información suficiente" con un rótulo distinto del de "Exitosa" (C2)

#### S-2.3 — Bloqueada por seguridad
- **Given** el servicio responde estado `Bloqueada por seguridad` sin fuentes
- **When** termina la consulta
- **Then** se ven la respuesta y el estado "Bloqueada por seguridad" con su propio rótulo
- **AND IT MUST** mostrarse igual que los otros estados aunque el backend aún no lo produzca (C2)

#### S-2.4 — Texto del servicio como texto
- **Given** una respuesta y un fragmento que contienen `<b>hola</b>` y `<a href="https://ejemplo.com">x</a>`
- **When** se muestran
- **Then** **BUT it must NOT** crearse elementos `b` ni `a`: el texto aparece literal (C3)

<a id="fr3"></a>
### FR-3 — Errores claros
Serves: AC-2, AC-2/C1
Projects: web

El cliente traduce cada falla a un mensaje fijo en español y al código de referencia (`requestId`)
cuando el servicio lo envía; el estado de procesamiento queda en `error`. Mensajes:

| Caso | Mensaje |
|---|---|
| 422 con `detail` | el `detail` del servicio (MDO-0001 lo escribe legible) |
| 422 sin `detail` | "Revisa la pregunta e intenta de nuevo." |
| 413 | "La pregunta es demasiado larga." |
| 415, 500, otro código o cuerpo que no cumple el contrato | "El servicio tuvo un problema. Intenta de nuevo en unos minutos." |
| Sin conexión | "No se pudo conectar con el servicio. Verifica que esté en ejecución." |
| Sin respuesta en 30 s | "El servicio tardó demasiado en responder. Intenta de nuevo." |

#### S-3.1 — Pregunta vacía rechazada
- **Given** el servicio responde 422 `application/problem+json` con `detail` "La pregunta no puede estar vacía." y `requestId` "abc-123"
- **When** termina la consulta
- **Then** se ven ese mensaje y "Código de referencia: abc-123", y el procesamiento queda en `error`

#### S-3.2 — Error del servicio
- **Given** el servicio responde 500 `application/problem+json` con `requestId`
- **When** termina la consulta
- **Then** se ve el mensaje genérico de problema del servicio y el código de referencia

#### S-3.3 — Sin conexión o sin respuesta
- **Given** la petición falla por red, o no hay respuesta en 30 s
- **When** termina la espera
- **Then** se ve el mensaje de conexión o de tiempo agotado, sin código de referencia

#### S-3.4 — Sin detalles técnicos
- **Given** un 500 con cuerpo HTML o texto plano, o un 200 cuyo `estado` no es uno de los tres
- **When** termina la consulta
- **Then** se ve el mensaje genérico de problema del servicio
- **BUT it must NOT** mostrarse el cuerpo recibido, trazas, rutas ni nombres de campos (C1)

<a id="fr4"></a>
### FR-4 — Conservar la pregunta
Serves: AC-2/C2
Projects: web

Al enviar, la caja se vacía y la pregunta enviada queda visible en la conversación; si la consulta
termina en error, la pregunta vuelve a la caja para corregirla o reintentar, salvo que el asesor ya haya
escrito otra. Un nuevo envío limpia el resultado o el error anterior antes de mostrar `procesando`
(enmendado por [C-9](#c-9) para el diseño de chat de C-6 y C-7; antes, ni el error ni el fin de la
consulta borraban el campo).

#### S-4.1 — Reintento tras un error
- **Given** una consulta que terminó en error
- **When** el asesor mira el campo de pregunta
- **Then** **AND IT MUST** seguir el texto que escribió, editable, y el botón habilitado (C2)

<a id="nfr1"></a>
### NFR-1 — Accesibilidad básica
Serves: AC-1, AC-2
Projects: web

El campo tiene etiqueta ("Pregunta"); el procesamiento, el resultado y el error se anuncian en una
región `aria-live="polite"`, y el error con `role="alert"`. Se mide en las pruebas: 100 % de los
elementos se encuentran por rol o etiqueta (`getByRole`, `getByLabelText`), nunca por clase o id.

## AC → FR matrix

| AC | Clause | FR / scenario | Status |
|---|---|---|---|
| AC-1 | main | FR-1 / S-1.1; FR-2 / S-2.1 | covered |
| AC-1 | C1: sin doble envío | FR-1 / S-1.2 | covered |
| AC-1 | C2: estado visible y distinguible | FR-2 / S-2.2, S-2.3 | covered |
| AC-1 | C3: texto, no HTML | FR-2 / S-2.4 | covered |
| AC-1 | C4: sin envío vacío ni de más de 1.000 caracteres | FR-1 / S-1.3, S-1.4 | covered |
| AC-2 | main | FR-3 / S-3.1, S-3.2, S-3.3 | covered |
| AC-2 | C1: sin detalles técnicos | FR-3 / S-3.4 | covered |
| AC-2 | C2: conservar la pregunta | FR-4 / S-4.1 | covered |

## Decisions

<a id="d1"></a>
### D1 — Proyecto `web` autocontenido en `src/web`, pruebas en `tests/web`

- `package.json`, `vite.config.ts`, `tsconfig.json` e `index.html` viven en `src/web` (el `path` del
  proyecto en `.mandao/config.yml`, decisión del PE), así los gates corren desde ahí. Las pruebas van
  en `tests/web/` (`standards.md`: `tests/` espeja `src/`) y Vitest las incluye con `../../tests/web/**`.
- Rechazadas: `package.json` en la raíz (mezcla el proyecto Node con el Python de `.`); pruebas dentro
  de `src/web` (contradice `standards.md`).

<a id="d2"></a>
### D2 — Proxy de Vite hacia el backend

- El cliente llama a la ruta relativa `/api/consultar`; en desarrollo y en `vite preview` el proxy de
  Vite la reenvía a `http://127.0.0.1:8000` (variable `API_URL` para cambiarla). Mismo origen: sin CORS.
- Rechazadas: CORS en FastAPI y servir `dist/` desde FastAPI (las dos tocan `src/server/http`, de
  MDO-0001, todavía abierta).

<a id="d3"></a>
### D3 — Un cliente de la API que nunca lanza

- `consultar(pregunta, opciones)` en `src/web/src/api.ts` devuelve
  `{ tipo: "ok", resultado } | { tipo: "error", mensaje, codigoReferencia? }`: valida el 200 contra el
  contrato (los tres estados, `fuentes` con tres textos) y traduce las fallas a la tabla de FR-3.
  Tiempo límite con `AbortSignal.timeout(30_000)`, inyectable para las pruebas.
- La pantalla (`App.tsx`) guarda `EstadoProcesamiento` (`inactivo | procesando | completado | error`,
  decisión del PE) con `useState`; `Resultado.tsx` pinta respuesta, estado y fuentes.
- 30 s: el backend tiene p95 de 3 s con Gemini y corta a Gemini a los 5 s (MDO-0001 D9); 30 s solo
  cubre un servicio colgado.
- Rechazadas: librería de estado o de peticiones (DP-9: un solo flujo); validar con un esquema externo
  (otra dependencia para tres campos).

<a id="d4"></a>
### D4 — Texto plano, sin Markdown (enmendado por C-8: Markdown con formato, sin HTML ni enlaces)

- Original: la respuesta y los fragmentos se pintaban como nodos de texto de React con `white-space: pre-wrap`.
- Enmienda ([C-8](#c-8)): pasan por `src/web/src/TextoMarkdown.tsx` (`react-markdown` con `remark-gfm` y
  `remark-breaks`, sin `rehype-raw`, con lista cerrada de elementos y `unwrapDisallowed`): títulos, tablas y
  listas con formato; un enlace queda como su texto, una imagen no se pinta y el HTML crudo se ve literal.
- En los dos casos `dangerouslySetInnerHTML` está prohibido; lo cubren S-2.4 y la revisión (la regla
  `react/no-danger` necesitaría otro plugin de ESLint).
- Rechazado en la enmienda: `rehype-raw` o un sanitizador de HTML (abre la vía de HTML que AC-1/C3 cierra).

<a id="d5"></a>
### D5 — Pruebas: backend simulado, y tres e2e al final

- Vitest + Testing Library + jsdom con `fetch` reemplazado por `vi.stubGlobal` y respuestas armadas
  según el contrato (decisión del PE). Rechazado MSW: otra dependencia para un solo endpoint.
- Playwright (decisión del PE, 2026-10-23) contra el backend real de MDO-0001: consulta exitosa con
  fuentes y pregunta sin información. Corren al final y necesitan MDO-0001 en `main`.
- Enmienda ([C-9](#c-9)): el caso "pregunta vacía con error visible" se reemplaza por dos, porque con D8
  la interfaz ya no envía una pregunta inválida:
  1. **Caja vacía:** el botón está deshabilitado y no sale ninguna petición a `/api/consultar` (S-1.3).
  2. **Error visible:** una pregunta válida con la respuesta forzada a 422 con `page.route` (problem+json
     con `detail` y `requestId`); se ven el mensaje y el código de referencia (S-3.1 en pantalla).
- El 422 real del backend queda cubierto por MDO-0001 (AC-7, pruebas de la API) y por `tests/web/api.test.ts` (S-3.1).

<a id="d6"></a>
### D6 — Gates del proyecto `web`

Aprobados por el PE el 2026-10-23 ([C-5](#c-5)); T1 los escribe en `.mandao/config.yml`:

| Gate | Comando (desde `src/web`) |
|---|---|
| format | `npm run format:check` (Prettier) |
| lint | `npm run lint` (ESLint + typescript-eslint + react-hooks; `complexity` ≤ 10, `max-lines-per-function` 50, `max-lines` 300 de `standards.md`) |
| typecheck | `npm run typecheck` (`tsc --noEmit`, `strict`) |
| test | `npm test` (`vitest run`) |
| build | `npm run build` (`tsc --noEmit && vite build`) |
| audit | `npm audit --omit=dev --audit-level=high` (sexto gate, pedido por el PE al aprobar) |

Las e2e (`npm run e2e`) no son gate: necesitan el backend real y corren en verify.

Si `npm audit` encuentra algo alto o crítico, el criterio es el de MDO-0001: el riesgo se acepta solo
si la vulnerabilidad no es alcanzable desde la interfaz, con su motivo escrito y aprobación del PE;
si no, se actualiza o se cambia la dependencia.

<a id="d7"></a>
### D7 — Dependencias, versiones y licencias

Versiones de npm del 2026-10-23, fijadas en `package-lock.json`:

- Ejecución: `react` y `react-dom` 19.3.1.
- Desarrollo: `vite` 8.3.5, `@vitejs/plugin-react` 6.1.2, `typescript` 6.0.3, `vitest` 5.0.5,
  `jsdom` 30.1.3, `@testing-library/react` 16.3.3, `@testing-library/user-event` 14.6.8,
  `@testing-library/jest-dom` 7.0.1, `@types/react` y `@types/react-dom` 19.3.0, `eslint` 10.13.0,
  `@eslint/js` 10.0.1, `typescript-eslint` 8.72.0, `eslint-plugin-react-hooks` 7.1.1, `globals`
  17.13.0, `prettier` 3.9.10, `@playwright/test` 1.64.1.
- TypeScript 6.0.3 y no 7.0.2: `typescript-eslint` 8.72.0 exige `typescript <6.1.0` ([P2](#p2)).
- Licencias directas: MIT y Apache-2.0. Excepción del PE (2026-10-23) para dependencias transitivas sin
  modificar: MPL-2.0 (p. ej. `lightningcss`, de Vite 8), PSF-2.0, ISC, BlueOak-1.0.0 y CC-BY-4.0. T1
  adjunta el informe real de licencias y `npm audit`.

<a id="d8"></a>
### D8 — Validar el largo de la pregunta en la interfaz, igual que el backend

- `src/web/src/pregunta.ts` exporta `MAXIMO_PREGUNTA = 1000`, `largoPregunta(texto)` =
  `[...texto.normalize("NFC").trim()].length` (puntos de código, como `len()` en Python) y
  `preguntaValida(texto)` = largo entre 1 y 1.000. Es la misma regla que `ConsultaEntrada` de MDO-0001
  (`unicodedata.normalize("NFC", valor).strip()` y `len(texto) > 1000`; [P4](#p4)).
- `Compositor` deshabilita el botón cuando `procesando` o la pregunta no es válida, y muestra el contador
  "N/1.000" (miles con punto) asociado al campo con `aria-describedby`; al pasarse lo marca como excedido.
  El manejador de `App` también retorna sin enviar si la pregunta no es válida: con el botón deshabilitado
  el navegador ya no envía con Enter, y el manejador lo garantiza igual (como con `procesando`, S-1.2).
- Se envía el texto tal como se escribió; el backend normaliza y valida, y sigue siendo la autoridad
  (S-3.1 con un 422 forzado y `api.test.ts`).
- Rechazadas: `maxLength` del `<input>` (cuenta unidades UTF-16, corta en silencio y no deja ver el
  exceso); el atributo `required` (acepta solo espacios y muestra el globo del navegador, fuera del
  diseño); contar con `texto.length` (un emoji cuenta 2 y la interfaz bloquearía preguntas que el
  backend acepta).

## Principle check

| ID | Applies? | Application or reason not applicable |
|---|---|---|
| DP-1 | yes | El texto del servicio no se interpreta como HTML ni crea enlaces (D4, S-2.4); la pregunta no se guarda en el navegador; la interfaz bloquea la pregunta inválida (D8) y la validación de la entrada sigue en el backend. |
| DP-2 | yes | La interfaz muestra solo lo que devuelve la API, con sus fuentes y estado, sin reescribirlo (FR-2). |
| DP-3 | yes | Cada escenario empieza con una prueba roja en Vitest; las e2e de D5 cubren AC-1 (crítico), la caja vacía sin petición y el error visible con un 422 forzado. |
| DP-4 | no | La interfaz no llama a ningún modelo. |
| DP-5 | yes | Cliente de la API (D3), pantalla y resultado separados; la pantalla no conoce HTTP. |
| DP-6 | yes | Sin servicios pagos; sin doble envío (S-1.2) ni preguntas inválidas (S-1.3, S-1.4) no salen consultas inútiles al backend. |
| DP-7 | yes | El `requestId` se muestra como código de referencia (FR-3) para cruzarlo con el log del backend; el registro es del backend. |
| DP-8 | no | La interfaz no escribe datos (`writes_data: no`). |
| DP-9 | yes | Sin librerías de UI, estado, peticiones ni mocks HTTP (D3, D5); Markdown con `react-markdown` por decisión del PE (D4, C-8); la validación de D8 es una función propia, sin librería. |

## Justified exceptions

| Principle | Why the exception is needed | Why a simpler alternative was rejected |
|---|---|---|
| `standards.md#dependencies` (solo MIT, Apache-2.0, BSD) | Vite 8 depende de `lightningcss` (MPL-2.0) y la cadena de desarrollo trae ISC, BlueOak-1.0.0 y CC-BY-4.0 | El stack aprobado es React + Vite (PE); otra herramienta de build trae licencias parecidas. Aprobada por el PE el 2026-10-23, solo para transitivas sin modificar |

## Data writes (ACID)

No aplica: la interfaz no escribe datos; el registro de la consulta es de MDO-0001.

## Changes by project and module

| Project | Module | Change | Exemplar file |
|---|---|---|---|
| web | `src/web` (config) | `package.json` con scripts de D6, `vite.config.ts` con proxy (D2) y Vitest, `tsconfig.json` `strict`, `eslint.config.js`, `.prettierrc`, `index.html`, `playwright.config.ts` | ninguno (primer proyecto Node) |
| web | `src/web/src/api.ts` | Cliente de la API y tipos del contrato (D3) | ninguno (nuevo; será el exemplar de cliente) |
| web | `src/web/src/App.tsx`, `Resultado.tsx`, `main.tsx` | Formulario, estado de procesamiento, resultado y error (FR-1, FR-2, FR-4) | ninguno (nuevo) |
| web | `tests/web/` | Pruebas Vitest por escenario y `tests/web/e2e/` con Playwright | ninguno (nuevo) |
| web | `src/web/src/pregunta.ts` (nuevo), `Compositor.tsx`, `App.tsx`, `estilos.css` | Validación del largo, botón deshabilitado y contador (D8, S-1.3, S-1.4) | `src/web/src/api.ts` |
| web | `tests/web/pregunta.test.ts` (nuevo), `tests/web/App.test.tsx`, `tests/web/e2e/consultar.spec.ts` | S-1.3 y S-1.4 en unidad y pantalla; S-3.1 en pantalla con una pregunta válida; las dos e2e de C-9 | `tests/web/App.test.tsx` |
| — | `.gitignore` | `node_modules/`, `src/web/dist/`, resultados de Playwright | `.gitignore` |

## Risks and impacts

| Change | Risk tags | Risk and mitigation |
|---|---|---|
| Resultado | `ui`, `security` | Texto de documentos interpretado como HTML: React lo escapa, D4 y la prueba S-2.4. |
| Cliente de la API | `input`, `public-api` | El contrato cambia en MDO-0001 y la interfaz no se entera: validación del 200 (S-3.4) y e2e contra el backend real. |
| Dependencias | `security` | Licencias transitivas fuera de la lista y vulnerabilidades: informe de licencias y `npm audit` en T1. |
| Validación en la interfaz | `input`, `ui` | La interfaz y el backend cuentan distinto y se bloquea una pregunta válida, o se deja pasar una inválida: misma fórmula (P4, comprobada con ambos), casos de borde en S-1.4 y el backend sigue validando. Solo difieren caracteres de control que `str.strip()` y `trim()` tratan distinto; ahí manda el 422 del backend. |

- **R-1:** las e2e dependen de que MDO-0001 esté en `main`; si se retrasa, T4 y T6 esperan y la spec no llega a `verified`.
- **R-2:** el proxy (D2) solo existe en `vite dev` y `vite preview`; servir `dist/` en otro lado necesita el mismo origen o CORS (fuera de alcance).

## Constitution Impact

Propuestas; solo `/mandao-close` las aplica, con aprobación.

- `standards.md#dependencies`: aceptar MPL-2.0, PSF-2.0, ISC, BlueOak-1.0.0 y CC-BY-4.0 para dependencias transitivas sin modificar.
- `standards.md#conventions`: el linter del frontend es ESLint con typescript-eslint (cierra el OPEN); exemplar de cliente `src/web/src/api.ts`.
- `architecture.md#stack`: versiones del frontend (D7) y el proxy de Vite (D2); módulo `src/web` como proyecto `web` (profile `app`).
- `critical-flows.md`: suite e2e `tests/web/e2e/` para "Consulta respondida con fuentes y registrada", desde la interfaz.
- `ux.md#design-tokens`: la paleta de Banco W de `src/web/src/estilos.css` (turquesa `#00b1bb`, naranja `#ff6900`, morado `#5f259f`, negro `#1b1b1b`, fondo `#faf9f6`), con modo oscuro y contraste AA (C-6).
- `ux.md`: marca Bot-W y dirección visual del mock `mockups/` (orbe animado, fondo degradado de Banco W, modo nocturno), con `prefers-reduced-motion` (C-7).

## Product Impact

- `product.md`, Capability map: "Frontend para consultar y ver respuesta, fuentes, errores y estado" pasa a `implemented` con evidencia en `src/web`.
- La propuesta del intake marca I-8 como abierta al mergear (PE), no en esta rama.

## Module Docs Impact

- `src/web/AGENTS.md`: cómo correr (`npm run dev` con el backend en el puerto 8000), los gates y las e2e.
- `src/web/AGENTS.md` (C-9): la pregunta vacía ya no llega al backend; `pregunta.ts` (D8), el contador y las dos e2e nuevas.
- `AGENTS.md` (raíz), Module index: `src/web` existe y es el proyecto `web`.
- MDO-0001 `story.md` y `design.md#contract`: MDO-0002 es la interfaz y MDO-0003 la seguridad (se corrige en esa spec).

## Consistency Check

| ID | Type | Finding | Severity | Owner | Status |
|---|---|---|---|---|---|
| CC-1 | CONTRACT | MDO-0001 `story.md` y `design.md#contract` llaman MDO-0003 a la interfaz y MDO-0002 a la seguridad; esta spec es MDO-0002 interfaz (PE). | normal | PO | resolved 2026-10-23: decisión del PE; se corrige en MDO-0001 |
| CC-2 | RULE | `standards.md#dependencies` solo permite MIT, Apache-2.0 y BSD; Vite 8 trae `lightningcss` (MPL-2.0) y otras transitivas. | normal | PO | resolved 2026-10-23: excepción del PE (D7, Justified exceptions) |
| CC-3 | DRIFT | FR-4 dice "ni el error ni el fin de la consulta borran el campo"; desde el rediseño de chat (C-6, C-7) `src/web/src/App.tsx` vacía la caja al enviar y la devuelve solo si hay error, y tras una respuesta queda vacía. S-4.1 (tras error) sí se cumple. | normal | PO | resolved 2026-10-23: el PE enmienda FR-4 al comportamiento actual (C-9) |

## Open items

- ASSUMPTION(source: MDO-0001 requirements.md S-7.x "un `detail` legible"): el `detail` del 422 llega en español y se puede mostrar tal cual; si no, se usa el mensaje genérico de 422. Confirma: dev de MDO-0001. — resolved 2026-10-23: MDO-0001 C-11 fija los `detail` del 422 en textos exactos en español ("La pregunta no puede estar vacía."); la e2e S-3.1 y `api.test.ts` los muestran tal cual.
- ASSUMPTION(source: performance.md p95 ≤ 3 s; MDO-0001 D9): 30 s de tiempo límite en la interfaz. Confirma: tech lead. — resolved 2026-10-23: el PE (tech lead) confirmó 30 s al cierre; implementado en `src/web/src/api.ts` y probado en S-3.3.

## Clarifications

### C-1 — ¿Excepción de licencias para MDO-0002? (2026-10-23)
- **Answer:** la de MDO-0001 ampliada: MPL-2.0, PSF-2.0, ISC, BlueOak-1.0.0 y CC-BY-4.0, solo transitivas sin modificar; T1 adjunta el informe real.
- **Answered by:** PE.
- **Effect:** D7, Justified exceptions, CC-2.

### C-2 — ¿Mock visual? (2026-10-23)
- **Answer:** no.
- **Answered by:** PE.
- **Effect:** `story.md#ux-references`.

### C-3 — ¿Herramienta e2e? (2026-10-23)
- **Answer:** Playwright, solo tres escenarios: consulta exitosa con fuentes, pregunta vacía con error visible y pregunta sin información; al final, con el backend real de MDO-0001.
- **Answered by:** PE.
- **Effect:** D5, T5.

### C-4 — ¿Mostrar el `requestId`? (2026-10-23)
- **Answer:** sí, como "Código de referencia: …".
- **Answered by:** PE.
- **Effect:** FR-3.

### C-5 — ¿Aprobación de la spec y de los gates de `web`? (2026-10-23)
- **Answer:** se aprueban story, spec y tasks con los cinco gates de D6, más un sexto: `audit: npm audit --omit=dev --audit-level=high`; un hallazgo se acepta solo si no es alcanzable, con su motivo (criterio de MDO-0001).
- **Answered by:** PE.
- **Effect:** D6, T1.

### C-6 — ¿Ajuste visual con los colores de Banco W? (2026-10-23)
- **Answer:** sí, solo visual: la paleta de Banco W (turquesa principal, naranja de acento, morado en los títulos de fuente), sin logos, con CSS propio y sin dependencias nuevas. Histórico y sugerencias de preguntas siguen fuera de alcance.
- **Answered by:** PE.
- **Effect:** `src/web/src/estilos.css`; amplía `story.md#out-of-scope` solo en lo visual; Constitution Impact (`ux.md#design-tokens`).

### C-7 — ¿Rediseño Bot-W según el mock? (2026-10-23)
- **Answer:** sí. La interfaz se llama Bot-W y sigue `mockups/` (exportado de Claude Design): orbe animado al centro sobre la caja, fondo con degradado animado de los colores de Banco W, modo nocturno para `prefers-color-scheme: dark`, sin panel lateral. Se incluyen tres preguntas sugeridas que solo llenan la caja (no envían). El historial sigue fuera de alcance.
- **Answered by:** PE.
- **Effect:** `src/web/src/` (estilos y componentes de la pantalla) e `index.html`; amplía C-6 (degradados y sugerencias); Constitution Impact (`ux.md`). Mock registrado como `accepted`, `source: design`.

### C-8 — ¿Respuesta con formato Markdown? (2026-10-23)
- **Answer:** sí. La respuesta y los fragmentos del servicio traen Markdown (títulos, tablas, listas) y se pintan con formato. Se mantiene AC-1/C3: nunca se interpreta HTML ni se crean enlaces o imágenes.
- **Answered by:** PE.
- **Effect:** D4 (enmendado): `react-markdown` 10.1.0 con `remark-gfm` 4.0.1 y `remark-breaks` 4.0.0 (MIT; transitiva ISC `@ungap/structured-clone`, dentro de C-1), sin `rehype-raw`, con lista cerrada de elementos (`allowedElements` y `unwrapDisallowed`): un enlace queda como su texto y una imagen no se pinta; el HTML crudo se ve literal. `src/web/src/TextoMarkdown.tsx` y `markdown.css`; pruebas en `tests/web/Resultado.test.tsx`.

### C-9 — ¿Bloquear en la interfaz la pregunta vacía o de más de 1.000 caracteres? (2026-10-23)
- **Answer:** sí. El botón queda desactivado y Enter no envía con la pregunta vacía o solo espacios, y con más de 1.000 caracteres; un contador "N/1.000" cuenta como el backend (NFC, `strip()`, puntos de código). La validación del backend se mantiene. La e2e "pregunta vacía con error visible" de C-3 se reemplaza por "caja vacía sin petición" y "error visible con un 422 (o 500) forzado con `page.route`"; el 422 real queda en MDO-0001 (AC-7) y en `api.test.ts`.
- **Answered by:** PE.
- **Effect:** AC-1/C4 en `story.md`; FR-1 (S-1.3, S-1.4); D5 y D8; T5 y T6; `src/web/AGENTS.md`; `quickstart.md`. Además, el PE resuelve CC-3: FR-4 se enmienda al comportamiento del chat (la caja se vacía al enviar y la pregunta vuelve si hay error; S-4.1 no cambia).

## Premise Ledger

<a id="p1"></a>
### P1 — El contrato aprobado de MDO-0001 es el que consume esta spec (High)
`design.md#contract` de MDO-0001 define el 200 `{respuesta, fuentes[{documento, seccion, fragmento}], estado}`
y los errores `application/problem+json` con `detail` y `requestId`. Si es falso, cambian D3, FR-3 y las
pruebas con backend simulado. El código de la ruta aún no existe en esa rama: las e2e de T5 lo confirman.

<a id="p2"></a>
### P2 — `typescript-eslint` 8.72.0 no admite TypeScript 7 (High)
Su `peerDependencies` exige `typescript >=4.8.4 <6.1.0`. Si es falso, se usa TypeScript 7.0.2 (D7).

<a id="p3"></a>
### P3 — El Node local cumple los motores de Vite, Vitest y jsdom (High)
Node 22.23.2 cumple `^22.12.0` (Vite, Vitest) y `^22.22.2` (jsdom). Si es falso, hay que fijar otra versión
de Node o bajar versiones (D7).

<a id="p4"></a>
### P4 — La interfaz cuenta el largo de la pregunta igual que el backend (High)
`ConsultaEntrada` de MDO-0001 acepta `1 ≤ len(unicodedata.normalize("NFC", texto).strip()) ≤ 1000` y
`[...texto.normalize("NFC").trim()].length` da lo mismo en el navegador para vacía, solo espacios, NBSP,
"é" descompuesta, emojis, 1.000 con espacios a los lados y 1.001. Si es falso, D8 bloquearía preguntas
válidas o dejaría pasar inválidas, y habría que cambiar la fórmula.

## Evidence

Corridas registradas con `mandao run premise` el 2026-10-23 (`_log/premises.md`).

<details><summary>P1 — probe p1_contrato.sh (git show de design.md en la rama de MDO-0001)</summary>

```
- 200: `{"respuesta": string, "fuentes": [{"documento": string, "seccion": string, "fragmento": string}], "estado": "Exitosa" | "Sin información suficiente" | "Bloqueada por seguridad"}`.
- 413 / 415 / 422 / 500: `application/problem+json` con `type`, `title`, `status`, `detail`, `requestId`.
- Todas las respuestas llevan `X-Request-Id`.
```
</details>

<details><summary>P2 — probe p2_peer.sh</summary>

```
{ "eslint": "^8.57.0 || ^9.0.0 || ^10.0.0", "typescript": ">=4.8.4 <6.1.0" }
```
</details>

<details><summary>P3 — probe p3_engines.sh</summary>

```
v22.23.2
^20.19.0 || >=22.12.0          (vite 8.3.5)
^22.12.0 || ^24.0.0 || >=26.0.0 (vitest 5.0.5)
^22.22.2 || ^24.15.0 || >=26.0.0 (jsdom 30.1.3)
OK: cumple ^22.22.2
```
</details>
