---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
environments: []
published: []
applied:
  - constitucion/architecture.md
  - constitucion/critical-flows.md
  - constitucion/standards.md
  - constitucion/glossary.md
  - constitucion/product.md
  - constitucion/business-rules.md
  - constitucion/constitucion.md
  - constitucion/model-registry.md
  - constitucion/CHANGELOG.md
closed_at: 2026-10-23T20:49:18.799Z
---

# Close — MDO-0001-consultar-la-base-documental-con-fuentes

`POST /api/consultar` responde con la base documental de `Data/` y sus fuentes, o con el mensaje fijo de
falta de información, y registra cada consulta. Los 16 criterios se cumplen. Funciona con Gemini o, sin
clave, en modo extractivo, y corre con un solo worker (D13).

## Outcome

- AC-1: met (T1, T3 committed; verify PASS)
- AC-2: met (T2 committed; verify PASS)
- AC-3: met (T4, T6, T9, T10, T15, T16 committed; verify PASS)
- AC-4: met (T7, T10, T14 committed; verify PASS)
- AC-5: met (T6, T7, T10, T14 committed; verify PASS)
- AC-6: met (T5, T10 committed; verify PASS)
- AC-7: met (T9, T17 committed; verify PASS)
- AC-8: met (T4 committed; verify PASS)
- AC-9: met (T9, T17 committed; verify PASS)
- AC-10: met (T9 committed; verify PASS)
- AC-11: met (T4, T5, T10, T16 committed; verify PASS)
- AC-12: met (T5 committed; verify PASS)
- AC-13: met (T5 committed; verify PASS)
- AC-14: met (T8, T9, T10 committed; verify PASS)
- AC-15: met (T12 committed; verify PASS)
- AC-16: met (T11, T13, T15 committed; verify PASS)

## For the PO

El asesor ya puede hacer una pregunta y recibir una respuesta tomada solo de los documentos oficiales.
Cada respuesta indica de qué documento, sección y texto sale. Si la base no tiene la información, el
asistente lo dice con el mensaje fijo y no inventa nada. Toda consulta queda registrada con su fecha y
hora, la respuesta, las fuentes y el estado.

| Criterio | Estado | Qué obtiene el asesor ahora |
|---|---|---|
| AC-1 | cumplido | Los documentos oficiales se pueden consultar. La información restringida nunca entra. |
| AC-2 | cumplido | Un contenido repetido cuenta una sola vez, también en las fuentes. |
| AC-3 | cumplido | Una pregunta con respaldo recibe respuesta y sus fuentes. |
| AC-4 | cumplido | La respuesta usa solo lo que encontró, sin mezclar productos. |
| AC-5 | cumplido | Si solo una parte tiene respaldo, se responde esa parte y se dice cuál falta. |
| AC-6 | cumplido | Cada fuente muestra el documento, la sección y el texto usado. |
| AC-7 | cumplido | Una pregunta vacía o mal enviada recibe un mensaje fijo y claro. |
| AC-8 | cumplido | Tildes, eñes y signos no afectan la búsqueda. |
| AC-9 | cumplido | Una pregunta de más de 1.000 caracteres se rechaza con un mensaje claro. |
| AC-10 | cumplido | Un envío demasiado grande o en otro formato se rechaza con un mensaje claro. |
| AC-11 | cumplido | Sin respaldo, el mensaje es "No tengo información suficiente para responder." |
| AC-12 | cumplido | Con la base vacía, el asistente responde lo mismo, sin fallar. |
| AC-13 | cumplido | Una pregunta fuera de tema recibe el mismo mensaje. |
| AC-14 | cumplido | Cada consulta queda registrada completa. |
| AC-15 | cumplido | Un error inesperado responde sin mostrar detalles internos. |
| AC-16 | cumplido | Si el modelo de IA falla, tarda o no está configurado, el asesor igual recibe el texto encontrado y su fuente. |

### Pendiente

- Bloquear las preguntas sobre información restringida, los intentos de manipular al asistente y los
  datos de otros clientes. Hoy esas preguntas reciben el mensaje de falta de información. Viene en la
  historia de seguridad.
- La pantalla para consultar. Hoy solo se prueba por la API. Viene en la historia de la interfaz.
- El README y el cuestionario de la prueba.

### Límites conocidos

- Corre en un solo proceso, que es suficiente para la prueba. Para más carga habría que pasar a un
  servidor de búsqueda vectorial; el código ya está preparado.
- Sin clave de Gemini, la respuesta muestra el texto encontrado tal cual. Puede incluir un fragmento
  relacionado de más (decisión del PE, C-10).

## For developers

Backend completo en `src/server/`, con capas hexagonales: `http` → `aplicacion` → puertos de `dominio`,
y `http` como raíz de composición de los cuatro adaptadores de `infraestructura`. 17 tareas: T1–T12 del
plan y T13–T17 abiertas por el Consistency Check del verify. El detalle por archivo está en
[src/server/AGENTS.md](../../src/server/AGENTS.md).

### Qué se construyó

| Módulo | Qué hace | Tareas |
|---|---|---|
| `infraestructura/documentos` | Carga `Data/` por sección `##`, excluye confidenciales (lista + marcador `CONFIDENCIAL`) y deduplica por sha256 normalizado | T1, T2 |
| `infraestructura/busqueda` | FTS5 con stemming español + Qdrant local, RRF, umbrales 0,60 / 0,525 | T3, T4, T10, T16 |
| `dominio`, `aplicacion` | `Estado`, `Fuente`, `Resultado`, puertos y el caso de uso `consultar` | T5 |
| `infraestructura/redactor` | Gemini (`gemini-3.5-flash-lite`, JSON + guardrail de ids y cifras) y respaldo extractivo | T6, T7, T11, T13, T14 |
| `infraestructura/persistencia` | Registro de cada consulta en SQLite, una transacción | T8 |
| `http` | `POST /api/consultar`, middleware 413/415/500, RFC 9457, semáforo de Gemini | T9, T12, T15, T17 |

### Decisiones y pivotes

- **D13:** un solo worker de uvicorn y un `QdrantClient` por app, porque Qdrant local bloquea su carpeta.
  Ahora está en `architecture.md`.
- **D4 / P5:** los umbrales 0,60 / 0,40 se refutaron en T10. Se recalibraron a 0,60 / 0,525 con el texto
  indexado `documento > sección\ntexto` y `consultas@v3` (C-9, C-10).
- **D9 (CC-1, T13):** el API rechaza plazos de servidor menores a 10 s. Se envía `X-Server-Timeout: 10`
  con un corte local de 5 s.
- **CC-2 (T15):** el candado global serializaba las llamadas al modelo. Lo reemplazó un
  `BoundedSemaphore` (`GEMINI_MAX_CONCURRENCIA`, 5). p95 mediana de 1,3 s con 5 consultas concurrentes.
- **CC-3 (T14):** cada fragmento llega a Gemini con su `documento > sección`, para que no mezcle productos.
- **CC-5 / C-11 (T17):** el `detail` del 422 es un texto fijo, sin `loc`/`msg` de Pydantic ni la entrada.

### Cambios de contrato

Nuevo: `POST /api/consultar` `{ pregunta }` → 200 `{ respuesta, fuentes[{documento, seccion, fragmento}],
estado }`. Errores `application/problem+json` con `requestId`: 422 (tres textos fijos, C-11), 413
(> 16 KB), 415 (no JSON) y 500 (sin detalles). Cada respuesta lleva `X-Request-Id`.

### Diagrama y drift

Junto al [propuesto](diagrams/proposed.html) está el [implementado](diagrams/implemented.html), con su
fuente en `diagrams/implemented.graph.json` y `diagrams/implemented.sequence.json`. El flujo de ejecución
coincide. El drift está en las dependencias estáticas:

- **Aristas faltantes** `aplicacion → busqueda`, `aplicacion → redactor` y `aplicacion → persistencia`:
  `aplicacion` solo importa `dominio` (DP-5) y llama a los adaptadores por sus puertos. En ejecución la
  llamada existe; en el código no hay import.
- **Aristas agregadas** `http → dominio` y `http → {busqueda, documentos, persistencia, redactor}`:
  `http/app.py` y `http/rutas.py` arman los adaptadores (raíz de composición). Además
  `{busqueda, documentos, persistencia, redactor} → dominio`, porque implementan sus puertos y usan sus
  tipos.
- **Nodos agregados** `src`, `src/server` y `src/server/infraestructura`: son carpetas contenedoras, sin
  comportamiento propio. `src/server/config.py` (rutas y umbrales) lo importan `http` y `busqueda`.
- **Contrato confirmado:** `POST /api/consultar` en `src/server/http/rutas.py:37`.

### Cómo probar

- `uv sync`, luego `uv run pytest` (unitarias y e2e, sin red) y `uv run pytest -m eval` (evals con el
  modelo de embeddings real).
- Manual: [quickstart.md](quickstart.md). Para levantar el servidor, ver "Levantar el backend" en el
  `AGENTS.md` raíz.

### Pendientes abiertos

- `mandao run tests` llama a `pytest` sin `uv run`. Los testers usaron `uv run pytest`.
- `QdrantClient.__del__` reporta un error de sqlite entre hilos al recolectar basura, en
  `test_la_app_abre_un_solo_qdrant_client_y_lo_cierra_al_apagar`. Es ruido del cierre, pero toca D13:
  revisarlo.
- Starlette avisa que su uso de `httpx` en `TestClient` está obsoleto.
- Índices con los nombres del PDF: [especificacion.md](especificacion.md), [plan.md](plan.md) y
  [tareas.md](tareas.md).

## Kaizen

17 tareas, rework 0,24 (4 FAIL del Reviewer), 1 escalamiento, 0 pivotes, 0 HALT, TDD parcial (16 de 17
tareas con prueba roja). 5 de las 17 tareas (T13–T17) salieron del verify. Costo USD 84,27 (equivalente,
suscripción): implement USD 63,08 (75 %), y dentro de él el leader USD 42,03. Tiempo activo: implement
55 min con 120 min de espera de agentes; verify 17 min con 47 min de espera del usuario.

### Comparación TDD

TDD: n = 0; sin TDD: n = 0 (mínimo 5 por grupo). Insufficient data: no se saca conclusión.

### Sessions

- **Sesiones faltantes:** ninguna.
- **Pausas:** 86. 83 de hasta 5 min, 3 de 5 a 60 min, 0 de más de 60 min; mediana 1,1 min.
- **Turnos por tarea:** T1 42, T2 11, T3 39, T4 51, T5 0, T6 0, T7 0, T8 23, T9 15, T10 68, T11 3, T13 3,
  T14 3. T12, T15, T16 y T17: not measured.
- **Verify:** 166 turnos. **Después de las tareas:** 571 turnos. **Close:** not recorded. **Recarga de
  contexto:** 20.385 tokens.
- **Corte de sesión** (`kaizen-compare`, `sessionCut`):

  | Constante | Valor | Medido | n | Resultado |
  |---|---|---|---|---|
  | turnos por tarea | 15 | 19,85 | 1 | insufficient data (minimum 3) |
  | turnos después de las tareas | 28 | not measured | 0 | insufficient data (minimum 3) |
  | tokens de recarga | 10.000 | 20.385 | 1 | insufficient data (minimum 3) |

  Hay 23 estimaciones de turnos restantes registradas (de 208 en T1 a 28 antes de cada verify). Sin los
  turnos que siguieron a cada una no se puede calcular el error absoluto medio: insufficient data
  (minimum 3). No se propone ningún cambio.

### Lecciones

1. **Una premisa sobre una API externa sin verificar se convierte en defecto tarde.** D9 suponía un plazo
   de 5 s. El API real exige al menos 10 s de plazo de servidor, y solo se vio en el verify con la clave
   real, porque las pruebas usan dobles (`standards.md`). Evidencia: CC-1, T13 (`9c8076a`).
   Estandarizado (K1): `standards.md`, Dependencies.
2. **El camino con el modelo real solo se ejercitó en el verify.** CC-2 (candado frente a NFR-1, T15) y
   CC-3 (fragmentos sin identidad, T14) también aparecieron recién con Gemini real, y sumaron 3 de las 5
   tareas posteriores al verify. Evidencia: CC-2, CC-3, `f9477b3`, `bccf698`. No se estandarizó: queda
   como recomendación correr una prueba de humo opcional con clave en la tarea que integra el modelo.
3. **Un criterio sin el texto exacto deja el mensaje a cargo del framework.** AC-7 pedía "un mensaje
   claro", y el `detail` del 422 salió con el formato de Pydantic. Evidencia: CC-5, C-11, T17
   (`fe65a6c`). Estandarizado (K2): `standards.md`, Errors.

## Delivery

- Closed: 2026-10-23T20:49:18.799Z
- Applied: `constitucion/architecture.md`, `constitucion/critical-flows.md`, `constitucion/standards.md`, `constitucion/glossary.md`, `constitucion/product.md`, `constitucion/business-rules.md`, `constitucion/constitucion.md`, `constitucion/model-registry.md`, `constitucion/CHANGELOG.md`
- [Verify report](verify-report.md)
- [Quickstart](quickstart.md)
