---
schema_version: 1
spec: MDO-0002-consultar-desde-la-interfaz
environments: []
published: []
applied:
  - constitucion/standards.md
  - constitucion/architecture.md
  - constitucion/critical-flows.md
  - constitucion/product.md
  - constitucion/security.md
  - constitucion/ux.md
  - constitucion/CHANGELOG.md
  - AGENTS.md
---

# Close — MDO-0002-consultar-desde-la-interfaz

W+IA, la pantalla local para consultar, quedó lista. El asesor escribe la pregunta, ve que se está
procesando y recibe la respuesta con sus fuentes y su estado, o un error claro. Los dos criterios se
cumplen. Corre con `npm run dev` en `src/web`, con el backend de MDO-0001 en el puerto 8000.

## Outcome

- AC-1: met (T2, T3, T4, T5, T6 committed; verify PASS)
- AC-2: met (T1, T3, T4, T6 committed; verify PASS)

## For the PO

El asesor ya tiene una pantalla para consultar al asistente. Mientras espera, la pantalla muestra que
la consulta se está procesando. Después ve la respuesta, el estado de la respuesta y, por cada fuente,
el documento, la sección y el texto usado. Si algo falla, recibe un mensaje claro en español y su
pregunta queda escrita para corregirla o reintentar.

| Criterio | Estado | Qué obtiene el asesor ahora |
|---|---|---|
| AC-1 | cumplido | Escribe la pregunta y ve el procesamiento, la respuesta, las fuentes y un estado siempre visible. No puede enviar dos consultas a la vez ni una pregunta vacía o de más de 1.000 caracteres, y un contador le muestra el largo. |
| AC-2 | cumplido | Si la consulta se rechaza, el servicio falla o no hay conexión, ve un mensaje claro sin detalles técnicos, con su código de referencia cuando existe, y conserva la pregunta. |

### Pendiente

- El estado "Bloqueada por seguridad" ya se muestra en pantalla, pero el servicio todavía no lo produce.
  Llega con la historia de seguridad (MDO-0003).
- El README y el cuestionario de la prueba.

### Límites conocidos

- Solo se ve la consulta en curso: no hay historial de consultas anteriores (fuera de alcance).
- La pantalla es local y sin inicio de sesión, como pide la prueba.

## For developers

Proyecto nuevo `web` (`src/web`, profile `app`): React 19 + Vite 8 + TypeScript `strict`, con las pruebas
en `tests/web`. Seis tareas, T1–T6. El detalle por archivo está en
[src/web/AGENTS.md](../../src/web/AGENTS.md).

### Qué se construyó

| Módulo | Qué hace | Tareas |
|---|---|---|
| `src/api.ts` | Cliente de `POST /api/consultar`. Nunca lanza, traduce 200/413/415/422/500, la red caída y el tiempo agotado (30 s) a un resultado, y de un 200 copia solo los campos del contrato | T1 |
| `src/Resultado.tsx`, `src/TextoMarkdown.tsx` | Respuesta, estado con rótulo propio y fuentes `documento > sección` + fragmento. Markdown con una lista cerrada de elementos, sin HTML crudo, enlaces ni imágenes | T2 |
| `src/App.tsx`, `src/Compositor.tsx`, `src/Cargando.tsx`, `src/Orbe.tsx` | Pantalla W+IA: `EstadoProcesamiento` en `useState`, bloqueo de doble envío, error con `role=alert` y código de referencia, y la pregunta conservada tras un error | T3 |
| `src/pregunta.ts` | Regla de largo igual a la del backend (NFC + `trim`, 1 a 1.000 puntos de código) y contador "N/1.000" | T5 |
| `tests/web/e2e/consultar.spec.ts` | Cuatro e2e con Playwright: consulta exitosa y sin información contra el backend real, caja vacía y 422 forzado | T4, T6 |

### Decisiones y pivotes

- **D2:** `/api` va por el proxy de Vite a `127.0.0.1:8000`, en el mismo origen y sin CORS. Así no se toca
  `src/server`. Ahora está en `architecture.md`.
- **D4 → C-8:** el texto plano pasó a Markdown con lista cerrada (`allowedElements` + `unwrapDisallowed`, sin
  `rehype-raw`). AC-1/C3 se sigue cumpliendo: el HTML sale literal y un enlace queda como texto.
- **C-9 (D8, T5, T6):** la pregunta vacía o demasiado larga se bloquea en la interfaz. La e2e de pregunta
  vacía se reemplazó por "caja vacía" y "422 forzado".
- **C-5 → C-7:** pase visual con la paleta de Banco W y después el rediseño según el mock. La marca
  Bot-W pasó a **W+IA** con un cambio rápido de texto (7492298, merge 509aa7f). La spec conserva el nombre
  anterior en C-7; `ux.md` ya dice W+IA.
- **T1 F1 (revisor):** `server.fs.allow` de Vite abría la raíz del repositorio, incluido
  `Data/Información restringida.md`. Se limitó a `src/web` y `tests/web`, con `Data/**` en `fs.deny`.
- **R-1:** las e2e de T4 se escribieron antes de que el backend estuviera en `main` y quedaron diferidas.
  Corrieron en la CI del PR #2, que se agregó en `ci.yml` (PR #3).

### Cambios de contrato

Ninguno. La interfaz consume `POST /api/consultar` tal como lo define MDO-0001. Muestra `detail` y
`requestId` de los errores `problem+json` y nunca el cuerpo crudo.

### Diagrama y drift

No aplica: es una spec lite, sin diagrama aprobado (`diagram-drift`: "lite specs have no diagram").

### Cómo probar

- En `src/web`: `npm ci`, luego `npm test` (67 unitarias) y los gates `format:check`, `lint`, `typecheck`
  y `build`.
- e2e: levantar el backend (ver "Levantar el backend" en el `AGENTS.md` raíz), `npx playwright install
  chromium` la primera vez y `npm run e2e`. En CI corre en el job `frontend`.
- Manual: [quickstart.md](quickstart.md).

### Pendientes abiertos

- No hay SAST para TypeScript. Es un hueco aceptado por el PE (`security-gaps`). Mejora: agregarlo en CI.
- En local, el guardián de recursos pide 4,5 GB libres para las e2e, así que en máquinas justas solo
  corren en CI.
- Los tokens de texto y fondo de la spec (`#1b1b1b`, `#faf9f6`) no coinciden con `estilos.css`
  (`#14161a`, `#f6f7fb`). `ux.md` toma los del código.

## Kaizen

6 tareas. Retrabajo de 0,67: 4 FAIL del revisor (T1, T2, T4, T6), sin escaladas ni pivotes. TDD: 4 de 4
tareas con pruebas tuvieron rojo antes del verde. Costo: US$38,28 equivalentes (specify 18,09, implement
17,34, verify 2,86). La comparación TDD/no-TDD y los cortes de sesión no tienen datos suficientes.

### Sessions

- Turnos por tarea: T1 12, T2 0, T3 0, T5 47 y T6 16. T4: not measured.
- Verify: 70 turnos. Después de las tareas: 177. Close: not recorded.
- Pausas: 29, con mediana de 0,5 min (24 de ≤ 5 min, 4 de 5 a 60 min y 1 de más de 60 min).
- Cortes de sesión: turnos por tarea 18,5 medidos frente a la constante 15 (n=2); turnos después de las
  tareas 622 frente a 28 (n=1); tokens de recarga 22.039,5 frente a 10.000 (n=2). En los tres casos:
  insufficient data (minimum 3). Las estimaciones de turnos restantes quedaron muy por debajo de lo real
  (en MDO-0001, 208 estimados frente a 928 reales en T1), y la muestra sigue sin llegar al mínimo.
- TDD frente a sin TDD: insufficient data (TDD n=1, sin TDD n=0; mínimo 5 por grupo).

### Lecciones

1. **La guía del módulo se olvida.** Tres de los cuatro FAIL fueron por `src/web/AGENTS.md` sin
   actualizar (T1 F3, T2 F2, T6 F1), incluso cuando la tarea lo listaba (T6). Regla nueva en
   `standards.md`: el `AGENTS.md` del módulo va en files y en Done when, y se revisa antes de entregar.
2. **Pruebas fuera del paquete sin plan.** Tener `tests/web` fuera de `src/web` obligó a tocar en T1 y T2
   alias, `paths` y el alcance de format y lint, en archivos no declarados (T1 F2, T2 F3 y F5). Regla nueva
   en `standards.md`: la primera tarea lo define.
3. **El servidor de desarrollo es superficie de ataque.** `fs.allow: ["../.."]` exponía el documento
   confidencial (T1 F1). Regla nueva en `security.md`: ningún servidor de desarrollo sirve la raíz y
   `Data/` va en su lista de denegación.

## Delivery

- Applied: `constitucion/standards.md`, `constitucion/architecture.md`, `constitucion/critical-flows.md`, `constitucion/product.md`, `constitucion/security.md`, `constitucion/ux.md`, `constitucion/CHANGELOG.md`, `AGENTS.md`
- [Verify report](verify-report.md)
- [Quickstart](quickstart.md)
