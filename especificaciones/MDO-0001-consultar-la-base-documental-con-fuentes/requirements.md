---
schema_version: 1
spec: MDO-0001-consultar-la-base-documental-con-fuentes
depth: standard
projects: [asistente-asesores]
status: approved
---

# Requirements — Consultar la base documental con fuentes

`POST /api/consultar` responde solo con la base documental oficial, cita documento, sección y fragmento,
devuelve el mensaje fijo cuando no hay soporte, rechaza entradas inválidas con RFC 9457 y registra cada
consulta procesada. Se comprueba con pruebas unitarias y de API y con los umbrales de evaluación de abajo.

## Functional requirements

<a id="fr1"></a>
### FR-1 — Preparar la base documental
Serves: AC-1, AC-1/C1
Projects: asistente-asesores

Al arrancar, el servidor carga los documentos de `Data/`, excluye los confidenciales y deja consultables
los demás, fragmentados por sección `##` con su identidad `documento > sección`.

#### S-1.1 — Documentos oficiales consultables
- **Given** los seis archivos de `Data/`
- **When** el servidor prepara la base documental
- **Then** hay fragmentos de los cinco documentos oficiales, incluido `Políticas de Atención.md`, y cada fragmento conoce su documento y su sección
- **BUT it must NOT** existir ningún fragmento, término indexado ni vector que provenga de `Información restringida.md` (C1)

#### S-1.2 — Documento confidencial por contenido
- **Given** un documento cuyo encabezado declara `CONFIDENCIAL` aunque su nombre no esté en la lista de excluidos
- **When** se prepara la base
- **Then** el documento se excluye y el arranque lo registra en el log sin su contenido

<a id="fr2"></a>
### FR-2 — Descartar contenido duplicado
Serves: AC-2, AC-2/C1
Projects: asistente-asesores

Un contenido idéntico (tras normalizar espacios y mayúsculas) se indexa una sola vez, sea un documento
entero o una sección repetida.

#### S-2.1 — Documento duplicado
- **Given** dos archivos con el mismo contenido normalizado
- **When** se prepara la base
- **Then** solo se indexan los fragmentos del primero en orden alfabético de nombre de archivo
- **BUT it must NOT** citarse dos veces el mismo contenido en una respuesta (C1)

#### S-2.2 — Fuentes sin repetir
- **Given** dos fragmentos recuperados con el mismo `documento > sección`
- **When** se arma la lista de fuentes
- **Then** la fuente aparece una sola vez

<a id="fr3"></a>
### FR-3 — Recuperar fragmentos relevantes
Serves: AC-3, AC-11
Projects: asistente-asesores

La búsqueda combina coincidencia de palabras y similitud semántica, ordena los fragmentos y aplica un
umbral de relevancia: si ningún fragmento lo supera, no hay soporte documental.

#### S-3.1 — Pregunta con soporte
- **Given** la base documental completa
- **When** se busca "¿Cuál es el monto máximo del Crédito Productivo Impulso?"
- **Then** el primer fragmento es `Productos de Crédito > Crédito Productivo Impulso`

#### S-3.2 — Pregunta sin soporte
- **Given** una pregunta de los cuatro temas cuya respuesta no está en la base (p. ej. la tasa de interés de un crédito)
- **When** se busca
- **Then** ningún fragmento supera el umbral y el resultado es "sin soporte"

<a id="fr4"></a>
### FR-4 — Responder solo con información encontrada
Serves: AC-3, AC-3/C1, AC-4, AC-4/C1
Projects: asistente-asesores

Con soporte, la respuesta se construye solo con los fragmentos recuperados y su estado es `Exitosa`; la
salida del modelo se valida antes de entregarse.

#### S-4.1 — Respuesta del ejemplo del PDF
- **Given** la base documental completa
- **When** el asesor envía `{"pregunta": "¿Cuál es el monto máximo del Crédito Productivo Impulso?"}`
- **Then** responde 200, `estado` `Exitosa` y la `respuesta` contiene `$50.000.000`
- **AND IT MUST** traer al menos una fuente (C1)

#### S-4.2 — Salida del modelo con datos sin soporte
- **Given** que el modelo devuelve una respuesta con un número que no aparece en los fragmentos citados, o cita un fragmento que no se recuperó
- **When** se valida la salida
- **Then** se descarta y se entrega la respuesta extractiva de [FR-12](#fr12)
- **BUT it must NOT** entregarse ningún dato ausente de la base documental (C1)

<a id="fr5"></a>
### FR-5 — Responder el soporte parcial
Serves: AC-5, AC-5/C1, AC-5/C2
Projects: asistente-asesores

Si la base responde solo parte de la pregunta, la respuesta contesta esa parte y la cita; con el modelo,
además dice qué parte no está en la base documental; sin modelo, no afirma cubrir toda la pregunta
([C-1](#c-1)).

#### S-5.1 — Monto y tasa
- **Given** el modelo de redacción configurado
- **When** se pregunta "¿Cuál es el monto máximo y la tasa del Crédito Productivo Impulso?"
- **Then** la respuesta trae el monto máximo con su fuente y una frase del tipo "No encontré información sobre la tasa", con estado `Exitosa`
- **BUT it must NOT** dar, estimar ni sugerir una tasa (C1)

#### S-5.2 — Soporte parcial en modo extractivo
- **Given** que no hay modelo configurado
- **When** se hace la misma pregunta
- **Then** la respuesta empieza con "Esto es lo que encontré en la base documental:", trae el fragmento del Crédito Productivo Impulso con su fuente y estado `Exitosa`
- **BUT it must NOT** afirmar que responde toda la pregunta ni dar una tasa (C1)

<a id="fr6"></a>
### FR-6 — Citar documento, sección y fragmento
Serves: AC-6, AC-6/C1, AC-2/C1
Projects: asistente-asesores

Cada elemento de `fuentes` trae `documento`, `seccion` y `fragmento`, y corresponde a un fragmento usado
en la respuesta.

#### S-6.1 — Forma de la fuente
- **Given** una respuesta `Exitosa`
- **When** se lee `fuentes`
- **Then** cada fuente trae `documento` (p. ej. "Productos de Crédito"), `seccion` (p. ej. "Crédito Productivo Impulso") y `fragmento` (el texto de la sección usado)
- **AND IT MUST** corresponder cada fuente a un fragmento que el redactor declaró usado (C1)

<a id="fr7"></a>
### FR-7 — Validar la pregunta
Serves: AC-7, AC-7/C1, AC-9, AC-9/C1, AC-9/C2
Projects: asistente-asesores

`pregunta` es obligatoria, de tipo texto y, normalizada a NFC y sin los espacios al inicio y al final,
tiene entre 1 y 1.000 puntos de código Unicode ([C-2](#c-2)). Si no cumple, la API responde 422 antes de
buscar.

#### S-7.1 — Vacía, solo espacios o cuerpo inválido
- **Given** `{"pregunta": ""}`, `{"pregunta": "   "}`, `{}`, `{"pregunta": 5}` o un JSON mal formado
- **When** se envía
- **Then** responde 422 `application/problem+json` con `requestId` y un `detail` legible
- **BUT it must NOT** consultar la base ni registrar la consulta (C1)

#### S-7.2 — Límite de longitud
- **Given** una pregunta de 1.001 puntos de código tras normalizar a NFC y quitar los espacios exteriores
- **When** se envía
- **Then** responde 422 con un `detail` que menciona el límite de 1.000 caracteres
- **AND IT MUST** procesar normalmente una pregunta de exactamente 1.000 puntos de código, también si trae espacios exteriores adicionales o llega en forma NFD y queda en 1.000 al normalizar (C1)
- **BUT it must NOT** recortar, consultar ni registrar la pregunta rechazada (C2)

<a id="fr8"></a>
### FR-8 — Aceptar caracteres especiales
Serves: AC-8, AC-8/C1
Projects: asistente-asesores

La pregunta admite cualquier carácter Unicode; la búsqueda trata el texto como datos, nunca como sintaxis
de consulta.

#### S-8.1 — Tildes, signos y emojis
- **Given** "¿Cuál es el monto máximo del \"Crédito\" Productivo Impulso? (urgente) 😊 * - :"
- **When** se envía
- **Then** responde 200 con el mismo resultado que la pregunta sin esos signos
- **BUT it must NOT** producir un error de sintaxis de búsqueda (C1)

#### S-8.2 — Sin tildes
- **Given** "cual es el monto maximo del credito productivo impulso"
- **When** se envía
- **Then** recupera el mismo fragmento que la pregunta con tildes

<a id="fr9"></a>
### FR-9 — Rechazar cuerpos y tipos no admitidos
Serves: AC-10
Projects: asistente-asesores

Un cuerpo de más de 16 KB responde 413 y un `Content-Type` distinto de `application/json` responde 415,
ambos en RFC 9457 con `requestId` y sin procesar la consulta.

#### S-9.1 — Cuerpo grande
- **Given** un cuerpo de 16.385 bytes, declarado en `Content-Length` o enviado sin él
- **When** se envía
- **Then** responde 413 `application/problem+json`

#### S-9.2 — Tipo de contenido
- **Given** un cuerpo válido con `Content-Type: text/plain`, o sin `Content-Type`
- **When** se envía
- **Then** responde 415 `application/problem+json`

<a id="fr10"></a>
### FR-10 — Responder sin información suficiente
Serves: AC-11, AC-12, AC-12/C1, AC-13, AC-13/C1
Projects: asistente-asesores

Sin soporte documental, o con la base vacía, la respuesta es exactamente "No tengo información suficiente
para responder.", `fuentes` vacío, estado `Sin información suficiente` y código 200. No se llama al modelo.

#### S-10.1 — Sin soporte
- **Given** una pregunta sin soporte en la base
- **When** se consulta
- **Then** responde 200 con el mensaje fijo exacto, `fuentes: []` y `estado` `Sin información suficiente`

#### S-10.2 — Base vacía
- **Given** una base documental sin documentos consultables (carpeta vacía o solo confidenciales)
- **When** el servidor arranca y se consulta
- **Then** arranca sin error y responde 200 con el mensaje fijo
- **BUT it must NOT** responder 5xx (C1)

#### S-10.3 — Fuera de tema
- **Given** "¿Va a llover mañana en Bogotá?"
- **When** se consulta
- **Then** responde con el mensaje fijo y estado `Sin información suficiente`
- **BUT it must NOT** devolver estado `Bloqueada por seguridad` (C1)

<a id="fr11"></a>
### FR-11 — Registrar cada consulta procesada
Serves: AC-14, AC-14/C1
Projects: asistente-asesores

Toda consulta que pasa la validación se guarda con pregunta, fecha y hora (UTC, ISO 8601), respuesta,
fuentes y estado antes de responder.

#### S-11.1 — Registro por estado
- **Given** una consulta `Exitosa` y otra `Sin información suficiente`
- **When** terminan
- **Then** cada una tiene un registro con los cinco campos, y las fuentes registradas coinciden con las devueltas
- **BUT it must NOT** existir registro de las peticiones rechazadas con 413, 415 o 422 (C1)

#### S-11.2 — Falla al guardar
- **Given** que el almacenamiento falla al guardar
- **When** se consulta
- **Then** responde 500 (ver [FR-13](#fr13)) y no queda un registro incompleto

<a id="fr12"></a>
### FR-12 — Respaldo extractivo
Serves: AC-16
Projects: asistente-asesores

Sin modelo configurado (el proveedor está apagado por defecto o falta su clave, [C-10](#c-10)), o si el
modelo falla, excede el tiempo, no consigue cupo a tiempo ([C-11](#c-11)) o su salida no pasa la validación,
la respuesta es extractiva: los fragmentos relevantes con sus fuentes, estado `Exitosa` y código 200.

#### S-12.1 — Modelo caído
- **Given** el modelo configurado pero respondiendo con error o sin responder antes del tiempo límite
- **When** se consulta una pregunta con soporte
- **Then** responde 200, `estado` `Exitosa`, con los fragmentos y sus fuentes

#### S-12.2 — Sin clave
- **Given** que `GEMINI_API_KEY` no está definida
- **When** se consulta
- **Then** no se intenta llamar al modelo y la respuesta es extractiva

#### S-12.3 — Proveedor apagado por defecto
- **Given** que `LLM_PROVIDER` no está definida o vale `ninguno`, aunque `GEMINI_API_KEY` esté definida
- **When** se consulta una pregunta con soporte
- **Then** no se intenta llamar al modelo y la respuesta es extractiva

<a id="fr13"></a>
### FR-13 — Controlar errores inesperados
Serves: AC-15, AC-15/C1
Projects: asistente-asesores

Una falla inesperada responde 500 en RFC 9457 con `requestId` y un mensaje genérico; el detalle queda solo
en el log.

#### S-13.1 — Falla en la búsqueda
- **Given** que la búsqueda lanza una excepción
- **When** se consulta
- **Then** responde 500 `application/problem+json` con `requestId` y `detail` genérico
- **BUT it must NOT** incluir trazas, rutas, nombres de archivos internos, SQL ni el texto de la pregunta (C1)

<a id="fr14"></a>
### FR-14 — Contrato de respuesta
Serves: AC-3
Projects: asistente-asesores

`POST /api/consultar` acepta `{"pregunta": string}` y responde 200 con
`{"respuesta": string, "fuentes": Fuente[], "estado": "Exitosa" | "Sin información suficiente" | "Bloqueada por seguridad"}`.

#### S-14.1 — Forma de la respuesta
- **Given** cualquier consulta válida
- **When** responde
- **Then** el cuerpo tiene exactamente `respuesta`, `fuentes` y `estado`, y la cabecera `X-Request-Id`

## Eval thresholds

Dataset `tests/fixtures/consultas.json@v2` (66 preguntas; v1 tenía 32): preguntas con respuesta, sin
respuesta, fuera de tema, parciales y de dato faltante sobre `Data/`, con el fragmento y el estado
esperados. "Dato faltante" pregunta un dato que no está de un producto o proceso que sí existe: es
soporte parcial (AC-5), no "sin soporte" ([C-9](#c-9)).

| ID | Serves | Metric | Threshold | Tolerance vs baseline | Dataset (version) |
|---|---|---|---|---|---|
| EV-1 | AC-3 | Recuperación: el fragmento esperado está entre las fuentes (hit@3) | ≥ 0,90 | −0,05 | consultas@v2 |
| EV-2 | AC-11, AC-13 | Precisión de "sin información": preguntas sin soporte con estado `Sin información suficiente` | ≥ 0,90 | −0,05 | consultas@v2 |
| EV-3 | AC-3 | Falsos "sin información": preguntas con soporte que no responden | ≤ 0,10 | +0,05 | consultas@v2 |
| EV-4 | AC-4 | Fidelidad: cifras de la respuesta presentes en los fragmentos citados | 1,00 | 0 | consultas@v2 |
| EV-5 | AC-6 | Respuestas `Exitosa` con al menos una fuente completa (documento, sección, fragmento) | 1,00 | 0 | consultas@v2 |
| EV-6 | AC-5 | Parciales y de dato faltante que nombran la parte o el dato que falta (con modelo) | ≥ 0,80 | −0,10 | consultas@v2 |
| EV-7 | AC-5/C2 | Dato faltante en modo extractivo: `Exitosa`, con la sección esperada entre las fuentes, la frase inicial de D12 y sin cifras fuera de los fragmentos citados (no afirma el dato) | ≥ 0,90 | −0,05 | consultas@v2 |

## Non-functional requirements

### NFR-1 — Latencia de la consulta
Serves: AC-3, AC-16

p95 ≤ 300 ms en modo extractivo y ≤ 3 s con el modelo, medidos con la prueba de carga local de
`performance.md` (N ≥ 5 corridas, mediana).

### NFR-2 — Arranque
Serves: AC-1

Preparar la base con los embeddings ya calculados toma ≤ 2 s, medido en el log de arranque.

### NFR-3 — Tiempo límite del modelo
Serves: AC-16

Una llamada al modelo se corta a los 5 s, sin reintentos, y pasa al respaldo extractivo; medido con un
doble que no responde.

### NFR-4 — Log por consulta
Serves: AC-14, AC-15, AC-15/C1

Cada petición emite una línea JSON con `requestId`, `estado` (o código HTTP), `latenciaMs` y número de
fuentes; 0 apariciones del texto de la pregunta, de secretos o de contenido confidencial, verificado por
una prueba que inspecciona los logs capturados.

### NFR-5 — Ejecución local
Serves: AC-1, AC-16

Tras la primera descarga del modelo de embeddings, el servidor arranca y responde sin red; las pruebas
no hacen llamadas de red (verificado ejecutándolas sin red).

## AC → FR matrix

| AC | Clause | FR / scenario | Status |
|---|---|---|---|
| AC-1 | main | FR-1 / S-1.1, S-1.2 | covered |
| AC-1 | C1: nada de la información restringida | FR-1 / S-1.1 C1 | covered |
| AC-2 | main | FR-2 / S-2.1 | covered |
| AC-2 | C1: sin fuente repetida | FR-2 / S-2.1 C1, S-2.2; FR-6 | covered |
| AC-3 | main | FR-3 / S-3.1; FR-4 / S-4.1; FR-14 / S-14.1 | covered |
| AC-3 | C1: al menos una fuente | FR-4 / S-4.1 C1 | covered |
| AC-4 | main | FR-4 / S-4.2 | covered |
| AC-4 | C1: sin inferir ni completar | FR-4 / S-4.2 C1 | covered |
| AC-5 | main | FR-5 / S-5.1 | covered |
| AC-5 | C1: sin completar la parte faltante | FR-5 / S-5.1 C1 | covered |
| AC-5 | C2: extractivo sin afirmar cobertura total | FR-5 / S-5.2, S-5.2 C1 | covered |
| AC-6 | main | FR-6 / S-6.1 | covered |
| AC-6 | C1: cada fuente usada | FR-6 / S-6.1 C1 | covered |
| AC-7 | main | FR-7 / S-7.1 | covered |
| AC-7 | C1: sin consultar ni registrar | FR-7 / S-7.1 C1 | covered |
| AC-8 | main | FR-8 / S-8.1, S-8.2 | covered |
| AC-8 | C1: la búsqueda no falla | FR-8 / S-8.1 C1 | covered |
| AC-9 | main | FR-7 / S-7.2 | covered |
| AC-9 | C1: 1.000 se acepta | FR-7 / S-7.2 C1 | covered |
| AC-9 | C2: sin recortar, consultar ni registrar | FR-7 / S-7.2 C2 | covered |
| AC-10 | main | FR-9 / S-9.1, S-9.2 | covered |
| AC-11 | main | FR-3 / S-3.2; FR-10 / S-10.1 | covered |
| AC-12 | main | FR-10 / S-10.2 | covered |
| AC-12 | C1: sin fallar | FR-10 / S-10.2 C1 | covered |
| AC-13 | main | FR-10 / S-10.3 | covered |
| AC-13 | C1: no bloqueada | FR-10 / S-10.3 C1 | covered |
| AC-14 | main | FR-11 / S-11.1, S-11.2 | covered |
| AC-14 | C1: sin registrar rechazos | FR-11 / S-11.1 C1 | covered |
| AC-15 | main | FR-13 / S-13.1 | covered |
| AC-15 | C1: sin detalles internos | FR-13 / S-13.1 C1 | covered |
| AC-16 | main | FR-12 / S-12.1, S-12.2, S-12.3 | covered |

## Clarifications

<a id="c-1"></a>
### C-1 — ¿Qué exige AC-5 en modo extractivo? (2026-10-23)
- **Answer:** con Gemini se indica la parte faltante; en modo extractivo la respuesta empieza con "Esto es lo que encontré en la base documental:" y no afirma cubrir toda la pregunta.
- **Answered by:** PE (Product Engineer).
- **Effect:** AC-5 gana la cláusula C2; FR-5 / S-5.2; design.md D12. EV-6 mide solo con modelo.

<a id="c-2"></a>
### C-2 — ¿Qué es un duplicado y cómo se cuentan los 1.000 caracteres? (2026-10-23)
- **Answer:** duplicado = contenido idéntico tras normalizar espacios y mayúsculas; el límite son 1.000 puntos de código Unicode tras normalizar a NFC y quitar los espacios exteriores.
- **Answered by:** PE (Product Engineer).
- **Effect:** FR-2 sin cambios; FR-7 / S-7.2 normalizan a NFC; design.md D6, D8.

<a id="c-3"></a>
### C-3 — ¿Qué almacén de vectores se usa en lugar de `sqlite-vec`? (2026-10-23)
- **Answer:** Qdrant en modo local (`qdrant-client` 1.20.0, `QdrantClient(path=…)`, sin servidor); SQLite queda para el registro de consultas y FTS5. Aplicado en `architecture.md` y `model-registry.md` (`/mandao-constitution`, commit 9da22a0), con verificación local en Python 3.13.16 y 3.13.4.
- **Answered by:** PE (Product Engineer), como tech lead.
- **Effect:** design.md D1, D4, D11, D13 (nueva: un solo proceso, P6), tabla ACID, Model and prompts, Constitution Impact; data-model.md con la colección Qdrant y sin tabla de caché; research.md R5; P2 solo exige FTS5.

<a id="c-6"></a>
### C-6 — ¿Cuántos procesos admite Qdrant local? (2026-10-23)
- **Answer:** uno. Un segundo cliente sobre la misma carpeta lanza `RuntimeError` (P6, verificado); la app abre un cliente en el `lifespan` y uvicorn corre con un worker.
- **Answered by:** resuelto técnicamente (base: `architecture.md` "ejecutable 100 % local sin servicios"; alternativas rechazadas: varios workers, servidor Qdrant).
- **Effect:** design.md D13; README indica un solo worker.

<a id="c-7"></a>
### C-7 — ¿Se aceptan R3 y R5 sin un MCP de búsqueda web declarado? (2026-10-23)
- **Answer:** sí, como excepción. R3 (FTS5) y R5 (Qdrant) se aceptan sin MCP de búsqueda: las premisas P2 y P6 se verificaron ejecutándolas en este entorno (Python 3.13 con `uv`), con comando y salida registrados en `_log/premises.md`; esa evidencia es más fuerte que una búsqueda web.
- **Answered by:** PE (Product Engineer).
- **Effect:** el research gate de `mandao run next` sigue marcando R3 y R5 (no hay `research.web_search_servers`); se aprueba igual, con esta excepción como respaldo.

<a id="c-8"></a>
### C-8 — ¿Qué gates y qué verificador de tipos usa el backend? (2026-10-23)
- **Answer:** `format: uv run ruff format --check .`, `lint: uv run ruff check .`, `typecheck: uv run mypy src`, `test: uv run pytest`, declarados en `projects[].gates` de `.mandao/config.yml` con aprobación del PE; mypy en modo estricto.
- **Answered by:** PE (Product Engineer).
- **Effect:** tasks.md T1; resuelve el `OPEN` "mypy o pyright" de `standards.md` (design.md, Constitution Impact).

<a id="c-4"></a>
### C-4 — ¿Cómo se fija Python y se registra la hora? (2026-10-23)
- **Answer:** Python 3.13 fijado con `.python-version`; el README instala con `uv`. Fecha y hora en UTC, mostradas en hora local (MDO-0003).
- **Answered by:** PE (Product Engineer).
- **Effect:** design.md D1; FR-11 (UTC, ISO 8601).

<a id="c-5"></a>
### C-5 — ¿Los umbrales 0,60 / 0,40 son definitivos? (2026-10-23)
- **Answer:** son iniciales y se ajustan con el dataset en las tareas.
- **Answered by:** PE (Product Engineer).
- **Effect:** design.md D4 y P5; una tarea calibra contra EV-2 y EV-3.

<a id="c-10"></a>
### C-10 — ¿El modelo de redacción es obligatorio y está atado a Gemini? (2026-10-23)
- **Answer:** no. El LLM es opcional y está apagado por defecto: el PDF no lo exige y el modo extractivo cumple el contrato. `LLM_PROVIDER` elige el proveedor (`ninguno` por defecto, `gemini`); el caso de uso recibe el `Redactor` elegido al arrancar y, con `ninguno` o sin la clave del proveedor, usa el extractivo. `AGENTS.md` explica cómo agregar otro proveedor (un adaptador que implemente `Redactor` y su registro), sin implementar otros. `model-registry.md` justifica Gemini como el proveedor incluido: costo (nivel gratuito, Flash-Lite), política de datos (gratuito solo con datos irreales, pago en producción) y tamaño justo; el proveedor es intercambiable por configuración.
- **Answered by:** PE (Product Engineer).
- **Effect:** FR-12 y S-12.3; design.md D14 (nueva), D9, Model and prompts, Constitution Impact; tasks.md T16.

<a id="c-11"></a>
### C-11 — ¿Cuánto espera una consulta por un cupo del semáforo del modelo? (2026-10-23)
- **Answer:** como máximo 1 s (`ESPERA_CUPO_S` en `config.py`); si no consigue cupo, responde en modo extractivo con 200 y el log dice "sin cupo", sin contenido. Así una consulta en cola no suma una espera ilimitada al presupuesto de 3 s de p95 (NFR-1): 1 s de espera más una llamada típica de 0,9 a 1,7 s (medición de T15) queda por debajo.
- **Answered by:** resuelto técnicamente (base: NFR-1, D9 "el extractivo es la respuesta de respaldo", AC-16; pedido de acotar la espera del PE, 2026-10-23). Rechazadas: espera sin límite (rompe NFR-1 con más de 5 consultas simultáneas), rechazar con 429 o 503 (AC-16 exige 200 extractivo), hacer la espera configurable (sin un caso que lo pida).
- **Effect:** FR-12; design.md D9; tasks.md T16.

<a id="c-9"></a>
### C-9 — ¿Qué es una pregunta por un dato que no está, de un producto que sí existe? (2026-10-23, verify)
- **Answer:** es soporte parcial (AC-5), no "sin soporte": el producto existe y falta el dato. Va en una categoría propia, `dato_faltante`. En modo extractivo, la respuesta muestra el fragmento correcto con la frase inicial de AC-5/C2 y no afirma el dato (EV-7); con Gemini, nombra el dato que falta (EV-6). El resto se recalibra con margen. Limitación documentada en el README: el modo extractivo no detecta qué atributo falta.
- **Answered by:** PE (Product Engineer).
- **Effect:** dataset `consultas@v2`; tabla de evals (EV-6 amplía su base, EV-7 nueva); design.md D4 (`UMBRAL_BAJO` 0,525). Motivo: con v2 ningún par de umbrales cumplía a la vez EV-2 y EV-3 si esas preguntas contaban como "sin soporte" (recuperan la sección correcta con FTS y coseno de 0,577 a 0,604).

## Consistency Check

| ID | Type | Finding | Severity | Owner | Status |
|---|---|---|---|---|---|
| CC-1 | PREMISE | P2 decía "Python 3.13.4 de pyenv permite cargar extensiones": falso (`AttributeError`). | normal | dev | resolved 2026-10-23: `sqlite-vec` reemplazado por Qdrant local (C-3); P2 solo exige FTS5, verificado con pyenv 3.13.4 |

<a id="open-items"></a>
## Open items

Ninguno.
