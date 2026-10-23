---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
depth: standard
projects: [asistente-asesores]
status: draft
writes_data: yes
---

# Design — Consultar la base documental con fuentes

Un backend FastAPI sobre Python 3.13 con arquitectura hexagonal: al arrancar indexa `Data/` (sin
confidenciales ni duplicados) en SQLite con FTS5 y en Qdrant local con vectores coseno; cada consulta
valida, recupera con
búsqueda híbrida y umbral, redacta con Gemini validando su salida o responde extractivo, y se registra en
la misma transacción que decide la respuesta.

## Decisions

<a id="d1"></a>
### D1 — Python 3.13 fijado en el proyecto

- `fastembed` depende de `onnxruntime`, que no publica wheels para Python 3.15 (el `python3` del sistema)
  ni para 3.10 en macOS arm64 ([research.md#R1](research.md)). Se fija 3.13 con `.python-version` y
  `requires-python = ">=3.11,<3.15"` en `pyproject.toml`.
- El README instala con `uv` (`uv sync`), que respeta `.python-version` ([C-4](requirements.md#c-4)). Con
  Qdrant local ([D4](#d4)) no hace falta un intérprete con extensiones de SQLite; basta FTS5 ([P2](#p2)).
- Rechazadas: 3.15 (no instala), 3.10 (sin wheel macOS arm64), 3.14 (válida pero sin probar en esta
  máquina).

<a id="d2"></a>
### D2 — Un fragmento por sección `##`

- Cada sección `##` con sus subsecciones `###` es un fragmento; su fuente es
  `documento > sección` (nombre del archivo sin `.md`, título `##`). Un documento sin `##` es un único
  fragmento titulado con su `#`. Las secciones de `Data/` son cortas y autocontenidas ([P4](#p4)), así que
  el fragmento citado es la sección entera, que es lo que pide AC-6.
- Rechazadas: ventanas de N caracteres (cortan tablas y pierden la sección para citar); fragmentos por
  `###` (separa "Condiciones" del nombre del crédito y la pregunta deja de encontrar su sección).

<a id="d3"></a>
### D3 — Exclusión de confidenciales en dos capas

- Una lista de excluidos en configuración (`Información restringida.md`) y, además, cualquier documento
  cuyas primeras líneas contengan la palabra `CONFIDENCIAL` (clasificación, `security.md`). El log de
  arranque registra el nombre del excluido, nunca su contenido. Así un documento confidencial nuevo no se
  indexa por olvido.
- Rechazadas: solo por nombre (frágil ante un archivo nuevo); mover el archivo a otra carpeta (cambia el
  árbol `Data/` que pide el PDF, p. 3).

<a id="d4"></a>
### D4 — Búsqueda híbrida con umbral de relevancia

- FTS5 (`unicode61 remove_diacritics 2`, BM25) en SQLite y Qdrant en modo local
  (`QdrantClient(path=…)`, `qdrant-client` 1.20.0, [C-3](requirements.md#c-3), `architecture.md`): una
  colección `fragmentos` de 384 dimensiones con distancia coseno, con embeddings locales de
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (0,22 GB, vía `fastembed`,
  [research.md#R1, R3, R5](research.md)). El id de cada punto es un UUID v5 del hash del fragmento y su
  payload trae `hash`; los resultados de Qdrant se unen a `fragmentos` por `hash`. Cada búsqueda trae hasta
  5 candidatos por vía, se combinan por Reciprocal Rank Fusion (k = 60) y se quedan los 3 primeros.
- **Umbral:** hay soporte si el mejor fragmento tiene similitud coseno ≥ `UMBRAL_ALTO` (0,60), o ≥
  `UMBRAL_BAJO` (0,40) y además coincide en FTS. Valores iniciales en configuración, calibrados en tareas
  contra EV-2 y EV-3 ([C-5](requirements.md#c-5), [P5](#p5)). Bajo el umbral: `Sin información
  suficiente`, sin llamar al modelo.
- Rechazadas: `sqlite-vec` (exige un Python con extensiones de SQLite cargables, que no todos los
  evaluadores tienen); coseno en memoria (no es una base vectorial); Chroma y LanceDB (sin paso directo de
  local a servidor con el mismo cliente), según `CHANGELOG.md` 2026-10-23; solo FTS (sin stemming en
  español, falla con sinónimos); solo vectores (falla con nombres
  exactos como "Agro Crece"); `paraphrase-multilingual-mpnet-base-v2` (1 GB de descarga para un corpus de
  ~20 fragmentos; queda como alternativa si EV-1 no se cumple); un umbral sobre el puntaje RRF (es por
  rango, no mide relevancia absoluta).

<a id="d5"></a>
### D5 — La pregunta es datos en la búsqueda

- Para FTS se normaliza la pregunta, se quitan las palabras vacías en español (lista corta en código), y
  cada palabra va entre comillas dobles con las comillas internas duplicadas, unidas con `OR`, siempre como
  parámetro (`MATCH ?`). Sin palabras útiles (solo signos o emojis), se omite la vía FTS. Cubre AC-8.
- Rechazada: escapar caracteres uno por uno (la sintaxis FTS5 tiene operadores y prefijos que se escapan
  mal).

<a id="d6"></a>
### D6 — Duplicados por hash de contenido normalizado

- sha256 del texto normalizado (minúsculas, espacios colapsados), por documento y por fragmento; gana el
  primero en orden alfabético de archivo. Las fuentes se deduplican por `documento > sección`.
- Rechazada: similitud aproximada (trata como duplicadas secciones parecidas que son productos distintos,
  p. ej. "Condiciones" de dos créditos).

<a id="d7"></a>
### D7 — Gemini redacta en JSON y el código valida la salida

- Gemini (`gemini-3.5-flash-lite`, `model-registry.md`) recibe en `system_instruction` el prompt versionado
  y en `contents` los fragmentos numerados y la pregunta, delimitados como datos. Responde con un esquema
  Pydantic: `respuesta`, `fragmentos_usados` (ids) y `partes_sin_soporte` (textos).
- **Guardrail de salida (código):** se descarta la salida y se pasa al extractivo si `fragmentos_usados`
  está vacío o cita ids no recuperados, o si una cifra de `respuesta` no aparece en los fragmentos citados
  (AC-4). Si el modelo declara que ninguna parte tiene soporte, el estado es `Sin información suficiente`.
- **Parcial (AC-5):** por cada parte en `partes_sin_soporte` el código agrega "No encontré información
  sobre <parte>." al final; la frase la arma el código, no el modelo.
- Rechazadas: texto libre con citas inline (no se puede validar en forma determinista); que el modelo
  elija las fuentes sin validación (puede citar lo que no recuperó).

<a id="d8"></a>
### D8 — Errores en RFC 9457 con middleware propio

- Un middleware ASGI asigna `requestId` (UUID v4, también en `X-Request-Id`), rechaza con 415 todo
  `Content-Type` distinto de `application/json` (con o sin `charset`) y con 413 un cuerpo de más de
  16.384 bytes, por `Content-Length` o contando los bytes recibidos. Handlers propios para
  `RequestValidationError` (422), `HTTPException` y `Exception` (500) responden
  `application/problem+json` con `type`, `title`, `status`, `detail` y `requestId`
  ([research.md#R4](research.md)).
- La validación de `pregunta` usa Pydantic: texto obligatorio, normalizado a NFC, `strip()` y luego 1–1.000
  puntos de código ([C-2](requirements.md#c-2)).
- Rechazadas: `RequestBodyLimitMiddleware` de Starlette (responde texto plano y no se confirmó su
  versión junto a FastAPI 0.161.1); `strict_content_type=False` (aceptaría cuerpos sin tipo).

<a id="d9"></a>
### D9 — Gemini con 5 s y sin reintentos

- `HttpOptions(timeout=5000)` sin `retry_options` (un solo intento, [research.md#R4](research.md)).
  Cualquier excepción o tiempo agotado → extractivo (AC-16). Sin `GEMINI_API_KEY` no se crea el cliente.
- Rechazado: reintentos (con un p95 de 3 s no hay margen; el extractivo es la respuesta de respaldo).

<a id="d10"></a>
### D10 — Registro en la misma operación que la respuesta

- El caso de uso arma el resultado y lo inserta en `consultas` en una transacción antes de devolverlo; si
  el insert falla, responde 500 y no hay respuesta sin registro (BR-6). Las peticiones que no pasan la
  validación nunca llegan al caso de uso, así que no se registran (AC-14/C1).
- Rechazada: registrar en segundo plano después de responder (podría perderse el registro sin que nadie
  lo sepa).

<a id="d11"></a>
### D11 — Índice reconstruido al arrancar; Qdrant como caché de embeddings

- En cada arranque: (1) se cargan y fragmentan los documentos; (2) en Qdrant se calculan y suben solo los
  embeddings de hashes que la colección no tiene (upsert idempotente por UUID del hash), lo que cumple
  NFR-2 sin una tabla de caché aparte; (3) se reconstruyen `fragmentos` y `fragmentos_fts` en una
  transacción SQLite; (4) solo si (3) hace commit se borran de Qdrant los puntos cuyo hash ya no existe.
  Si (2) o (3) fallan, el servidor no arranca; los puntos que sobren en Qdrant no se devuelven porque la
  búsqueda filtra por los hashes presentes en `fragmentos`.
- Si cambia el modelo de embeddings (nombre guardado en la configuración de la colección), se recrea la
  colección (`model-registry.md`).
- Rechazadas: actualización incremental por archivo (más estados posibles para ~20 fragmentos); una
  tabla `embeddings_cache` en SQLite (duplica lo que Qdrant ya persiste).

<a id="d13"></a>
### D13 — Un solo proceso y un cliente Qdrant por aplicación

- El modo local bloquea su carpeta: un segundo `QdrantClient` sobre el mismo `path` lanza
  `RuntimeError` ([P6](#p6)). La app abre un único cliente en el `lifespan` de FastAPI y lo cierra al
  apagar; uvicorn corre con un solo worker (README). Las pruebas usan una carpeta temporal por prueba, o
  `QdrantClient(":memory:")`.
- Rechazadas: varios workers (fallan al abrir la carpeta); un servidor Qdrant (rompe "ejecutable 100 %
  local sin servicios", `architecture.md`; queda como paso a producción).

<a id="d12"></a>
### D12 — Respuesta extractiva

- La respuesta empieza con "Esto es lo que encontré en la base documental:" y sigue con los fragmentos
  que superan el umbral (máximo 2), cada uno precedido por `Documento > Sección`, con estado `Exitosa`. No
  afirma cubrir toda la pregunta ni nombra partes faltantes ([C-1](requirements.md#c-1)).

## Principle check

| ID | Applies? | Application or reason not applicable |
|---|---|---|
| DP-1 | yes | Validación antes de procesar (D8); confidenciales fuera del índice en dos capas (D3); la pregunta y los fragmentos son datos en búsqueda y prompt (D5, D7). El bloqueo por seguridad es MDO-0002. |
| DP-2 | yes | Solo información recuperada, validada por el guardrail de salida (D7); fuentes siempre (FR-6); mensaje fijo sin soporte (FR-10). |
| DP-3 | yes | Cada escenario empieza con una prueba roja; dobles de `Redactor` y embeddings en las pruebas (`standards.md`). |
| DP-4 | yes | El modelo solo redacta con fragmentos recuperados; su salida se valida en código; umbral y estados son deterministas (D4, D7). |
| DP-5 | yes | Caso de uso sobre puertos `BuscadorDocumental`, `RepositorioConsultas`, `Redactor`; sin capas extra. |
| DP-6 | yes | Modo por defecto local y gratuito; sin modelo bajo el umbral; embeddings locales y en caché (D4, D9, D11). |
| DP-7 | yes | Registro de cada consulta (D10) y log JSON por petición con `requestId`, estado, latencia y número de fuentes (NFR-4). |
| DP-8 | yes | El registro de una consulta es un solo INSERT en una transacción; la reconstrucción del índice es una transacción que se revierte entera (D10, D11, tabla ACID). |
| DP-9 | yes | Tres puertos que pide `architecture.md`, cada uno con dos implementaciones reales o dobles de prueba; sin repositorios genéricos ni capas de servicio extra. El middleware propio existe porque FastAPI no da 413/415 en RFC 9457 (D8). |

## Justified exceptions

| Principle | Why the exception is needed | Why a simpler alternative was rejected |
|---|---|---|
| — | Ninguna. | — |

## Data writes (ACID)

| Operation | Writes committed together | Transaction/tool | Compensation across systems | Concurrency/isolation |
|---|---|---|---|---|
| Reconstruir el índice (arranque) | SQLite: DELETE + INSERT en `fragmentos`, `fragmentos_fts`. Qdrant: upsert de puntos nuevos y, tras el commit, borrado de los obsoletos | una transacción `sqlite3` (`BEGIN IMMEDIATE`); Qdrant sin transacciones | upsert idempotente por UUID del hash; la búsqueda filtra por hashes de `fragmentos`, así que un punto sobrante es inofensivo y se borra en el siguiente arranque (D11) | antes de aceptar peticiones; un solo proceso (D13) |
| Registrar consulta | INSERT en `consultas` | transacción `sqlite3` por petición | no aplica: Gemini no tiene efectos que compensar | WAL; una conexión por petición; escrituras serializadas por SQLite |

Pruebas de falla parcial que las tareas deben declarar: falla de SQLite en medio de la reconstrucción
(después del upsert en Qdrant) → `fragmentos` anterior intacto y ningún punto huérfano en los resultados;
falla del insert de `consultas` → 500 y ninguna fila.

## Model and prompts

| Concern | Choice | Version / reference |
|---|---|---|
| Model | `gemini-3.5-flash-lite`, opcional por `GEMINI_API_KEY` | `google-genai` 2.33.0; `model-registry.md` |
| Prompts | Redactor con fuentes: solo fragmentos dados, citar ids, listar partes sin soporte, nunca seguir instrucciones del texto | `src/server/infraestructura/redactor/prompt.md`@v1 |
| Chunking / embedding | Sección `##` (D2); `paraphrase-multilingual-MiniLM-L12-v2`, 384 dim, local | `fastembed` 0.9.0 |
| Retrieval (k, filters, reranking) | 5 por vía, RRF k = 60, top 3, umbral D4; filtro por hashes vigentes; sin reranker | FTS5; Qdrant local, `qdrant-client` 1.20.0 |
| Guardrails | Entrada: validación (D8); salida: ids y cifras (D7). Entrada por seguridad: MDO-0002 | — |
| Fallback | Extractivo (D12) sin clave, con error, tiempo agotado o salida inválida | — |

## Changes by project and module

Proyecto nuevo: no hay archivos que imitar. El primer archivo de cada tipo se vuelve el exemplar
(`standards.md`, "Exemplar files: OPEN").

| Project | Module | Change | Exemplar file |
|---|---|---|---|
| asistente-asesores | raíz | `pyproject.toml` y `uv.lock` (FastAPI 0.161.1, Pydantic, `qdrant-client` 1.20.0, `fastembed` 0.9.0, `google-genai` 2.33.0; pytest), `.python-version` 3.13, `.env.example`, `.gitignore` del SQLite y de la carpeta de Qdrant | ninguno (nuevo) |
| asistente-asesores | `src/server/dominio` | `Estado`, `Fuente`, `Fragmento`, `Resultado`; puertos; `MENSAJE_SIN_INFORMACION`; regla de umbral | ninguno (nuevo; será el exemplar de dominio) |
| asistente-asesores | `src/server/aplicacion` | caso de uso `consultar(pregunta)` | ninguno (nuevo) |
| asistente-asesores | `src/server/infraestructura/documentos` | cargador de `Data/`: exclusión, fragmentación, hash | ninguno (nuevo) |
| asistente-asesores | `src/server/infraestructura/busqueda` | esquema FTS5, colección Qdrant, reconstrucción del índice, consulta FTS segura, RRF | ninguno (nuevo) |
| asistente-asesores | `src/server/infraestructura/persistencia` | `RepositorioConsultas` SQLite | ninguno (nuevo) |
| asistente-asesores | `src/server/infraestructura/redactor` | `RedactorGemini`, `RedactorExtractivo`, validación de salida, `prompt.md` v1 | ninguno (nuevo) |
| asistente-asesores | `src/server/http` | app, middleware (requestId, 413, 415), handlers RFC 9457, ruta `POST /api/consultar`, log JSON | ninguno (nuevo) |
| asistente-asesores | `tests/` | unitarias por módulo, API con `TestClient`, dataset `tests/fixtures/consultas.json`@v1 y evals | ninguno (nuevo) |

## Diagram

<!-- mandao:diagram type=sequence tool=archify file=diagrams/proposed.html graph=diagrams/proposed.graph.json graphHash=sha256:9cbeeb8f7168942b source=sha256:a655e86858eef0f9 -->
Derived from this design; regenerated whenever it changes. Part of the design approval.

![sequence diagram](diagrams/proposed.html)

## Contract

`POST /api/consultar`, `Content-Type: application/json`, cuerpo ≤ 16 KB.

- Petición: `{"pregunta": string}` (1–1.000 caracteres tras `strip()`).
- 200: `{"respuesta": string, "fuentes": [{"documento": string, "seccion": string, "fragmento": string}], "estado": "Exitosa" | "Sin información suficiente" | "Bloqueada por seguridad"}`.
- 413 / 415 / 422 / 500: `application/problem+json` con `type`, `title`, `status`, `detail`, `requestId`.
- Todas las respuestas llevan `X-Request-Id`.

MDO-0003 (interfaz) consume este contrato; MDO-0002 solo agrega el estado `Bloqueada por seguridad`.

## Risks and risk tags

| Change | Risk tags | Risk and mitigation |
|---|---|---|
| Middleware y validación | `input`, `public-api` | Un 413/415 mal implementado deja pasar cuerpos grandes: pruebas con y sin `Content-Length`. |
| Redactor Gemini | `ai-prompt`, `security` | El modelo inventa o sigue instrucciones del texto: guardrail de salida D7, prompt versionado, extractivo como respaldo. |
| Registro de consultas | `pii` | La pregunta puede traer datos de clientes: se guarda solo en el SQLite local y nunca en logs (NFR-4). |
| Búsqueda y umbral | `perf` | Primer arranque descarga 0,22 GB; umbral mal calibrado da falsos "sin información": EV-2 y EV-3. |
| Índice | `security` | Un confidencial nuevo indexado por error: doble capa D3 y prueba que busca sus términos en el índice. |

- **R-5:** `google-genai` 2.33.0 salió el mismo día del diseño y `qdrant-client` 1.20.0 el día anterior; si alguno falla, se fija la versión previa (2.32.0, 1.19.1).
- **R-7:** el modo local de Qdrant está pensado para desarrollo y pruebas (README de qdrant-client); con ~20 fragmentos basta, y producción usaría un servidor Qdrant con el mismo cliente (`architecture.md`).
- Sin guardrail de entrada por seguridad hasta MDO-0002: una pregunta por credenciales queda `Sin información suficiente`, porque el documento no está indexado (D3).

## Constitution Impact

Propuestas; solo `/mandao-close` las aplica, con aprobación. Qdrant local, Python 3.13 con `uv` y el
modelo de embeddings ya están en `architecture.md` y `model-registry.md` (`/mandao-constitution`,
2026-10-23, [C-3](requirements.md#c-3)).

- `architecture.md`: un solo worker de uvicorn por el bloqueo de carpeta de Qdrant local (D13, P6).
- `model-registry.md`: prompt `prompt.md` v1 creado; dataset `tests/fixtures/consultas.json` v1 creado.
- `critical-flows.md`: suite E2E del flujo "Consulta respondida con fuentes y registrada" (la que creen
  las tareas).
- `standards.md`: nombrar los exemplar files creados.
- `glossary.md`: "Modo de respuesta" (`modo`: `modelo`, `extractivo`, `ninguno`).

## Product Impact

- `product.md`, Capability map: "Responder consultas con fuentes", "Indicar falta de información" y
  "Registrar consultas" pasan a `implemented` con su evidencia en código al cerrar.

## Module Docs Impact

- Crear `src/server/AGENTS.md` (capas, puertos, cómo correr las pruebas) y actualizar el índice de
  módulos de `AGENTS.md` raíz.

## Premise Ledger

<a id="p1"></a>
### P1 — No existe código en `src/` ni en `tests/` (High)

- **If false:** habría que leer el esquema y los módulos existentes; `data-model.md` dejaría de ser solo ADDED.
- **Evidence:** verified 2026-10-23, `_log/premises.md` P1; ver [Evidence](#evidence).

<a id="p2"></a>
### P2 — El `sqlite3` de Python 3.13 trae FTS5 y `remove_diacritics 2` pliega tildes (High)

- **If false:** FTS no plegaría tildes (AC-8, S-8.2) y la vía de palabras necesitaría normalizar el texto antes de indexar.
- **Evidence:** verified 2026-10-23 con pyenv 3.13.4, `_log/premises.md` P2; ver [Evidence](#evidence).

<a id="p3"></a>
### P3 — `fastembed` no instala sobre Python 3.15 (Low)

- **If false:** D1 podría usar el Python del sistema; no cambia el diseño.
- **Evidence:** UNVERIFIED — inferido de los wheels de `onnxruntime` 1.31.0 ([research.md#R1](research.md)); no se instala nada para probarlo.

<a id="p4"></a>
### P4 — Todos los documentos oficiales de `Data/` se organizan en secciones `##` de menos de 1 KB (High)

- **If false:** D2 necesitaría partir secciones largas y el límite de 128 tokens de MiniLM cortaría texto.
- **Evidence:** verified 2026-10-23, `_log/premises.md` P4 (sección mayor: 387 bytes); ver [Evidence](#evidence).

<a id="p5"></a>
### P5 — Los umbrales 0,60 / 0,40 separan preguntas con y sin soporte en `Data/` (Low)

- **If false:** se recalibran en la tarea de evals ([C-5](requirements.md#c-5)); no cambia el diseño.
- **Evidence:** UNVERIFIED — se mide con EV-2 y EV-3 cuando exista el dataset.

<a id="p6"></a>
### P6 — Qdrant en modo local bloquea su carpeta: un segundo cliente sobre el mismo `path` falla (High)

- **If false:** se podrían usar varios workers de uvicorn; D13 dejaría de exigir un solo proceso.
- **Evidence:** verified 2026-10-23, `_log/premises.md` P6; ver [Evidence](#evidence).

## Evidence

Corridas registradas en `_log/premises.md` (2026-10-23).

<details><summary>P6 — probe p6_qdrant_lock.py con uv, qdrant-client 1.20.0</summary>

```
python 3.13.16 qdrant-client 1.20.0
second client on same path: refused -> RuntimeError Storage folder <tmp del worktree>
```
El mensaje sigue con "is already accessed by another instance of Qdrant client" (recortado por el probe a una línea).
</details>

<details><summary>P1 — listado de archivos versionados en src/ y tests/</summary>

Salida vacía, exit 0: no hay archivos versionados en `src/` ni `tests/`.
</details>

<details><summary>P2 — probe p2_sqlite.py</summary>

pyenv 3.13.4 (`PYENV_VERSION=3.13.4 python3`), exit 0:
```
python 3.13.4 sqlite 3.54.0
fts5 credito -> 1
fts5 CRÉDITO -> 1
```
</details>

<details><summary>P4 — probe p4_sections.py</summary>

```
Manual del Asesor Comercial.md sections 3 max_bytes 164
Políticas de Atención.md sections 4 max_bytes 123
Portafolio de Microseguros.md sections 4 max_bytes 153
Procedimientos Operativos.md sections 3 max_bytes 179
Productos de Crédito.md sections 3 max_bytes 387
```
</details>
